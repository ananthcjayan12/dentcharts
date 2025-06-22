# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ToothCondition(Document):
	def validate(self):
		self.validate_tooth_number()
		self.validate_condition_code()
		self.set_default_values()
	
	def validate_tooth_number(self):
		"""Validate that the tooth number exists"""
		if not self.tooth_number:
			frappe.throw("Tooth number is required")
		
		if not frappe.db.exists("Tooth Master", self.tooth_number):
			frappe.throw(f"Invalid tooth number: {self.tooth_number}")
	
	def validate_condition_code(self):
		"""Validate that the condition code exists"""
		if not self.condition_code:
			frappe.throw("Condition code is required")
		
		if not frappe.db.exists("Dental Condition Master", self.condition_code):
			frappe.throw(f"Invalid condition code: {self.condition_code}")
	
	def set_default_values(self):
		"""Set default values from linked documents"""
		if not self.surface:
			self.surface = "Whole Tooth"
		
		if not self.identified_by:
			self.identified_by = frappe.session.user
		
		if not self.date_identified:
			self.date_identified = frappe.utils.today()
	
	def before_save(self):
		"""Set computed fields before saving"""
		if self.condition_code:
			condition_master = frappe.get_cached_doc("Dental Condition Master", self.condition_code)
			self.requires_treatment = condition_master.requires_treatment
			self.is_emergency = condition_master.is_emergency 