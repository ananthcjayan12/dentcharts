import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, today, add_days, getdate

class TreatmentPlan(Document):
	def validate(self):
		"""Validate treatment plan data"""
		self.validate_dates()
		self.validate_plan_items()
		self.calculate_totals()
		self.update_progress()
		self.set_default_values()
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.start_date and getdate(self.start_date) < getdate(today()):
			frappe.throw("Treatment start date cannot be in the past")
		
		if self.target_completion_date and self.start_date:
			if getdate(self.target_completion_date) < getdate(self.start_date):
				frappe.throw("Target completion date cannot be before start date")
	
	def validate_plan_items(self):
		"""Validate treatment plan items"""
		if not self.plan_items:
			frappe.throw("Treatment plan must have at least one treatment item")
		
		# Validate sequence numbers are unique
		sequences = [item.treatment_sequence for item in self.plan_items if item.treatment_sequence]
		if len(sequences) != len(set(sequences)):
			frappe.throw("Treatment sequence numbers must be unique")
		
		# Auto-assign sequence numbers if missing
		for i, item in enumerate(self.plan_items):
			if not item.treatment_sequence:
				item.treatment_sequence = i + 1
	
	def calculate_totals(self):
		"""Calculate total cost and duration from plan items"""
		total_cost = 0
		total_duration = 0
		
		for item in self.plan_items:
			# Auto-populate item details if missing
			if item.procedure_code:
				try:
					procedure = frappe.get_doc("Dental Procedure Master", item.procedure_code)
					# Only auto-populate if values are not already set
					if not item.estimated_cost:
						item.estimated_cost = procedure.standard_fee
					if not item.estimated_duration:
						item.estimated_duration = procedure.duration_minutes
					if not item.insurance_coverage_percentage:
						item.insurance_coverage_percentage = procedure.insurance_coverage
				except frappe.DoesNotExistError:
					pass
			
			# Calculate insurance amounts for each item
			if item.estimated_cost and item.insurance_coverage_percentage:
				item.insurance_amount = flt(item.estimated_cost * item.insurance_coverage_percentage / 100)
				item.patient_portion = flt(item.estimated_cost - item.insurance_amount)
			else:
				item.patient_portion = item.estimated_cost or 0
			
			# Add to totals
			if item.estimated_cost:
				total_cost += item.estimated_cost
			if item.estimated_duration:
				total_duration += item.estimated_duration
		
		# Update main document totals
		self.total_estimated_cost = total_cost
		self.total_estimated_duration = total_duration
		
		# Calculate overall insurance amounts
		# Prioritize individual item calculations over plan-level percentage
		individual_insurance_total = sum([flt(item.insurance_amount) for item in self.plan_items])
		
		if individual_insurance_total > 0:
			# Use sum of individual item insurance amounts
			self.insurance_amount = individual_insurance_total
		elif self.insurance_coverage_percentage and total_cost:
			# Fall back to plan-level percentage if no individual amounts
			self.insurance_amount = flt(total_cost * self.insurance_coverage_percentage / 100)
		else:
			self.insurance_amount = 0
		
		self.patient_portion = flt(total_cost - self.insurance_amount)
	
	def update_progress(self):
		"""Update plan progress based on completed items"""
		if not self.plan_items:
			return
		
		total_items = len(self.plan_items)
		completed_items = len([item for item in self.plan_items if item.item_status == "Completed"])
		
		self.total_items = total_items
		self.completed_items = completed_items
		
		if total_items > 0:
			self.plan_progress = flt(completed_items / total_items * 100, 2)
		else:
			self.plan_progress = 0
		
		# Auto-update plan status based on progress
		if self.plan_progress == 100 and self.plan_status != "Completed":
			self.plan_status = "Completed"
			self.actual_completion_date = today()
		elif self.plan_progress > 0 and self.plan_status == "Draft":
			self.plan_status = "In Progress"
	
	def set_default_values(self):
		"""Set default values for new treatment plans"""
		if not self.created_by:
			self.created_by = frappe.session.user
		
		if not self.plan_date:
			self.plan_date = today()
		
		# Auto-link dental chart if patient is selected
		if self.patient and not self.dental_chart:
			chart = frappe.db.get_value("Dental Chart", {"patient": self.patient}, "name")
			if chart:
				self.dental_chart = chart
	
	def before_submit(self):
		"""Actions before submitting treatment plan"""
		if self.plan_status == "Draft":
			frappe.throw("Cannot submit a draft treatment plan. Please activate it first.")
		
		# Validate all required approvals
		if not self.approved_by:
			frappe.throw("Treatment plan must be approved before submission")
	
	def on_submit(self):
		"""Actions after submitting treatment plan"""
		self.plan_status = "Active"
		self.save()
		
		# Create initial appointments for urgent items
		self.schedule_urgent_treatments()
	
	def activate_plan(self):
		"""Activate the treatment plan"""
		if self.plan_status != "Draft":
			frappe.throw("Only draft plans can be activated")
		
		self.plan_status = "Active"
		if not self.start_date:
			self.start_date = today()
		
		self.save()
		
		# Auto-schedule high priority items
		self.schedule_high_priority_treatments()
	
	def complete_plan(self):
		"""Mark treatment plan as completed"""
		incomplete_items = [item for item in self.plan_items if item.item_status not in ["Completed", "Cancelled"]]
		
		if incomplete_items:
			frappe.throw(f"Cannot complete plan. {len(incomplete_items)} items are still pending.")
		
		self.plan_status = "Completed"
		self.actual_completion_date = today()
		self.save()
	
	def cancel_plan(self, reason=None):
		"""Cancel the treatment plan"""
		self.plan_status = "Cancelled"
		if reason:
			self.add_comment("Comment", f"Plan cancelled: {reason}")
		
		# Cancel all pending appointments
		for item in self.plan_items:
			if item.scheduled_appointment and item.item_status not in ["Completed", "Cancelled"]:
				try:
					appointment = frappe.get_doc("Dental Appointment", item.scheduled_appointment)
					appointment.cancel_appointment(f"Treatment plan {self.name} cancelled")
				except Exception:
					pass
		
		self.save()
	
	def schedule_urgent_treatments(self):
		"""Schedule appointments for urgent treatment items"""
		urgent_items = [item for item in self.plan_items 
						if item.urgency_flag and item.item_status == "Planned"]
		
		for item in urgent_items:
			self.schedule_treatment_item(item.name, priority="Emergency")
	
	def schedule_high_priority_treatments(self):
		"""Schedule appointments for high priority items"""
		high_priority_items = [item for item in self.plan_items 
							   if item.priority in ["High", "Urgent"] and item.item_status == "Planned"]
		
		for item in high_priority_items:
			self.schedule_treatment_item(item.name)
	
	def schedule_treatment_item(self, item_name, priority="Routine"):
		"""Schedule an appointment for a specific treatment item"""
		item = None
		for plan_item in self.plan_items:
			if plan_item.name == item_name:
				item = plan_item
				break
		
		if not item:
			frappe.throw(f"Treatment item {item_name} not found")
		
		if item.scheduled_appointment:
			frappe.throw(f"Treatment item {item_name} is already scheduled")
		
		# Calculate appointment date (next available slot)
		appointment_date = add_days(today(), 1)  # Tomorrow as default
		
		try:
			# Create appointment
			appointment = frappe.get_doc({
				"doctype": "Dental Appointment",
				"patient": self.patient,
				"practitioner": self.dentist,
				"appointment_date": appointment_date,
				"appointment_time": "09:00:00",  # Default time
				"appointment_type": "Treatment",
				"chief_complaint": f"Treatment plan item: {item.procedure_name}",
				"dental_chart": self.dental_chart,
				"treatment_plan_reference": self.name,
				"duration_minutes": item.estimated_duration or 60,
				"estimated_cost": item.estimated_cost or 0,
				"planned_procedures": [
					{
						"procedure_code": item.procedure_code,
						"tooth_number": item.tooth_number,
						"surface": item.surface or "Whole Tooth",
						"estimated_duration": item.estimated_duration,
						"estimated_cost": item.estimated_cost,
						"notes": f"From treatment plan {self.name}"
					}
				]
			})
			appointment.insert()
			
			# Link appointment back to treatment item
			item.scheduled_appointment = appointment.name
			item.item_status = "Scheduled"
			self.save()
			
			return appointment.name
			
		except Exception as e:
			frappe.log_error(f"Failed to schedule treatment item {item_name}: {str(e)}")
			frappe.throw(f"Failed to schedule treatment: {str(e)}")
	
	def update_item_status(self, item_name, status, completed_by=None):
		"""Update the status of a treatment plan item"""
		item = None
		for plan_item in self.plan_items:
			if plan_item.name == item_name:
				item = plan_item
				break
		
		if not item:
			frappe.throw(f"Treatment item {item_name} not found")
		
		old_status = item.item_status
		item.item_status = status
		
		if status == "Completed":
			item.completed_date = today()
			if completed_by:
				item.completed_by = completed_by
		
		# Update overall plan progress
		self.update_progress()
		self.save()
		
		# Log the status change
		self.add_comment("Comment", f"Item {item.procedure_name} status changed from {old_status} to {status}")
	
	def get_treatment_summary(self):
		"""Get comprehensive treatment plan summary"""
		summary = {
			"plan_id": self.name,
			"patient": self.patient_name,
			"dentist": self.dentist_name,
			"status": self.plan_status,
			"progress": self.plan_progress,
			"total_cost": self.total_estimated_cost,
			"patient_portion": self.patient_portion,
			"total_duration": self.total_estimated_duration,
			"items": []
		}
		
		for item in self.plan_items:
			summary["items"].append({
				"sequence": item.treatment_sequence,
				"procedure": item.procedure_name,
				"tooth": item.tooth_name or item.tooth_number,
				"surface": item.surface,
				"priority": item.priority,
				"status": item.item_status,
				"cost": item.estimated_cost,
				"duration": item.estimated_duration,
				"scheduled": bool(item.scheduled_appointment),
				"urgent": item.urgency_flag
			})
		
		return summary
	
	def generate_from_dental_chart(self, dental_chart_name):
		"""Generate treatment plan from existing dental chart conditions"""
		try:
			chart = frappe.get_doc("Dental Chart", dental_chart_name)
			
			sequence = 1
			
			# Add procedures for each condition that requires treatment
			for condition in chart.tooth_conditions:
				if condition.treatment_required:
					# Find appropriate procedure for this condition
					procedure_code = self.get_procedure_for_condition(condition.condition_code)
					
					if procedure_code:
						self.append("plan_items", {
							"treatment_sequence": sequence,
							"procedure_code": procedure_code,
							"tooth_number": condition.tooth_number,
							"surface": condition.surface,
							"priority": "High" if condition.emergency_condition else "Medium",
							"urgency_flag": condition.emergency_condition,
							"notes": f"Treatment for {condition.condition_name}"
						})
						sequence += 1
			
			self.save()
			
		except Exception as e:
			frappe.throw(f"Failed to generate treatment plan from dental chart: {str(e)}")
	
	def get_procedure_for_condition(self, condition_code):
		"""Get appropriate procedure code for a dental condition"""
		# This is a simplified mapping - in practice, this would be more sophisticated
		condition_procedure_map = {
			"CAR001": "REST001",  # Small Cavity -> Composite Filling
			"CAR002": "REST002",  # Large Cavity -> Crown
			"PER001": "PREV002",  # Gingivitis -> Deep Cleaning
			"END001": "ENDO001",  # Pulpitis -> Root Canal
			# Add more mappings as needed
		}
		
		return condition_procedure_map.get(condition_code)
	
	@staticmethod
	def get_active_plans_for_patient(patient):
		"""Get all active treatment plans for a patient"""
		return frappe.get_all("Treatment Plan",
			filters={
				"patient": patient,
				"plan_status": ["in", ["Active", "In Progress"]],
				"docstatus": ["!=", 2]
			},
			fields=["name", "plan_date", "plan_status", "plan_progress", "total_estimated_cost"],
			order_by="plan_date desc"
		)
	
	@staticmethod
	def get_pending_treatments_for_dentist(dentist):
		"""Get all pending treatment items for a dentist"""
		plans = frappe.get_all("Treatment Plan",
			filters={
				"dentist": dentist,
				"plan_status": ["in", ["Active", "In Progress"]],
				"docstatus": ["!=", 2]
			},
			fields=["name"]
		)
		
		pending_items = []
		for plan in plans:
			plan_doc = frappe.get_doc("Treatment Plan", plan.name)
			for item in plan_doc.plan_items:
				if item.item_status in ["Planned", "Scheduled"]:
					pending_items.append({
						"plan": plan.name,
						"patient": plan_doc.patient_name,
						"procedure": item.procedure_name,
						"tooth": item.tooth_number,
						"priority": item.priority,
						"status": item.item_status,
						"urgent": item.urgency_flag
					})
		
		return pending_items 