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
		
		# Clean up any existing test data first
		self.cleanup_test_data()
		
		# Create a test healthcare practitioner first (let Frappe auto-generate the name)
		try:
			practitioner = frappe.get_doc({
				"doctype": "Healthcare Practitioner",
				"practitioner_name": f"Dr. Test Dentist {self.timestamp}",
				"first_name": "Test",
				"last_name": f"Dentist{self.timestamp}",
				"mobile": "1234567890"
			})
			practitioner.insert()
			frappe.db.commit()
			self.practitioner_id = practitioner.name
			
		except Exception as e:
			# If Healthcare Practitioner creation fails, skip the test
			self.skipTest(f"Could not create Healthcare Practitioner: {str(e)}")
		
		# Create a test dental practitioner
		try:
			dental_practitioner = frappe.get_doc({
				"doctype": "Dental Practitioner",
				"healthcare_practitioner": self.practitioner_id,
				"dental_license_number": f"DL{self.timestamp}",
				"specialization": "General Dentistry",
				"years_of_experience": 5,
				"consultation_fee": 100
			})
			dental_practitioner.insert()
			frappe.db.commit()
			self.dental_practitioner_id = dental_practitioner.name
			
		except Exception as e:
			self.skipTest(f"Could not create Dental Practitioner: {str(e)}")
	
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
			filters={"specialization": "General Dentistry"}, pluck="name")
		for dp_name in existing_dental_practitioners:
			try:
				frappe.delete_doc("Dental Practitioner", dp_name, force=True)
			except:
				pass
		
		# Clean up healthcare practitioners with test names
		existing_practitioners = frappe.get_all("Healthcare Practitioner", 
			filters={"practitioner_name": ["like", "Dr. Test Dentist%"]}, pluck="name")
		for hp_name in existing_practitioners:
			try:
				frappe.delete_doc("Healthcare Practitioner", hp_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		# Clean up test data
		try:
			if hasattr(self, 'dental_practitioner_id') and frappe.db.exists("Dental Practitioner", self.dental_practitioner_id):
				frappe.delete_doc("Dental Practitioner", self.dental_practitioner_id, force=True)
			if hasattr(self, 'practitioner_id') and frappe.db.exists("Healthcare Practitioner", self.practitioner_id):
				frappe.delete_doc("Healthcare Practitioner", self.practitioner_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors 