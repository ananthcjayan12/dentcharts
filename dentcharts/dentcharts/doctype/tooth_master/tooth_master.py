# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class ToothMaster(Document):
	def validate(self):
		self.validate_universal_number()
		self.set_computed_fields()
		self.validate_surfaces()
	
	def validate_universal_number(self):
		if self.dentition_type == "Permanent":
			if not (1 <= self.universal_number <= 32):
				frappe.throw("Universal number for permanent teeth must be between 1-32")
		elif self.dentition_type == "Primary":
			# Primary teeth use letters A-T, but we store as numbers 101-120
			if not (101 <= self.universal_number <= 120):
				frappe.throw("Universal number for primary teeth must be between 101-120")
	
	def set_computed_fields(self):
		"""Set arch and position based on universal number"""
		if self.dentition_type == "Permanent":
			if 1 <= self.universal_number <= 16:
				self.arch = "Upper"
				if 1 <= self.universal_number <= 8:
					self.quadrant = "Upper Right"
					self.position_in_quadrant = 9 - self.universal_number
				else:
					self.quadrant = "Upper Left"
					self.position_in_quadrant = self.universal_number - 8
			else:
				self.arch = "Lower"
				if 17 <= self.universal_number <= 24:
					self.quadrant = "Lower Left"
					self.position_in_quadrant = self.universal_number - 16
				else:
					self.quadrant = "Lower Right"
					self.position_in_quadrant = 33 - self.universal_number
	
	def validate_surfaces(self):
		"""Ensure surfaces is valid JSON"""
		if self.surfaces:
			try:
				if isinstance(self.surfaces, str):
					json.loads(self.surfaces)
			except json.JSONDecodeError:
				frappe.throw("Surfaces must be valid JSON format")

	@staticmethod
	def create_standard_teeth():
		"""Create all 32 permanent teeth with standard data"""
		teeth_data = [
			# Upper Right Quadrant (1-8)
			{"num": 1, "name": "Upper Right Central Incisor", "type": "Incisor"},
			{"num": 2, "name": "Upper Right Lateral Incisor", "type": "Incisor"},
			{"num": 3, "name": "Upper Right Canine", "type": "Canine"},
			{"num": 4, "name": "Upper Right First Premolar", "type": "Premolar"},
			{"num": 5, "name": "Upper Right Second Premolar", "type": "Premolar"},
			{"num": 6, "name": "Upper Right First Molar", "type": "Molar"},
			{"num": 7, "name": "Upper Right Second Molar", "type": "Molar"},
			{"num": 8, "name": "Upper Right Third Molar (Wisdom)", "type": "Wisdom Tooth"},
			
			# Upper Left Quadrant (9-16)
			{"num": 9, "name": "Upper Left Central Incisor", "type": "Incisor"},
			{"num": 10, "name": "Upper Left Lateral Incisor", "type": "Incisor"},
			{"num": 11, "name": "Upper Left Canine", "type": "Canine"},
			{"num": 12, "name": "Upper Left First Premolar", "type": "Premolar"},
			{"num": 13, "name": "Upper Left Second Premolar", "type": "Premolar"},
			{"num": 14, "name": "Upper Left First Molar", "type": "Molar"},
			{"num": 15, "name": "Upper Left Second Molar", "type": "Molar"},
			{"num": 16, "name": "Upper Left Third Molar (Wisdom)", "type": "Wisdom Tooth"},
			
			# Lower Left Quadrant (17-24)
			{"num": 17, "name": "Lower Left Central Incisor", "type": "Incisor"},
			{"num": 18, "name": "Lower Left Lateral Incisor", "type": "Incisor"},
			{"num": 19, "name": "Lower Left Canine", "type": "Canine"},
			{"num": 20, "name": "Lower Left First Premolar", "type": "Premolar"},
			{"num": 21, "name": "Lower Left Second Premolar", "type": "Premolar"},
			{"num": 22, "name": "Lower Left First Molar", "type": "Molar"},
			{"num": 23, "name": "Lower Left Second Molar", "type": "Molar"},
			{"num": 24, "name": "Lower Left Third Molar (Wisdom)", "type": "Wisdom Tooth"},
			
			# Lower Right Quadrant (25-32)
			{"num": 25, "name": "Lower Right Central Incisor", "type": "Incisor"},
			{"num": 26, "name": "Lower Right Lateral Incisor", "type": "Incisor"},
			{"num": 27, "name": "Lower Right Canine", "type": "Canine"},
			{"num": 28, "name": "Lower Right First Premolar", "type": "Premolar"},
			{"num": 29, "name": "Lower Right Second Premolar", "type": "Premolar"},
			{"num": 30, "name": "Lower Right First Molar", "type": "Molar"},
			{"num": 31, "name": "Lower Right Second Molar", "type": "Molar"},
			{"num": 32, "name": "Lower Right Third Molar (Wisdom)", "type": "Wisdom Tooth"},
		]
		
		created_count = 0
		for tooth_data in teeth_data:
			if not frappe.db.exists("Tooth Master", str(tooth_data["num"])):
				# Set surfaces based on tooth type
				if tooth_data["type"] in ["Incisor", "Canine"]:
					surfaces = ["Incisal", "Mesial", "Distal", "Facial", "Lingual"]
				else:
					surfaces = ["Occlusal", "Mesial", "Distal", "Buccal", "Lingual"]
				
				tooth = frappe.get_doc({
					"doctype": "Tooth Master",
					"tooth_number": str(tooth_data["num"]),
					"universal_number": tooth_data["num"],
					"tooth_name": tooth_data["name"],
					"tooth_type": tooth_data["type"],
					"dentition_type": "Permanent",
					"surfaces": json.dumps(surfaces),
					"is_active": 1
				})
				tooth.insert()
				created_count += 1
		
		return f"Created {created_count} teeth" 