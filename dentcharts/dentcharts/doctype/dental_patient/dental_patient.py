# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalPatient(Document):
	def validate(self):
		self.validate_healthcare_patient()
		self.validate_emergency_contact()
		self.set_patient_name()
	
	def validate_healthcare_patient(self):
		if not self.healthcare_patient:
			frappe.throw("Healthcare Patient is required")
		
		# Check if healthcare patient exists
		if not frappe.db.exists("Patient", self.healthcare_patient):
			frappe.throw("Healthcare Patient does not exist")
	
	def validate_emergency_contact(self):
		if self.emergency_phone and len(self.emergency_phone) < 10:
			frappe.throw("Please enter a valid emergency phone number")
	
	def set_patient_name(self):
		if self.healthcare_patient:
			patient_name = frappe.db.get_value("Patient", self.healthcare_patient, "patient_name")
			if patient_name:
				self.patient_name = patient_name
	
	def before_save(self):
		# Create dental chart if it doesn't exist
		self.ensure_dental_chart_exists()
	
	def ensure_dental_chart_exists(self):
		"""Ensure a dental chart exists for this patient"""
		if not frappe.db.exists("Dental Chart", {"patient": self.name}):
			# Will be implemented in Phase 3
			pass 