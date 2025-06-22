# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest
import time
import random


class TestDentalPractitioner(unittest.TestCase):
	def setUp(self):
		# Use timestamp + random number to ensure unique test data
		self.timestamp = str(int(time.time())) + str(random.randint(1000, 9999))
		self.practitioner_id = f"HP-TEST-{self.timestamp}"
		self.dental_practitioner_id = f"DP-TEST-{self.timestamp}"
		
		# Clean up any existing test data first
		self.cleanup_test_data()
		
		# Create a test healthcare practitioner first
		practitioner = frappe.get_doc({
			"doctype": "Healthcare Practitioner",
			"practitioner_name": f"Dr. Test Dentist {self.timestamp}",
			"first_name": "Test",
			"last_name": f"Dentist{self.timestamp}",
			"name": self.practitioner_id,
			"mobile": "1234567890"
		})
		practitioner.insert()
		frappe.db.commit()  # Ensure the practitioner is committed to DB
		
		# Verify practitioner exists before creating dental practitioner
		if not frappe.db.exists("Healthcare Practitioner", self.practitioner_id):
			raise Exception(f"Healthcare Practitioner {self.practitioner_id} was not created successfully")
		
		# Create a test dental practitioner
		dental_practitioner = frappe.get_doc({
			"doctype": "Dental Practitioner",
			"name": self.dental_practitioner_id,
			"healthcare_practitioner": self.practitioner_id,
			"dental_license_number": f"DL{self.timestamp}",
			"specialization": "General Dentistry",
			"years_of_experience": 5,
			"consultation_fee": 100
		})
		dental_practitioner.insert()
		frappe.db.commit()
	
	def test_dental_practitioner_creation(self):
		dental_practitioner = frappe.get_doc("Dental Practitioner", self.dental_practitioner_id)
		self.assertEqual(dental_practitioner.healthcare_practitioner, self.practitioner_id)
		self.assertEqual(dental_practitioner.specialization, "General Dentistry")
	
	def test_practitioner_name_fetch(self):
		dental_practitioner = frappe.get_doc("Dental Practitioner", self.dental_practitioner_id)
		self.assertEqual(dental_practitioner.practitioner_name, f"Dr. Test Dentist {self.timestamp}")
	
	def test_default_consultation_fee(self):
		dental_practitioner = frappe.get_doc("Dental Practitioner", self.dental_practitioner_id)
		self.assertEqual(dental_practitioner.consultation_fee, 100)
	
	def cleanup_test_data(self):
		"""Clean up any existing test data"""
		# Clean up dental practitioners
		existing_dental_practitioners = frappe.get_all("Dental Practitioner", 
			filters={"name": ["like", "DP-TEST-%"]}, pluck="name")
		for dp_name in existing_dental_practitioners:
			try:
				frappe.delete_doc("Dental Practitioner", dp_name, force=True)
			except:
				pass
		
		# Clean up healthcare practitioners
		existing_practitioners = frappe.get_all("Healthcare Practitioner", 
			filters={"name": ["like", "HP-TEST-%"]}, pluck="name")
		for hp_name in existing_practitioners:
			try:
				frappe.delete_doc("Healthcare Practitioner", hp_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		# Clean up test data
		try:
			if frappe.db.exists("Dental Practitioner", self.dental_practitioner_id):
				frappe.delete_doc("Dental Practitioner", self.dental_practitioner_id, force=True)
			if frappe.db.exists("Healthcare Practitioner", self.practitioner_id):
				frappe.delete_doc("Healthcare Practitioner", self.practitioner_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors 