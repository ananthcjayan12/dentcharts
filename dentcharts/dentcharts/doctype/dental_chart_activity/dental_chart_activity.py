# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalChartActivity(Document):
	def validate(self):
		"""Validate activity log entry"""
		# Description is now generated in the parent document before adding to table
		pass 