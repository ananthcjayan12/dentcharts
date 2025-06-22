# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest
import time
import random


class TestDentalPatient(unittest.TestCase):
	def setUp(self):
		# Use timestamp + random number to ensure unique test data
		self.timestamp = str(int(time.time())) + str(random.randint(1000, 9999))
		self.patient_id = f"PAT-TEST-{self.timestamp}"
		self.dental_patient_id = f"DP-TEST-{self.timestamp}"
		
		# Clean up any existing test data first
		self.cleanup_test_data()
		
		# Create a test healthcare patient first
		patient = frappe.get_doc({
			"doctype": "Patient",
			"patient_name": f"Test Patient {self.timestamp}",
			"first_name": "Test",
			"last_name": f"Patient{self.timestamp}",
			"name": self.patient_id,
			"sex": "Male"
		})
		patient.insert()
		frappe.db.commit()  # Ensure the patient is committed to DB
		
		# Verify patient exists before creating dental patient
		if not frappe.db.exists("Patient", self.patient_id):
			raise Exception(f"Patient {self.patient_id} was not created successfully")
		
		# Create a test dental patient
		dental_patient = frappe.get_doc({
			"doctype": "Dental Patient",
			"name": self.dental_patient_id,
			"healthcare_patient": self.patient_id,
			"dental_history": "No previous dental issues",
			"emergency_contact": "John Doe",
			"emergency_phone": "1234567890"
		})
		dental_patient.insert()
		frappe.db.commit()
	
	def test_dental_patient_creation(self):
		dental_patient = frappe.get_doc("Dental Patient", self.dental_patient_id)
		self.assertEqual(dental_patient.healthcare_patient, self.patient_id)
		self.assertEqual(dental_patient.emergency_contact, "John Doe")
	
	def test_patient_name_fetch(self):
		dental_patient = frappe.get_doc("Dental Patient", self.dental_patient_id)
		self.assertEqual(dental_patient.patient_name, f"Test Patient {self.timestamp}")
	
	def cleanup_test_data(self):
		"""Clean up any existing test data"""
		# Clean up dental patients
		existing_dental_patients = frappe.get_all("Dental Patient", 
			filters={"name": ["like", "DP-TEST-%"]}, pluck="name")
		for dp_name in existing_dental_patients:
			try:
				frappe.delete_doc("Dental Patient", dp_name, force=True)
			except:
				pass
		
		# Clean up patients
		existing_patients = frappe.get_all("Patient", 
			filters={"name": ["like", "PAT-TEST-%"]}, pluck="name")
		for p_name in existing_patients:
			try:
				frappe.delete_doc("Patient", p_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		# Clean up test data
		try:
			if frappe.db.exists("Dental Patient", self.dental_patient_id):
				frappe.delete_doc("Dental Patient", self.dental_patient_id, force=True)
			if frappe.db.exists("Patient", self.patient_id):
				frappe.delete_doc("Patient", self.patient_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors 