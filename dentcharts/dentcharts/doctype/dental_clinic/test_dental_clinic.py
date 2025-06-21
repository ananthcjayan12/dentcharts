# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest


class TestDentalClinic(unittest.TestCase):
	def setUp(self):
		# Create a test clinic
		if not frappe.db.exists("Dental Clinic", "TEST001"):
			clinic = frappe.get_doc({
				"doctype": "Dental Clinic",
				"clinic_name": "Test Dental Clinic",
				"clinic_code": "TEST001",
				"status": "Active",
				"email": "test@dental.com",
				"phone": "1234567890"
			})
			clinic.insert()
	
	def test_clinic_creation(self):
		clinic = frappe.get_doc("Dental Clinic", "TEST001")
		self.assertEqual(clinic.clinic_name, "Test Dental Clinic")
		self.assertEqual(clinic.status, "Active")
	
	def tearDown(self):
		# Clean up test data
		if frappe.db.exists("Dental Clinic", "TEST001"):
			frappe.delete_doc("Dental Clinic", "TEST001") 