# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest
import json


class TestToothMaster(unittest.TestCase):
	def setUp(self):
		# Clean up any existing test teeth
		frappe.db.delete("Tooth Master", {"tooth_number": ["in", ["TEST1", "TEST2"]]})
		
	def test_tooth_creation(self):
		# Test creating a standard tooth with FDI numbering
		tooth = frappe.get_doc({
			"doctype": "Tooth Master",
			"tooth_number": "TEST1",
			"universal_number": 11,  # FDI: Upper Right Central Incisor
			"tooth_name": "Test Central Incisor",
			"tooth_type": "Incisor",
			"dentition_type": "Permanent"
		})
		tooth.insert()
		
		# Check computed fields
		self.assertEqual(tooth.arch, "Upper")
		self.assertEqual(tooth.quadrant, "Upper Right")
		self.assertEqual(tooth.position_in_quadrant, 1)
	
	def test_universal_number_validation(self):
		# Test invalid universal number for permanent teeth (FDI)
		tooth = frappe.get_doc({
			"doctype": "Tooth Master",
			"tooth_number": "TEST2",
			"universal_number": 19,  # Invalid FDI number
			"tooth_name": "Test Tooth",
			"tooth_type": "Incisor",
			"dentition_type": "Permanent"
		})
		
		with self.assertRaises(frappe.ValidationError):
			tooth.insert()
	
	def test_quadrant_calculation(self):
		# Test different quadrants with FDI numbering
		test_cases = [
			{"num": 11, "arch": "Upper", "quadrant": "Upper Right"},
			{"num": 21, "arch": "Upper", "quadrant": "Upper Left"},
			{"num": 31, "arch": "Lower", "quadrant": "Lower Left"},
			{"num": 41, "arch": "Lower", "quadrant": "Lower Right"}
		]
		
		for i, case in enumerate(test_cases):
			tooth = frappe.get_doc({
				"doctype": "Tooth Master",
				"tooth_number": f"TEST_Q{i}",
				"universal_number": case["num"],
				"tooth_name": f"Test Tooth {case['num']}",
				"tooth_type": "Incisor",
				"dentition_type": "Permanent"
			})
			tooth.insert()
			
			self.assertEqual(tooth.arch, case["arch"])
			self.assertEqual(tooth.quadrant, case["quadrant"])
			
			# Clean up
			tooth.delete()
	
	def test_surfaces_json(self):
		# Test surfaces field with JSON data
		surfaces = ["Occlusal", "Mesial", "Distal", "Buccal", "Lingual"]
		tooth = frappe.get_doc({
			"doctype": "Tooth Master",
			"tooth_number": "TEST_SURF",
			"universal_number": 16,  # FDI: Upper Right First Molar
			"tooth_name": "Test Molar",
			"tooth_type": "Molar",
			"dentition_type": "Permanent",
			"surfaces": json.dumps(surfaces)
		})
		tooth.insert()
		
		# Verify surfaces can be parsed
		parsed_surfaces = json.loads(tooth.surfaces)
		self.assertEqual(parsed_surfaces, surfaces)
		
		# Clean up
		tooth.delete()
	
	def test_create_standard_teeth(self):
		# Test the static method for creating all teeth
		# First, ensure no teeth exist
		existing_count = frappe.db.count("Tooth Master", {"dentition_type": "Permanent"})
		
		# Create standard teeth
		result = ToothMaster.create_standard_teeth()
		
		# Check that teeth were created
		new_count = frappe.db.count("Tooth Master", {"dentition_type": "Permanent"})
		self.assertGreater(new_count, existing_count)
		
		# Verify specific teeth exist with FDI numbering
		tooth_11 = frappe.get_doc("Tooth Master", "11")
		self.assertEqual(tooth_11.tooth_name, "Upper Right Central Incisor")
		self.assertEqual(tooth_11.tooth_type, "Incisor")
		
		tooth_48 = frappe.get_doc("Tooth Master", "48")
		self.assertEqual(tooth_48.tooth_name, "Lower Right Third Molar (Wisdom)")
		self.assertEqual(tooth_48.tooth_type, "Wisdom Tooth")
	
	def tearDown(self):
		# Clean up test data
		test_teeth = ["TEST1", "TEST2", "TEST_Q0", "TEST_Q1", "TEST_Q2", "TEST_Q3", "TEST_SURF"]
		for tooth_num in test_teeth:
			if frappe.db.exists("Tooth Master", tooth_num):
				frappe.delete_doc("Tooth Master", tooth_num)


# Import the class for the static method test
from dentcharts.dentcharts.doctype.tooth_master.tooth_master import ToothMaster 