# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalPatient(Document):
	def validate(self):
		self.validate_healthcare_patient()
		self.validate_emergency_contact()
		self.set_patient_name()
		self.validate_date_of_registration()
		self.validate_source()
	
	def validate_healthcare_patient(self):
		# If linking to existing Patient, verify it; otherwise ensure required data for new Patient
		if self.healthcare_patient:
			if not frappe.db.exists("Patient", self.healthcare_patient):
				frappe.throw("Healthcare Patient does not exist")
		else:
			# New Patient creation: require first_name and gender
			if not self.first_name:
				frappe.throw("First Name is required for new Patient")
			if not self.sex:
				frappe.throw("Gender is required for new Patient")
	
	def validate_emergency_contact(self):
		if self.emergency_phone and len(self.emergency_phone) < 10:
			frappe.throw("Please enter a valid emergency phone number")
	
	def validate_date_of_registration(self):
		"""Validate date of registration is not in the future"""
		if self.date_of_registration:
			from frappe.utils import today
			if self.date_of_registration > today():
				frappe.throw("Date of Registration cannot be in the future")
	
	def validate_source(self):
		"""Validate source field is not empty if provided"""
		if self.source and len(self.source.strip()) == 0:
			frappe.throw("Source cannot be empty if provided")
	
	def set_patient_name(self):
		if self.healthcare_patient:
			patient_name = frappe.db.get_value("Patient", self.healthcare_patient, "patient_name")
			if patient_name:
				self.patient_name = patient_name
	
	def before_save(self):
		# Create dental chart if it doesn't exist
		self.ensure_dental_chart_exists()
	
	def ensure_dental_chart_exists(self):
		"""Ensure a MASTER dental chart exists for this patient"""
		# Check if a master chart already exists
		existing_chart = frappe.db.exists("Dental Chart", {
			"patient": self.healthcare_patient,
			"chart_type": "Master Chart"
		})
		
		if not existing_chart:
			# Get a default practitioner - try multiple sources
			default_dentist = self.get_default_practitioner()
			
			# Create a MASTER dental chart for this patient
			chart_data = {
				"doctype": "Dental Chart",
				"patient": self.healthcare_patient,
				"chart_type": "Master Chart",
				"status": "Active",
				"dentition_type": "Permanent",  # Default to permanent, can be changed
				"notes": f"Master Dental Chart created for {self.patient_name}\nCreated on: {frappe.utils.now()}\n--- Patient Registration ---"
			}
			
			# Add chief complaint to the chart if available
			if self.chief_complaint:
				chart_data["chief_complaint"] = self.chief_complaint
			
			# Only add dentist if we found one
			if default_dentist:
				chart_data["dentist"] = default_dentist
			
			chart = frappe.get_doc(chart_data)
			chart.insert(ignore_permissions=True)
			
			frappe.msgprint(
				f"Master Dental Chart created successfully for {self.patient_name}",
				title="Master Chart Created",
				indicator="green"
			)
	
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

	def before_insert(self):
		"""Automatically set or create a Healthcare Patient if not provided"""
		# Use existing Patient if selected via patient_name link
		if not self.healthcare_patient and self.patient_name:
			if frappe.db.exists("Patient", self.patient_name):
				self.healthcare_patient = self.patient_name
				return
		# Otherwise create a new Patient record
		if not self.healthcare_patient:
			patient_data = {
				"doctype": "Patient",
				"first_name": self.first_name,
				"sex": self.sex,
				"patient_name": self.patient_name or f"{self.first_name} {self.last_name or ''}".strip()
			}
			# Include optional fields
			if getattr(self, "last_name", None):
				patient_data["last_name"] = self.last_name
			if getattr(self, "dob", None):
				patient_data["dob"] = self.dob
			if getattr(self, "mobile", None):
				patient_data["mobile"] = self.mobile
			if getattr(self, "email", None):
				patient_data["email"] = self.email
			if getattr(self, "address", None):
				patient_data["address"] = self.address
			# Create the Patient doc
			patient_doc = frappe.get_doc(patient_data)
			patient_doc.insert(ignore_permissions=True)
			self.healthcare_patient = patient_doc.name 