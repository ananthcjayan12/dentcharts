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
		if not frappe.db.exists("Dental Chart", {"patient": self.healthcare_patient}):
			# Get a default practitioner - try multiple sources
			default_dentist = self.get_default_practitioner()
			
			# Create a new dental chart for this patient
			chart_data = {
				"doctype": "Dental Chart",
				"patient": self.healthcare_patient,
				"chart_type": "Comprehensive",
				"status": "Draft"
			}
			
			# Only add dentist if we found one
			if default_dentist:
				chart_data["dentist"] = default_dentist
			
			chart = frappe.get_doc(chart_data)
			chart.insert(ignore_permissions=True)
	
	def get_default_practitioner(self):
		"""Get a default practitioner for dental chart creation"""
		# First check if patient has a preferred dentist
		if self.preferred_dentist:
			return self.preferred_dentist
		
		# Try to get any available Dental Practitioner's healthcare practitioner
		try:
			dental_practitioners = frappe.get_all("Dental Practitioner", 
				limit=1, 
				pluck="healthcare_practitioner",
				filters={"status": "Active"}
			)
			if dental_practitioners:
				return dental_practitioners[0]
		except:
			pass
		
		# Try to get any available Healthcare Practitioner
		try:
			practitioners = frappe.get_all("Healthcare Practitioner", 
				limit=1, 
				pluck="name",
				filters={"status": "Active"}
			)
			if practitioners:
				return practitioners[0]
		except:
			pass
		
		# Last resort - return None and let the chart creation handle it
		return None 