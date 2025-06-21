# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest


class TestDentalConditionMaster(unittest.TestCase):
	def setUp(self):
		# Clean up any existing test conditions
		frappe.db.delete("Dental Condition Master", {"condition_code": ["like", "TEST%"]})
		
	def test_condition_creation(self):
		# Test creating a standard condition
		condition = frappe.get_doc({
			"doctype": "Dental Condition Master",
			"condition_code": "TEST001",
			"condition_name": "Test Cavity",
			"category": "Caries",
			"severity": "Medium"
		})
		condition.insert()
		
		# Check default values were set
		self.assertEqual(condition.symbol, "C")
		self.assertEqual(condition.color_code, "#ffc107")  # Yellow for Medium
		self.assertTrue(condition.requires_treatment)
		
	def test_color_validation(self):
		# Test invalid color code
		condition = frappe.get_doc({
			"doctype": "Dental Condition Master",
			"condition_code": "TEST002",
			"condition_name": "Test Condition",
			"category": "Caries",
			"severity": "Low",
			"color_code": "invalid"
		})
		
		with self.assertRaises(frappe.ValidationError):
			condition.insert()
	
	def test_default_colors(self):
		# Test default colors for different severities
		severities = ["Low", "Medium", "High", "Critical"]
		expected_colors = ["#28a745", "#ffc107", "#fd7e14", "#dc3545"]
		
		for i, (severity, expected_color) in enumerate(zip(severities, expected_colors)):
			condition = frappe.get_doc({
				"doctype": "Dental Condition Master",
				"condition_code": f"TEST_SEV{i}",
				"condition_name": f"Test {severity} Condition",
				"category": "Caries",
				"severity": severity
			})
			condition.insert()
			
			self.assertEqual(condition.color_code, expected_color)
			
			# Clean up
			condition.delete()
	
	def test_default_symbols(self):
		# Test default symbols for different categories
		categories = ["Caries", "Periodontal", "Endodontic", "Emergency"]
		expected_symbols = ["C", "P", "E", "!"]
		
		for i, (category, expected_symbol) in enumerate(zip(categories, expected_symbols)):
			condition = frappe.get_doc({
				"doctype": "Dental Condition Master",
				"condition_code": f"TEST_CAT{i}",
				"condition_name": f"Test {category} Condition",
				"category": category,
				"severity": "Medium"
			})
			condition.insert()
			
			self.assertEqual(condition.symbol, expected_symbol)
			
			# Clean up
			condition.delete()
	
	def test_emergency_conditions(self):
		# Test emergency condition creation
		condition = frappe.get_doc({
			"doctype": "Dental Condition Master",
			"condition_code": "TEST_EMERG",
			"condition_name": "Test Emergency",
			"category": "Emergency",
			"severity": "Critical",
			"is_emergency": 1
		})
		condition.insert()
		
		self.assertTrue(condition.is_emergency)
		self.assertEqual(condition.severity, "Critical")
		self.assertEqual(condition.symbol, "!")
		
		# Clean up
		condition.delete()
	
	def test_create_standard_conditions(self):
		# Test the static method for creating all conditions
		from dentcharts.dentcharts.doctype.dental_condition_master.dental_condition_master import DentalConditionMaster
		
		# Get count before
		existing_count = frappe.db.count("Dental Condition Master")
		
		# Create standard conditions
		result = DentalConditionMaster.create_standard_conditions()
		
		# Check that conditions were created
		new_count = frappe.db.count("Dental Condition Master")
		self.assertGreater(new_count, existing_count)
		
		# Verify specific conditions exist
		cavity_condition = frappe.get_doc("Dental Condition Master", "CAR001")
		self.assertEqual(cavity_condition.condition_name, "Small Cavity")
		self.assertEqual(cavity_condition.category, "Caries")
		
		abscess_condition = frappe.get_doc("Dental Condition Master", "END003")
		self.assertEqual(abscess_condition.condition_name, "Apical Abscess")
		self.assertTrue(abscess_condition.is_emergency)
	
	def tearDown(self):
		# Clean up test data
		test_conditions = frappe.get_all("Dental Condition Master", 
			filters={"condition_code": ["like", "TEST%"]}, pluck="name")
		for condition_name in test_conditions:
			frappe.delete_doc("Dental Condition Master", condition_name) 