# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest


class TestDentalProcedureMaster(unittest.TestCase):
	def setUp(self):
		# Clean up any existing test procedures
		frappe.db.delete("Dental Procedure Master", {"procedure_code": ["like", "TEST%"]})
		
	def test_procedure_creation(self):
		# Test creating a standard procedure
		procedure = frappe.get_doc({
			"doctype": "Dental Procedure Master",
			"procedure_code": "TEST001",
			"procedure_name": "Test Filling",
			"category": "Restorative",
			"complexity": "Simple",
			"duration_minutes": 45,
			"standard_fee": 200
		})
		procedure.insert()
		
		# Check that it was created successfully
		self.assertEqual(procedure.procedure_name, "Test Filling")
		# Check that currency is set (should default to system default currency)
		default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")
		self.assertEqual(procedure.currency, default_currency or "INR")
		
	def test_duration_validation(self):
		# Test invalid duration (0 minutes)
		procedure = frappe.get_doc({
			"doctype": "Dental Procedure Master",
			"procedure_code": "TEST002",
			"procedure_name": "Test Invalid Duration",
			"category": "Restorative",
			"complexity": "Simple",
			"duration_minutes": 0
		})
		
		with self.assertRaises(frappe.ValidationError):
			procedure.insert()
		
		# Test excessive duration (over 8 hours)
		procedure2 = frappe.get_doc({
			"doctype": "Dental Procedure Master",
			"procedure_code": "TEST003",
			"procedure_name": "Test Long Duration",
			"category": "Restorative",
			"complexity": "Simple",
			"duration_minutes": 500  # Over 8 hours
		})
		
		with self.assertRaises(frappe.ValidationError):
			procedure2.insert()
	
	def test_follow_up_validation(self):
		# Test follow-up required but no days specified
		procedure = frappe.get_doc({
			"doctype": "Dental Procedure Master",
			"procedure_code": "TEST004",
			"procedure_name": "Test Follow-up Required",
			"category": "Restorative",
			"complexity": "Simple",
			"duration_minutes": 45,
			"follow_up_required": 1
			# Missing follow_up_days
		})
		
		with self.assertRaises(frappe.ValidationError):
			procedure.insert()
		
		# Test valid follow-up configuration
		procedure2 = frappe.get_doc({
			"doctype": "Dental Procedure Master",
			"procedure_code": "TEST005",
			"procedure_name": "Test Valid Follow-up",
			"category": "Restorative",
			"complexity": "Simple",
			"duration_minutes": 45,
			"follow_up_required": 1,
			"follow_up_days": 14
		})
		procedure2.insert()
		
		self.assertTrue(procedure2.follow_up_required)
		self.assertEqual(procedure2.follow_up_days, 14)
		
		# Clean up
		procedure2.delete()
	
	def test_currency_default(self):
		# Test that currency defaults properly
		procedure = frappe.get_doc({
			"doctype": "Dental Procedure Master",
			"procedure_code": "TEST006",
			"procedure_name": "Test Currency Default",
			"category": "Preventive",
			"complexity": "Simple",
			"duration_minutes": 30,
			"standard_fee": 100
		})
		procedure.insert()
		
		# Should default to system default currency
		self.assertIsNotNone(procedure.currency)
		default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")
		self.assertEqual(procedure.currency, default_currency or "INR")
		
		# Clean up
		procedure.delete()
	
	def test_create_standard_procedures(self):
		# Test the static method for creating all procedures
		from dentcharts.dentcharts.doctype.dental_procedure_master.dental_procedure_master import DentalProcedureMaster
		
		# Get existing count
		existing_count = frappe.db.count("Dental Procedure Master")
		
		# Create standard procedures (this should handle duplicates gracefully)
		result = DentalProcedureMaster.create_standard_procedures()
		
		# Check that we have a reasonable number of procedures (at least 15)
		final_count = frappe.db.count("Dental Procedure Master")
		self.assertGreaterEqual(final_count, 15, "Should have at least 15 dental procedures")
		
		# Verify specific procedures exist
		self.assertTrue(frappe.db.exists("Dental Procedure Master", "PREV001"), "Cleaning procedure should exist")
		self.assertTrue(frappe.db.exists("Dental Procedure Master", "ENDO001"), "Root canal procedure should exist")
		
		# Verify procedure details
		cleaning = frappe.get_doc("Dental Procedure Master", "PREV001")
		self.assertEqual(cleaning.procedure_name, "Routine Cleaning")
		self.assertEqual(cleaning.category, "Preventive")
		
		root_canal = frappe.get_doc("Dental Procedure Master", "ENDO001")
		self.assertEqual(root_canal.procedure_name, "Root Canal - Anterior")
		self.assertTrue(root_canal.follow_up_required)
	
	def test_complexity_categories(self):
		# Test all complexity levels
		complexities = ["Simple", "Moderate", "Complex", "Advanced"]
		
		for i, complexity in enumerate(complexities):
			procedure = frappe.get_doc({
				"doctype": "Dental Procedure Master",
				"procedure_code": f"TEST_COMP{i}",
				"procedure_name": f"Test {complexity} Procedure",
				"category": "Restorative",
				"complexity": complexity,
				"duration_minutes": 60
			})
			procedure.insert()
			
			self.assertEqual(procedure.complexity, complexity)
			
			# Clean up
			procedure.delete()
	
	def tearDown(self):
		# Clean up test data
		test_procedures = frappe.get_all("Dental Procedure Master", 
			filters={"procedure_code": ["like", "TEST%"]}, pluck="name")
		for procedure_name in test_procedures:
			frappe.delete_doc("Dental Procedure Master", procedure_name) 