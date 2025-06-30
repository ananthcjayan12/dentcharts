import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, today, add_days, getdate, nowdate
from datetime import datetime, timedelta

class Invoice(Document):
	def validate(self):
		"""Validate invoice data"""
		self.validate_dates()
		self.validate_invoice_items()
		self.calculate_totals()
		self.update_payment_status()
		self.set_default_values()
	
	def validate_dates(self):
		"""Validate date fields"""
		if not self.due_date:
			# Auto-set due date based on payment terms
			if self.payment_terms == "Immediate":
				self.due_date = self.invoice_date
			elif self.payment_terms == "Net 15":
				self.due_date = add_days(self.invoice_date, 15)
			elif self.payment_terms == "Net 30":
				self.due_date = add_days(self.invoice_date, 30)
			elif self.payment_terms == "Net 60":
				self.due_date = add_days(self.invoice_date, 60)
			else:
				self.due_date = add_days(self.invoice_date, 30)  # Default
		
		if getdate(self.due_date) < getdate(self.invoice_date):
			frappe.throw("Due date cannot be before invoice date")
	
	def validate_invoice_items(self):
		"""Validate invoice items"""
		if not self.invoice_items:
			frappe.throw("Invoice must have at least one item")
		
		# Validate item details
		for item in self.invoice_items:
			if not item.procedure_code:
				frappe.throw(f"Procedure code is required for row {item.idx}")
			
			if not item.amount or item.amount <= 0:
				frappe.throw(f"Amount must be greater than 0 for row {item.idx}")
			
			# Auto-populate item details if missing
			if item.procedure_code and not item.description:
				try:
					procedure = frappe.get_doc("Dental Procedure Master", item.procedure_code)
					item.description = procedure.procedure_name
					if not item.amount:
						item.amount = procedure.standard_fee
				except frappe.DoesNotExistError:
					pass
	
	def calculate_totals(self):
		"""Calculate total amounts"""
		subtotal = 0
		
		for item in self.invoice_items:
			# Always calculate total_amount for each item to ensure consistency
			item.total_amount = flt(item.quantity or 1) * flt(item.amount or 0)
			subtotal += flt(item.total_amount)
		
		self.subtotal = subtotal
		
		# Calculate tax (if applicable)
		# You can customize tax calculation based on your requirements
		self.tax_amount = 0  # No tax for now, can be enhanced
		
		self.total_amount = flt(self.subtotal + self.tax_amount)
		
		# Calculate insurance amounts
		if self.insurance_coverage_percentage and self.total_amount:
			self.insurance_amount = flt(self.total_amount * self.insurance_coverage_percentage / 100)
		else:
			self.insurance_amount = 0
		
		self.patient_portion = flt(self.total_amount - self.insurance_amount)
		
		# Calculate outstanding amount
		self.outstanding_amount = flt(self.total_amount - (self.paid_amount or 0))
	
	def update_payment_status(self):
		"""Update payment status based on paid amount"""
		if not self.total_amount:
			return
		
		paid_amount = self.paid_amount or 0
		
		if paid_amount == 0:
			self.payment_status = "Unpaid"
		elif paid_amount >= self.total_amount:
			self.payment_status = "Paid"
			if paid_amount > self.total_amount:
				self.payment_status = "Overpaid"
		else:
			self.payment_status = "Partially Paid"
		
		# Check for overdue
		if (self.payment_status in ["Unpaid", "Partially Paid"] and 
			getdate(today()) > getdate(self.due_date)):
			self.invoice_status = "Overdue"
			# Calculate late fee if applicable
			if self.late_fee_applicable:
				self.calculate_late_fee()
	
	def calculate_late_fee(self):
		"""Calculate late fee for overdue invoices"""
		if not self.late_fee_applicable:
			return
		
		days_overdue = (getdate(today()) - getdate(self.due_date)).days
		
		if days_overdue > 0:
			# Calculate late fee as 1.5% per month (0.05% per day)
			late_fee_rate = 0.0005  # 0.05% per day
			self.late_fee_amount = flt(self.outstanding_amount * late_fee_rate * days_overdue)
	
	def set_default_values(self):
		"""Set default values for new invoices"""
		if not self.created_by:
			self.created_by = frappe.session.user
		
		if not self.invoice_date:
			self.invoice_date = today()
		
		# Auto-populate patient details
		if self.patient and not self.billing_address:
			try:
				patient = frappe.get_doc("Patient", self.patient)
				# You can customize this based on your Patient DocType structure
				self.billing_address = getattr(patient, 'address', '')
			except:
				pass
	
	def before_submit(self):
		"""Actions before submitting invoice"""
		if self.invoice_status == "Draft":
			self.invoice_status = "Sent"
			self.sent_date = today()
		
		# Validate all required fields
		if not self.approved_by:
			frappe.throw("Invoice must be approved before submission")
	
	def on_submit(self):
		"""Actions after submitting invoice"""
		# Update treatment plan if linked
		if self.treatment_plan:
			self.update_treatment_plan_billing()
		
		# Create insurance claim if applicable
		if self.insurance_amount > 0:
			self.create_insurance_claim()
	
	def update_treatment_plan_billing(self):
		"""Update treatment plan with billing information"""
		if not self.treatment_plan:
			return
		
		try:
			treatment_plan = frappe.get_doc("Treatment Plan", self.treatment_plan)
			# You can add billing status to treatment plan
			treatment_plan.add_comment("Comment", f"Invoice {self.name} created for ${self.total_amount}")
			treatment_plan.save()
		except Exception as e:
			frappe.log_error(f"Failed to update treatment plan: {str(e)}")
	
	def create_insurance_claim(self):
		"""Create insurance claim for this invoice"""
		if not self.insurance_amount or self.insurance_amount <= 0:
			return
		
		try:
			claim = frappe.get_doc({
				"doctype": "Insurance Claim",
				"invoice": self.name,
				"patient": self.patient,
				"practitioner": self.practitioner,
				"insurance_provider": self.insurance_provider,
				"claim_amount": self.insurance_amount,
				"claim_date": today(),
				"claim_status": "Submitted"
			})
			claim.insert()
			
			frappe.msgprint(f"Insurance claim {claim.name} created for ${self.insurance_amount}")
		except Exception as e:
			frappe.log_error(f"Failed to create insurance claim: {str(e)}")
	
	def record_payment(self, payment_amount, payment_method="Cash", payment_date=None, reference_number=None):
		"""Record a payment against this invoice"""
		if not payment_date:
			payment_date = today()
		
		if payment_amount <= 0:
			frappe.throw("Payment amount must be greater than 0")
		
		# Create payment entry
		payment_entry = frappe.get_doc({
			"doctype": "Payment Entry",
			"invoice": self.name,
			"patient": self.patient,
			"payment_amount": payment_amount,
			"payment_method": payment_method,
			"payment_date": payment_date,
			"reference_number": reference_number
		})
		payment_entry.insert()
		
		# Update invoice amounts manually
		self.paid_amount = flt(self.paid_amount or 0) + flt(payment_amount)
		self.outstanding_amount = flt(self.total_amount) - flt(self.paid_amount)
		
		# Update payment status
		self.update_payment_status()
		
		self.save()
		
		return payment_entry.name
	
	def send_invoice(self):
		"""Send invoice to patient"""
		if self.invoice_status == "Draft":
			self.invoice_status = "Sent"
			self.sent_date = today()
			self.save()
			
			# Here you can add email sending logic
			frappe.msgprint(f"Invoice {self.name} marked as sent")
	
	def cancel_invoice(self, reason=None):
		"""Cancel the invoice"""
		self.invoice_status = "Cancelled"
		if reason:
			self.add_comment("Comment", f"Invoice cancelled: {reason}")
		self.save()
	
	@staticmethod
	def create_from_treatment_plan(treatment_plan_name):
		"""Create invoice from completed treatment plan items"""
		treatment_plan = frappe.get_doc("Treatment Plan", treatment_plan_name)
		
		# Get completed items that haven't been billed
		completed_items = []
		for item in treatment_plan.plan_items:
			if item.item_status == "Completed":
				# Check if already billed (you might want to add a billed flag to treatment plan items)
				completed_items.append(item)
		
		if not completed_items:
			frappe.throw("No completed items found to bill")
		
		# Create invoice
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": treatment_plan.patient,
			"practitioner": treatment_plan.dentist,
			"treatment_plan": treatment_plan_name,
			"insurance_coverage_percentage": treatment_plan.insurance_coverage_percentage,
			"invoice_items": []
		})
		
		# Add items
		for item in completed_items:
			invoice.append("invoice_items", {
				"procedure_code": item.procedure_code,
				"description": f"{item.procedure_code} - Tooth {item.tooth_number or 'N/A'}",
				"tooth_number": item.tooth_number,
				"surface": item.surface,
				"amount": item.actual_cost or item.estimated_cost,
				"treatment_plan_item": item.name
			})
		
		invoice.insert()
		return invoice.name
	
	@staticmethod
	def create_from_appointment(appointment_name):
		"""Create invoice from completed appointment"""
		appointment = frappe.get_doc("Dental Appointment", appointment_name)
		
		if appointment.appointment_status != "Completed":
			frappe.throw("Can only create invoice from completed appointments")
		
		# Create invoice
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": appointment.patient,
			"practitioner": appointment.practitioner,
			"appointment_reference": appointment_name,
			"invoice_items": []
		})
		
		# Add procedures from appointment
		for procedure in appointment.planned_procedures:
			invoice.append("invoice_items", {
				"procedure_code": procedure.procedure_code,
				"description": f"{procedure.procedure_code} - Tooth {procedure.tooth_number or 'N/A'}",
				"tooth_number": procedure.tooth_number,
				"surface": procedure.surface,
				"amount": procedure.actual_cost or procedure.estimated_cost
			})
		
		invoice.insert()
		return invoice.name
	
	@staticmethod
	def get_outstanding_invoices_for_patient(patient):
		"""Get all outstanding invoices for a patient"""
		return frappe.get_all("Invoice", 
			filters={
				"patient": patient,
				"payment_status": ["in", ["Unpaid", "Partially Paid"]],
				"invoice_status": ["!=", "Cancelled"]
			},
			fields=["name", "invoice_date", "due_date", "total_amount", "outstanding_amount", "invoice_status"]
		)
	
	@staticmethod
	def get_overdue_invoices():
		"""Get all overdue invoices"""
		return frappe.get_all("Invoice",
			filters={
				"due_date": ["<", today()],
				"payment_status": ["in", ["Unpaid", "Partially Paid"]],
				"invoice_status": ["!=", "Cancelled"]
			},
			fields=["name", "patient", "patient_name", "due_date", "outstanding_amount"]
		)
	
	@frappe.whitelist()
	def get_payment_history(self):
		"""Get payment history for this invoice"""
		return frappe.get_all("Payment Entry",
			filters={"invoice": self.name},
			fields=["name", "payment_date", "payment_amount", "payment_method", "reference_number"],
			order_by="payment_date desc"
		) 