# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalPractitioner(Document):
	def validate(self):
		self.validate_healthcare_practitioner()
		self.validate_license_number()
		self.set_practitioner_name()
	
	def validate_healthcare_practitioner(self):
		if not self.healthcare_practitioner:
			frappe.throw("Healthcare Practitioner is required")
		
		# Check if healthcare practitioner exists
		if not frappe.db.exists("Healthcare Practitioner", self.healthcare_practitioner):
			frappe.throw("Healthcare Practitioner does not exist")
	
	def validate_license_number(self):
		if self.dental_license_number:
			# Check if license number is unique
			existing = frappe.db.get_value("Dental Practitioner", 
				{"dental_license_number": self.dental_license_number, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Dental License Number {self.dental_license_number} already exists")
	
	def set_practitioner_name(self):
		if self.healthcare_practitioner:
			practitioner_name = frappe.db.get_value("Healthcare Practitioner", 
				self.healthcare_practitioner, "practitioner_name")
			if practitioner_name:
				self.practitioner_name = practitioner_name
	
	def before_save(self):
		# Set default consultation fee based on specialization
		self.set_default_consultation_fee()
	
	def set_default_consultation_fee(self):
		"""Set default consultation fee based on specialization if not already set"""
		if not self.consultation_fee and self.specialization:
			default_fees = {
				"General Dentistry": 100,
				"Orthodontics": 150,
				"Endodontics": 200,
				"Periodontics": 175,
				"Oral Surgery": 250,
				"Prosthodontics": 200,
				"Pediatric Dentistry": 120
			}
			self.consultation_fee = default_fees.get(self.specialization, 100) 