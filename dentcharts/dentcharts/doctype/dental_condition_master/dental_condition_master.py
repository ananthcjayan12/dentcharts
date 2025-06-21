# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalConditionMaster(Document):
	def validate(self):
		self.validate_color_code()
		self.set_default_values()
	
	def validate_color_code(self):
		"""Validate hex color code format"""
		if self.color_code:
			if not self.color_code.startswith('#') or len(self.color_code) != 7:
				frappe.throw("Color code must be in hex format (#RRGGBB)")
	
	def set_default_values(self):
		"""Set default values based on category and severity"""
		if not self.color_code:
			self.color_code = self.get_default_color()
		
		if not self.symbol:
			self.symbol = self.get_default_symbol()
	
	def get_default_color(self):
		"""Get default color based on severity"""
		color_map = {
			"Low": "#28a745",      # Green
			"Medium": "#ffc107",   # Yellow
			"High": "#fd7e14",     # Orange
			"Critical": "#dc3545"  # Red
		}
		return color_map.get(self.severity, "#6c757d")  # Default gray
	
	def get_default_symbol(self):
		"""Get default symbol based on category"""
		symbol_map = {
			"Caries": "C",
			"Periodontal": "P",
			"Endodontic": "E",
			"Prosthodontic": "Pr",
			"Orthodontic": "O",
			"Oral Surgery": "S",
			"Cosmetic": "Co",
			"Prevention": "Pv",
			"Emergency": "!",
			"Other": "?"
		}
		return symbol_map.get(self.category, "?")

	@staticmethod
	def create_standard_conditions():
		"""Create all standard dental conditions"""
		conditions_data = [
			# Caries conditions
			{
				"code": "CAR001", "name": "Small Cavity", "category": "Caries", 
				"severity": "Low", "symbol": "C", "color": "#ffc107",
				"description": "Small carious lesion requiring restoration"
			},
			{
				"code": "CAR002", "name": "Large Cavity", "category": "Caries", 
				"severity": "Medium", "symbol": "C+", "color": "#fd7e14",
				"description": "Large carious lesion requiring extensive restoration"
			},
			{
				"code": "CAR003", "name": "Deep Cavity", "category": "Caries", 
				"severity": "High", "symbol": "C++", "color": "#dc3545",
				"description": "Deep carious lesion close to pulp"
			},
			
			# Restorative conditions
			{
				"code": "RES001", "name": "Amalgam Filling", "category": "Prosthodontic", 
				"severity": "Low", "symbol": "AM", "color": "#6c757d",
				"description": "Existing amalgam restoration", "requires_treatment": 0
			},
			{
				"code": "RES002", "name": "Composite Filling", "category": "Prosthodontic", 
				"severity": "Low", "symbol": "CO", "color": "#28a745",
				"description": "Existing composite restoration", "requires_treatment": 0
			},
			{
				"code": "RES003", "name": "Defective Filling", "category": "Prosthodontic", 
				"severity": "Medium", "symbol": "DF", "color": "#fd7e14",
				"description": "Defective restoration requiring replacement"
			},
			
			# Crown and Bridge
			{
				"code": "PRO001", "name": "Crown", "category": "Prosthodontic", 
				"severity": "Low", "symbol": "CR", "color": "#17a2b8",
				"description": "Existing crown restoration", "requires_treatment": 0
			},
			{
				"code": "PRO002", "name": "Bridge Abutment", "category": "Prosthodontic", 
				"severity": "Low", "symbol": "BA", "color": "#17a2b8",
				"description": "Bridge abutment tooth", "requires_treatment": 0
			},
			{
				"code": "PRO003", "name": "Bridge Pontic", "category": "Prosthodontic", 
				"severity": "Low", "symbol": "BP", "color": "#17a2b8",
				"description": "Bridge pontic (missing tooth replacement)", "requires_treatment": 0
			},
			
			# Periodontal conditions
			{
				"code": "PER001", "name": "Gingivitis", "category": "Periodontal", 
				"severity": "Low", "symbol": "G", "color": "#ffc107",
				"description": "Gum inflammation"
			},
			{
				"code": "PER002", "name": "Periodontitis", "category": "Periodontal", 
				"severity": "Medium", "symbol": "P", "color": "#fd7e14",
				"description": "Periodontal disease with bone loss"
			},
			{
				"code": "PER003", "name": "Severe Periodontitis", "category": "Periodontal", 
				"severity": "High", "symbol": "P+", "color": "#dc3545",
				"description": "Advanced periodontal disease"
			},
			
			# Endodontic conditions
			{
				"code": "END001", "name": "Root Canal Treatment", "category": "Endodontic", 
				"severity": "Medium", "symbol": "RCT", "color": "#6f42c1",
				"description": "Root canal therapy needed"
			},
			{
				"code": "END002", "name": "Completed RCT", "category": "Endodontic", 
				"severity": "Low", "symbol": "✓RCT", "color": "#28a745",
				"description": "Completed root canal treatment", "requires_treatment": 0
			},
			{
				"code": "END003", "name": "Apical Abscess", "category": "Endodontic", 
				"severity": "Critical", "symbol": "ABS", "color": "#dc3545",
				"description": "Apical abscess requiring immediate treatment", "is_emergency": 1
			},
			
			# Extraction conditions
			{
				"code": "EXT001", "name": "Extraction Needed", "category": "Oral Surgery", 
				"severity": "High", "symbol": "EXT", "color": "#dc3545",
				"description": "Tooth extraction required"
			},
			{
				"code": "EXT002", "name": "Missing Tooth", "category": "Oral Surgery", 
				"severity": "Medium", "symbol": "X", "color": "#6c757d",
				"description": "Missing tooth", "requires_treatment": 0, "is_visible": 0
			},
			{
				"code": "EXT003", "name": "Impacted Tooth", "category": "Oral Surgery", 
				"severity": "Medium", "symbol": "IMP", "color": "#fd7e14",
				"description": "Impacted tooth"
			},
			
			# Preventive conditions
			{
				"code": "PRV001", "name": "Healthy Tooth", "category": "Prevention", 
				"severity": "Low", "symbol": "✓", "color": "#28a745",
				"description": "Healthy tooth with no issues", "requires_treatment": 0
			},
			{
				"code": "PRV002", "name": "Plaque Build-up", "category": "Prevention", 
				"severity": "Low", "symbol": "PL", "color": "#ffc107",
				"description": "Plaque accumulation requiring cleaning"
			},
			{
				"code": "PRV003", "name": "Calculus/Tartar", "category": "Prevention", 
				"severity": "Medium", "symbol": "CA", "color": "#fd7e14",
				"description": "Calculus deposits requiring scaling"
			}
		]
		
		created_count = 0
		for condition_data in conditions_data:
			if not frappe.db.exists("Dental Condition Master", condition_data["code"]):
				condition = frappe.get_doc({
					"doctype": "Dental Condition Master",
					"condition_code": condition_data["code"],
					"condition_name": condition_data["name"],
					"category": condition_data["category"],
					"severity": condition_data["severity"],
					"symbol": condition_data["symbol"],
					"color_code": condition_data["color"],
					"description": condition_data["description"],
					"requires_treatment": condition_data.get("requires_treatment", 1),
					"is_emergency": condition_data.get("is_emergency", 0),
					"is_visible": condition_data.get("is_visible", 1),
					"affects_function": condition_data.get("affects_function", 1),
					"is_active": 1
				})
				condition.insert()
				created_count += 1
		
		return f"Created {created_count} dental conditions" 