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
			# FDI notation: 11-18, 21-28, 31-38, 41-48
			valid_numbers = (
				list(range(11, 19)) +  # Upper Right: 11-18
				list(range(21, 29)) +  # Upper Left: 21-28
				list(range(31, 39)) +  # Lower Left: 31-38
				list(range(41, 49))    # Lower Right: 41-48
			)
			if self.universal_number not in valid_numbers:
				frappe.throw("Universal number must be valid FDI notation (11-18, 21-28, 31-38, 41-48)")
		elif self.dentition_type == "Primary":
			# Palmer notation for primary teeth uses letters A-E
			# Universal_number field not used for primary teeth
			if self.universal_number and self.universal_number != 0:
				frappe.throw("Primary teeth use Palmer notation with letters (A-E), not universal numbers")
	
	def set_computed_fields(self):
		"""Set arch and position based on numbering system"""
		if self.dentition_type == "Permanent" and self.universal_number:
			num = self.universal_number
			
			# FDI notation: First digit = quadrant, Second digit = position
			quadrant_digit = num // 10
			position_digit = num % 10
			
			if quadrant_digit == 1:  # Upper Right (11-18)
				self.arch = "Upper"
				self.quadrant = "Upper Right"
				self.position_in_quadrant = position_digit
			elif quadrant_digit == 2:  # Upper Left (21-28)
				self.arch = "Upper"
				self.quadrant = "Upper Left"
				self.position_in_quadrant = position_digit
			elif quadrant_digit == 3:  # Lower Left (31-38)
				self.arch = "Lower"
				self.quadrant = "Lower Left"
				self.position_in_quadrant = position_digit
			elif quadrant_digit == 4:  # Lower Right (41-48)
				self.arch = "Lower"
				self.quadrant = "Lower Right"
				self.position_in_quadrant = position_digit
		elif self.dentition_type == "Primary" and self.tooth_number:
			# Palmer notation for primary teeth uses letters with quadrant indicators
			# tooth_number format: "UR-A", "UL-B", "LL-C", "LR-D", etc.
			if "-" in self.tooth_number:
				quadrant_code, letter = self.tooth_number.split("-")
				
				if quadrant_code == "UR":  # Upper Right
					self.arch = "Upper"
					self.quadrant = "Upper Right"
				elif quadrant_code == "UL":  # Upper Left
					self.arch = "Upper"
					self.quadrant = "Upper Left"
				elif quadrant_code == "LL":  # Lower Left
					self.arch = "Lower"
					self.quadrant = "Lower Left"
				elif quadrant_code == "LR":  # Lower Right
					self.arch = "Lower"
					self.quadrant = "Lower Right"
				
				# Position based on letter (A=1, B=2, C=3, D=4, E=5)
				if letter in "ABCDE":
					self.position_in_quadrant = ord(letter) - ord('A') + 1
	
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
		"""Create all 32 permanent teeth with FDI numbering system"""
		teeth_data = [
			# Upper Right Quadrant (11-18)
			{"num": 11, "name": "Upper Right Central Incisor", "type": "Incisor"},
			{"num": 12, "name": "Upper Right Lateral Incisor", "type": "Incisor"},
			{"num": 13, "name": "Upper Right Canine", "type": "Canine"},
			{"num": 14, "name": "Upper Right First Premolar", "type": "Premolar"},
			{"num": 15, "name": "Upper Right Second Premolar", "type": "Premolar"},
			{"num": 16, "name": "Upper Right First Molar", "type": "Molar"},
			{"num": 17, "name": "Upper Right Second Molar", "type": "Molar"},
			{"num": 18, "name": "Upper Right Third Molar (Wisdom)", "type": "Wisdom Tooth"},
			
			# Upper Left Quadrant (21-28)
			{"num": 21, "name": "Upper Left Central Incisor", "type": "Incisor"},
			{"num": 22, "name": "Upper Left Lateral Incisor", "type": "Incisor"},
			{"num": 23, "name": "Upper Left Canine", "type": "Canine"},
			{"num": 24, "name": "Upper Left First Premolar", "type": "Premolar"},
			{"num": 25, "name": "Upper Left Second Premolar", "type": "Premolar"},
			{"num": 26, "name": "Upper Left First Molar", "type": "Molar"},
			{"num": 27, "name": "Upper Left Second Molar", "type": "Molar"},
			{"num": 28, "name": "Upper Left Third Molar (Wisdom)", "type": "Wisdom Tooth"},
			
			# Lower Left Quadrant (31-38)
			{"num": 31, "name": "Lower Left Central Incisor", "type": "Incisor"},
			{"num": 32, "name": "Lower Left Lateral Incisor", "type": "Incisor"},
			{"num": 33, "name": "Lower Left Canine", "type": "Canine"},
			{"num": 34, "name": "Lower Left First Premolar", "type": "Premolar"},
			{"num": 35, "name": "Lower Left Second Premolar", "type": "Premolar"},
			{"num": 36, "name": "Lower Left First Molar", "type": "Molar"},
			{"num": 37, "name": "Lower Left Second Molar", "type": "Molar"},
			{"num": 38, "name": "Lower Left Third Molar (Wisdom)", "type": "Wisdom Tooth"},
			
			# Lower Right Quadrant (41-48)
			{"num": 41, "name": "Lower Right Central Incisor", "type": "Incisor"},
			{"num": 42, "name": "Lower Right Lateral Incisor", "type": "Incisor"},
			{"num": 43, "name": "Lower Right Canine", "type": "Canine"},
			{"num": 44, "name": "Lower Right First Premolar", "type": "Premolar"},
			{"num": 45, "name": "Lower Right Second Premolar", "type": "Premolar"},
			{"num": 46, "name": "Lower Right First Molar", "type": "Molar"},
			{"num": 47, "name": "Lower Right Second Molar", "type": "Molar"},
			{"num": 48, "name": "Lower Right Third Molar (Wisdom)", "type": "Wisdom Tooth"},
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
		
		return f"Created {created_count} permanent teeth"

	@staticmethod
	def create_standard_primary_teeth():
		"""Create all 20 primary teeth with Palmer notation system"""
		primary_teeth_data = [
			# Upper Right Quadrant (E, D, C, B, A)
			{"code": "UR-E", "name": "Upper Right Second Molar (Primary)", "type": "Molar"},
			{"code": "UR-D", "name": "Upper Right First Molar (Primary)", "type": "Molar"},
			{"code": "UR-C", "name": "Upper Right Canine (Primary)", "type": "Canine"},
			{"code": "UR-B", "name": "Upper Right Lateral Incisor (Primary)", "type": "Incisor"},
			{"code": "UR-A", "name": "Upper Right Central Incisor (Primary)", "type": "Incisor"},
			
			# Upper Left Quadrant (A, B, C, D, E)
			{"code": "UL-A", "name": "Upper Left Central Incisor (Primary)", "type": "Incisor"},
			{"code": "UL-B", "name": "Upper Left Lateral Incisor (Primary)", "type": "Incisor"},
			{"code": "UL-C", "name": "Upper Left Canine (Primary)", "type": "Canine"},
			{"code": "UL-D", "name": "Upper Left First Molar (Primary)", "type": "Molar"},
			{"code": "UL-E", "name": "Upper Left Second Molar (Primary)", "type": "Molar"},
			
			# Lower Left Quadrant (A, B, C, D, E)
			{"code": "LL-A", "name": "Lower Left Central Incisor (Primary)", "type": "Incisor"},
			{"code": "LL-B", "name": "Lower Left Lateral Incisor (Primary)", "type": "Incisor"},
			{"code": "LL-C", "name": "Lower Left Canine (Primary)", "type": "Canine"},
			{"code": "LL-D", "name": "Lower Left First Molar (Primary)", "type": "Molar"},
			{"code": "LL-E", "name": "Lower Left Second Molar (Primary)", "type": "Molar"},
			
			# Lower Right Quadrant (E, D, C, B, A)
			{"code": "LR-E", "name": "Lower Right Second Molar (Primary)", "type": "Molar"},
			{"code": "LR-D", "name": "Lower Right First Molar (Primary)", "type": "Molar"},
			{"code": "LR-C", "name": "Lower Right Canine (Primary)", "type": "Canine"},
			{"code": "LR-B", "name": "Lower Right Lateral Incisor (Primary)", "type": "Incisor"},
			{"code": "LR-A", "name": "Lower Right Central Incisor (Primary)", "type": "Incisor"},
		]
		
		created_count = 0
		for tooth_data in primary_teeth_data:
			if not frappe.db.exists("Tooth Master", tooth_data["code"]):
				# Primary teeth have different surfaces (no premolars)
				if tooth_data["type"] in ["Incisor", "Canine"]:
					surfaces = ["Incisal", "Mesial", "Distal", "Facial", "Lingual"]
				else:  # Molars
					surfaces = ["Occlusal", "Mesial", "Distal", "Buccal", "Lingual"]
				
				tooth = frappe.get_doc({
					"doctype": "Tooth Master",
					"tooth_number": tooth_data["code"],
					"universal_number": 0,  # Not used for primary teeth
					"tooth_name": tooth_data["name"],
					"tooth_type": tooth_data["type"],
					"dentition_type": "Primary",
					"surfaces": json.dumps(surfaces),
					"is_active": 1
				})
				tooth.insert()
				created_count += 1
		
		return f"Created {created_count} primary teeth" 