# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalClinic(Document):
	def validate(self):
		self.validate_email()
		self.validate_phone()
	
	def validate_email(self):
		if self.email and "@" not in self.email:
			frappe.throw("Please enter a valid email address")
	
	def validate_phone(self):
		if self.phone and len(self.phone) < 10:
			frappe.throw("Please enter a valid phone number") 