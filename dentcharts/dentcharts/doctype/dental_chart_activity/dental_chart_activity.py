# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalChartActivity(Document):
	def validate(self):
		"""Validate activity log entry"""
		if not self.activity_description:
			self.generate_activity_description()
	
	def generate_activity_description(self):
		"""Generate a human-readable activity description"""
		descriptions = {
			"Condition Added": f"Added condition to tooth {self.tooth_number}",
			"Condition Removed": f"Removed condition from tooth {self.tooth_number}",
			"Condition Modified": f"Modified condition on tooth {self.tooth_number}",
			"Procedure Added": f"Added procedure to tooth {self.tooth_number}",
			"Procedure Removed": f"Removed procedure from tooth {self.tooth_number}",
			"Procedure Status Changed": f"Changed procedure status on tooth {self.tooth_number}",
			"Procedure Cost Modified": f"Modified procedure cost for tooth {self.tooth_number}",
			"Visit Recorded": "Recorded new patient visit",
			"Chart Updated": "Updated dental chart",
			"Treatment Completed": f"Completed treatment on tooth {self.tooth_number}"
		}
		
		self.activity_description = descriptions.get(self.activity_type, f"{self.activity_type} on tooth {self.tooth_number}")
		
		# Add more specific details if available
		if self.condition_code:
			condition_name = frappe.db.get_value("Dental Condition Master", self.condition_code, "condition_name")
			self.activity_description += f" ({condition_name})"
		
		if self.procedure_code:
			procedure_name = frappe.db.get_value("Dental Procedure Master", self.procedure_code, "procedure_name")
			self.activity_description += f" ({procedure_name})"
		
		if self.cost_impact:
			self.activity_description += f" - Cost Impact: {frappe.format_value(self.cost_impact, {'fieldtype': 'Currency'})}" 