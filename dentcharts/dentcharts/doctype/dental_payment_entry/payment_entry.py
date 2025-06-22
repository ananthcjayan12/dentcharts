import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

class DentalPaymentEntry(Document):
	def validate(self):
		"""Validate payment entry data"""
		self.validate_payment_details()
		self.set_default_values()
	
	def validate_payment_details(self):
		"""Validate payment details"""
		if not self.payment_amount or self.payment_amount <= 0:
			frappe.throw("Payment amount must be greater than 0")
		
		# Validate against invoice outstanding amount
		if self.invoice:
			invoice = frappe.get_doc("Invoice", self.invoice)
			
			# Check if payment amount exceeds outstanding amount
			if self.payment_amount > invoice.outstanding_amount:
				frappe.msgprint(
					f"Payment amount ${self.payment_amount} exceeds outstanding amount ${invoice.outstanding_amount}. "
					f"This will result in overpayment.",
					alert=True
				)
		
		# Validate reference number for certain payment methods
		if self.payment_method in ["Check", "Bank Transfer", "Online Payment"] and not self.reference_number:
			frappe.throw(f"Reference number is required for {self.payment_method} payments")
	
	def set_default_values(self):
		"""Set default values for new payment entries"""
		if not self.created_by:
			self.created_by = frappe.session.user
		
		if not self.received_by:
			self.received_by = frappe.session.user
		
		if not self.payment_date:
			self.payment_date = today()
		
		if not self.posting_date:
			self.posting_date = self.payment_date or today()
		
		if not self.company:
			self.company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company") or "Company"
	
	def before_insert(self):
		"""Actions before inserting payment entry"""
		# Auto-populate patient from invoice
		if self.invoice and not self.patient:
			invoice = frappe.get_doc("Invoice", self.invoice)
			self.patient = invoice.patient
	
	def on_submit(self):
		"""Actions after submitting payment entry"""
		# Update invoice paid amount
		if self.invoice:
			self.update_invoice_payment()
	
	def on_cancel(self):
		"""Actions when payment entry is cancelled"""
		# Reverse invoice payment update
		if self.invoice:
			self.reverse_invoice_payment()
	
	def update_invoice_payment(self):
		"""Update invoice with payment information"""
		if not self.invoice:
			return
		
		try:
			invoice = frappe.get_doc("Invoice", self.invoice)
			
			# Add payment amount to invoice
			invoice.paid_amount = flt(invoice.paid_amount or 0) + flt(self.payment_amount)
			
			# Recalculate outstanding amount
			invoice.outstanding_amount = flt(invoice.total_amount) - flt(invoice.paid_amount)
			
			# Update payment status
			if invoice.paid_amount >= invoice.total_amount:
				invoice.payment_status = "Paid"
				if invoice.paid_amount > invoice.total_amount:
					invoice.payment_status = "Overpaid"
			elif invoice.paid_amount > 0:
				invoice.payment_status = "Partially Paid"
			else:
				invoice.payment_status = "Unpaid"
			
			# Update invoice status if fully paid
			if invoice.payment_status == "Paid" and invoice.invoice_status != "Paid":
				invoice.invoice_status = "Paid"
			
			invoice.save()
			
			# Add comment to invoice
			invoice.add_comment("Comment", 
				f"Payment of ${self.payment_amount} received via {self.payment_method} (Payment Entry: {self.name})")
		
		except Exception as e:
			frappe.log_error(f"Failed to update invoice payment: {str(e)}")
			frappe.throw(f"Failed to update invoice: {str(e)}")
	
	def reverse_invoice_payment(self):
		"""Reverse payment update on invoice when payment is cancelled"""
		if not self.invoice:
			return
		
		try:
			invoice = frappe.get_doc("Invoice", self.invoice)
			
			# Subtract payment amount from invoice
			invoice.paid_amount = flt(invoice.paid_amount or 0) - flt(self.payment_amount)
			if invoice.paid_amount < 0:
				invoice.paid_amount = 0
			
			# Recalculate outstanding amount
			invoice.outstanding_amount = flt(invoice.total_amount) - flt(invoice.paid_amount)
			
			# Update payment status
			if invoice.paid_amount >= invoice.total_amount:
				invoice.payment_status = "Paid"
			elif invoice.paid_amount > 0:
				invoice.payment_status = "Partially Paid"
			else:
				invoice.payment_status = "Unpaid"
			
			# Update invoice status
			if invoice.payment_status != "Paid" and invoice.invoice_status == "Paid":
				invoice.invoice_status = "Partially Paid" if invoice.paid_amount > 0 else "Sent"
			
			invoice.save()
			
			# Add comment to invoice
			invoice.add_comment("Comment", 
				f"Payment of ${self.payment_amount} cancelled (Payment Entry: {self.name})")
		
		except Exception as e:
			frappe.log_error(f"Failed to reverse invoice payment: {str(e)}")
	
	def process_refund(self, refund_amount=None, refund_reason=None):
		"""Process a refund for this payment"""
		if not refund_amount:
			refund_amount = self.payment_amount
		
		if refund_amount > self.payment_amount:
			frappe.throw("Refund amount cannot exceed original payment amount")
		
		# Create refund payment entry
		refund_entry = frappe.get_doc({
			"doctype": "Dental Payment Entry",
			"invoice": self.invoice,
			"payment_amount": -refund_amount,  # Negative amount for refund
			"payment_method": self.payment_method,
			"payment_status": "Refunded",
			"reference_number": f"REFUND-{self.name}",
			"notes": f"Refund for payment {self.name}. Reason: {refund_reason or 'Not specified'}"
		})
		refund_entry.insert()
		refund_entry.submit()
		
		# Update original payment status
		self.payment_status = "Refunded"
		self.save()
		
		return refund_entry.name
	
	@staticmethod
	def get_payments_for_invoice(invoice_name):
		"""Get all payments for a specific invoice"""
		return frappe.get_all("Dental Payment Entry",
			filters={"invoice": invoice_name, "docstatus": 1},
			fields=["name", "payment_date", "payment_amount", "payment_method", "payment_status", "reference_number"],
			order_by="payment_date desc"
		)
	
	@staticmethod
	def get_payments_for_patient(patient):
		"""Get all payments for a specific patient"""
		return frappe.get_all("Dental Payment Entry",
			filters={"patient": patient, "docstatus": 1},
			fields=["name", "invoice", "payment_date", "payment_amount", "payment_method", "payment_status"],
			order_by="payment_date desc"
		)
	
	@staticmethod
	def get_daily_collections(date=None):
		"""Get daily payment collections"""
		if not date:
			date = today()
		
		collections = frappe.db.sql("""
			SELECT 
				payment_method,
				COUNT(*) as transaction_count,
				SUM(payment_amount) as total_amount
			FROM `tabDental Payment Entry`
			WHERE payment_date = %s AND docstatus = 1
			GROUP BY payment_method
			ORDER BY total_amount DESC
		""", date, as_dict=True)
		
		return collections
	
	@staticmethod
	def get_outstanding_payments():
		"""Get payments that are still processing or pending clearance"""
		return frappe.get_all("Dental Payment Entry",
			filters={
				"payment_status": ["in", ["Processing", "Received"]],
				"docstatus": 1
			},
			fields=["name", "invoice", "patient_name", "payment_amount", "payment_method", "payment_date"],
			order_by="payment_date asc"
		) 