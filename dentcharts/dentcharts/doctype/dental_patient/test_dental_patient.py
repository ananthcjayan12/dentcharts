# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest


class TestDentalPatient(unittest.TestCase):
	def setUp(self):
		# Create a test healthcare patient first
		if not frappe.db.exists("Patient", "PAT-TEST-001"):
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": "Test Patient",
				"name": "PAT-TEST-001",
				"sex": "Male"
			})
			patient.insert()
		
		# Create a test dental patient
		if not frappe.db.exists("Dental Patient", "PAT-TEST-001"):
			dental_patient = frappe.get_doc({
				"doctype": "Dental Patient",
				"healthcare_patient": "PAT-TEST-001",
				"dental_history": "No previous dental issues",
				"emergency_contact": "John Doe",
				"emergency_phone": "1234567890"
			})
			dental_patient.insert()
	
	def test_dental_patient_creation(self):
		dental_patient = frappe.get_doc("Dental Patient", "PAT-TEST-001")
		self.assertEqual(dental_patient.healthcare_patient, "PAT-TEST-001")
		self.assertEqual(dental_patient.emergency_contact, "John Doe")
	
	def test_patient_name_fetch(self):
		dental_patient = frappe.get_doc("Dental Patient", "PAT-TEST-001")
		self.assertEqual(dental_patient.patient_name, "Test Patient")
	
	def tearDown(self):
		# Clean up test data
		if frappe.db.exists("Dental Patient", "PAT-TEST-001"):
			frappe.delete_doc("Dental Patient", "PAT-TEST-001")
		if frappe.db.exists("Patient", "PAT-TEST-001"):
			frappe.delete_doc("Patient", "PAT-TEST-001") 