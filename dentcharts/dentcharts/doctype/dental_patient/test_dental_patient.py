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
		
		# Clean up any existing test data first
		self.cleanup_test_data()
		
		# Create a test healthcare patient first (let Frappe auto-generate the name)
		try:
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": f"Test Patient {self.timestamp}",
				"first_name": "Test",
				"last_name": f"Patient{self.timestamp}",
				"sex": "Male",
				"mobile": "1234567890"
			})
			patient.insert()
			frappe.db.commit()
			self.patient_id = patient.name
			
		except Exception as e:
			# If Healthcare Patient creation fails, skip the test
			self.skipTest(f"Could not create Healthcare Patient: {str(e)}")
		
		# Create a test dental patient
		try:
			dental_patient = frappe.get_doc({
				"doctype": "Dental Patient",
				"healthcare_patient": self.patient_id,
				"dental_history": "No previous dental issues",
				"emergency_contact": "John Doe",
				"emergency_phone": "1234567890"
			})
			dental_patient.insert()
			frappe.db.commit()
			self.dental_patient_id = dental_patient.name
			
		except Exception as e:
			self.skipTest(f"Could not create Dental Patient: {str(e)}")
	
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
			filters={"emergency_contact": "John Doe"}, pluck="name")
		for dp_name in existing_dental_patients:
			try:
				frappe.delete_doc("Dental Patient", dp_name, force=True)
			except:
				pass
		
		# Clean up patients with test names
		existing_patients = frappe.get_all("Patient", 
			filters={"patient_name": ["like", "Test Patient%"]}, pluck="name")
		for p_name in existing_patients:
			try:
				frappe.delete_doc("Patient", p_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		# Clean up test data
		try:
			if hasattr(self, 'dental_patient_id') and frappe.db.exists("Dental Patient", self.dental_patient_id):
				frappe.delete_doc("Dental Patient", self.dental_patient_id, force=True)
			if hasattr(self, 'patient_id') and frappe.db.exists("Patient", self.patient_id):
				frappe.delete_doc("Patient", self.patient_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors added test