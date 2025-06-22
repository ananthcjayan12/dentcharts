# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AppointmentProcedure(Document):
	def validate(self):
		"""Validate appointment procedure data"""
		self.set_procedure_details()
		self.validate_tooth_surface_combination()
	
	def set_procedure_details(self):
		"""Auto-populate procedure details from master data"""
		if self.procedure_code:
			procedure_master = frappe.get_doc("Dental Procedure Master", self.procedure_code)
			
			# Set duration and cost from master data
			self.estimated_duration = procedure_master.duration_minutes
			self.estimated_cost = procedure_master.standard_fee
	
	def validate_tooth_surface_combination(self):
		"""Validate tooth and surface combination"""
		if self.tooth_number and self.surface:
			# Validate that the surface is appropriate for the tooth
			if self.surface == "Incisal":
				# Incisal surface only exists on front teeth (incisors and canines)
				tooth_doc = frappe.get_doc("Tooth Master", self.tooth_number)
				if tooth_doc.tooth_type not in ["Incisor", "Canine"]:
					frappe.throw(f"Incisal surface is not valid for {tooth_doc.tooth_type} teeth")
			
			elif self.surface == "Occlusal":
				# Occlusal surface only exists on back teeth (premolars and molars)
				tooth_doc = frappe.get_doc("Tooth Master", self.tooth_number)
				if tooth_doc.tooth_type not in ["Premolar", "Molar", "Wisdom"]:
					frappe.throw(f"Occlusal surface is not valid for {tooth_doc.tooth_type} teeth") 