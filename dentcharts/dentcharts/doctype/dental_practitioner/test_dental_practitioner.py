# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest


class TestDentalPractitioner(unittest.TestCase):
	def setUp(self):
		# Create a test healthcare practitioner first
		if not frappe.db.exists("Healthcare Practitioner", "HP-TEST-001"):
			practitioner = frappe.get_doc({
				"doctype": "Healthcare Practitioner",
				"practitioner_name": "Dr. Test Dentist",
				"first_name": "Test",
				"last_name": "Dentist",
				"name": "HP-TEST-001",
				"mobile": "1234567890"
			})
			practitioner.insert()
		
		# Create a test dental practitioner
		if not frappe.db.exists("Dental Practitioner", "HP-TEST-001"):
			dental_practitioner = frappe.get_doc({
				"doctype": "Dental Practitioner",
				"healthcare_practitioner": "HP-TEST-001",
				"dental_license_number": "DL12345",
				"specialization": "General Dentistry",
				"years_of_experience": 5,
				"consultation_fee": 100
			})
			dental_practitioner.insert()
	
	def test_dental_practitioner_creation(self):
		dental_practitioner = frappe.get_doc("Dental Practitioner", "HP-TEST-001")
		self.assertEqual(dental_practitioner.healthcare_practitioner, "HP-TEST-001")
		self.assertEqual(dental_practitioner.specialization, "General Dentistry")
	
	def test_practitioner_name_fetch(self):
		dental_practitioner = frappe.get_doc("Dental Practitioner", "HP-TEST-001")
		self.assertEqual(dental_practitioner.practitioner_name, "Dr. Test Dentist")
	
	def test_default_consultation_fee(self):
		dental_practitioner = frappe.get_doc("Dental Practitioner", "HP-TEST-001")
		self.assertEqual(dental_practitioner.consultation_fee, 100)
	
	def tearDown(self):
		# Clean up test data
		if frappe.db.exists("Dental Practitioner", "HP-TEST-001"):
			frappe.delete_doc("Dental Practitioner", "HP-TEST-001")
		if frappe.db.exists("Healthcare Practitioner", "HP-TEST-001"):
			frappe.delete_doc("Healthcare Practitioner", "HP-TEST-001") 