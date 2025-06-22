import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

class TreatmentPlanItem(Document):
	def validate(self):
		"""Validate treatment plan item data"""
		self.validate_tooth_surface_combination()
		self.set_procedure_details()
		self.calculate_costs()
		self.validate_status_transitions()
	
	def validate_tooth_surface_combination(self):
		"""Validate that the selected surface is appropriate for the tooth"""
		if not self.tooth_number or not self.surface:
			return
		
		# Get tooth information
		try:
			tooth = frappe.get_doc("Tooth Master", self.tooth_number)
			
			# Validate surface selection based on tooth type
			invalid_combinations = []
			
			# Incisors don't have occlusal surfaces
			if tooth.tooth_type == "Incisor" and self.surface == "Occlusal":
				invalid_combinations.append("Incisors don't have occlusal surfaces")
			
			# Canines typically don't have occlusal surfaces
			if tooth.tooth_type == "Canine" and self.surface == "Occlusal":
				frappe.msgprint("Warning: Canines typically don't have occlusal surfaces", alert=True)
			
			if invalid_combinations:
				frappe.throw("; ".join(invalid_combinations))
				
		except frappe.DoesNotExistError:
			pass  # Tooth master doesn't exist, skip validation
	
	def set_procedure_details(self):
		"""Auto-populate procedure details from master data"""
		if self.procedure_code:
			try:
				procedure_master = frappe.get_doc("Dental Procedure Master", self.procedure_code)
				
				# Set cost and duration from master data if not already set
				if not self.estimated_cost:
					self.estimated_cost = procedure_master.standard_fee
				if not self.estimated_duration:
					self.estimated_duration = procedure_master.duration_minutes
				if not self.insurance_coverage_percentage:
					self.insurance_coverage_percentage = procedure_master.insurance_coverage_percentage
				
				# Set urgency flag for emergency procedures
				if procedure_master.category == "Emergency" and not self.urgency_flag:
					self.urgency_flag = 1
					self.priority = "Urgent"
				
			except frappe.DoesNotExistError:
				# If procedure master doesn't exist, set default values
				if not self.estimated_cost:
					self.estimated_cost = 100
				if not self.estimated_duration:
					self.estimated_duration = 60
	
	def calculate_costs(self):
		"""Calculate insurance and patient portions"""
		if self.estimated_cost and self.insurance_coverage_percentage:
			self.insurance_amount = flt(self.estimated_cost * self.insurance_coverage_percentage / 100)
			self.patient_portion = flt(self.estimated_cost - self.insurance_amount)
		else:
			self.insurance_amount = 0
			self.patient_portion = self.estimated_cost or 0 