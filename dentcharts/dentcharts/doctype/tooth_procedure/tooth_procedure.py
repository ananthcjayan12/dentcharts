# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_days


class ToothProcedure(Document):
	def validate(self):
		self.validate_tooth_number()
		self.validate_procedure_code()
		self.set_default_values()
		self.calculate_patient_portion()
	
	def validate_tooth_number(self):
		"""Validate that the tooth number exists"""
		if not self.tooth_number:
			frappe.throw("Tooth number is required")
		
		# Skip validation for general procedures
		if self.tooth_number == "General":
			return
		
		if not frappe.db.exists("Tooth Master", self.tooth_number):
			frappe.throw(f"Invalid tooth number: {self.tooth_number}")
	
	def validate_procedure_code(self):
		"""Validate that the procedure code exists"""
		if not self.procedure_code:
			frappe.throw("Procedure code is required")
		
		if not frappe.db.exists("Dental Procedure Master", self.procedure_code):
			frappe.throw(f"Invalid procedure code: {self.procedure_code}")
	
	def set_default_values(self):
		"""Set default values from linked documents"""
		if not self.surface:
			self.surface = "Whole Tooth"
		
		if not self.status:
			self.status = "Planned"
		
		if not self.planned_by:
			self.planned_by = frappe.session.user
		
		if not self.planned_date:
			self.planned_date = today()
		
		# Set actual fee to standard fee if not set
		if self.procedure_code and not self.actual_fee:
			procedure_master = frappe.get_cached_doc("Dental Procedure Master", self.procedure_code)
			self.actual_fee = procedure_master.standard_fee
	
	def before_save(self):
		"""Set computed fields and validate status changes"""
		if self.procedure_code:
			procedure_master = frappe.get_cached_doc("Dental Procedure Master", self.procedure_code)
			self.follow_up_required = procedure_master.follow_up_required
			
			# Set follow-up date if required and completed
			if self.follow_up_required and self.status == "Completed" and not self.follow_up_date:
				follow_up_days = procedure_master.follow_up_days or 7
				self.follow_up_date = add_days(self.completed_date or today(), follow_up_days)
		
		# Validate status transitions
		self.validate_status_change()
	
	def validate_status_change(self):
		"""Validate status changes and set required fields"""
		if self.status == "Completed":
			if not self.completed_date:
				self.completed_date = today()
			if not self.performed_by:
				frappe.throw("Performed By is required when marking procedure as completed")
		
		elif self.status == "In Progress":
			if not self.performed_by:
				frappe.throw("Performed By is required when starting a procedure")
	
	def calculate_patient_portion(self):
		"""Calculate patient portion after insurance"""
		if self.actual_fee and self.insurance_covered:
			self.patient_portion = self.actual_fee - self.insurance_covered
		elif self.actual_fee:
			self.patient_portion = self.actual_fee
		else:
			self.patient_portion = 0
	
	def mark_completed(self, performed_by, completed_date=None, notes=None):
		"""Mark procedure as completed"""
		self.status = "Completed"
		self.performed_by = performed_by
		self.completed_date = completed_date or today()
		if notes:
			self.notes = notes
		
		# Set follow-up date if required
		if self.follow_up_required and self.procedure_code:
			procedure_master = frappe.get_cached_doc("Dental Procedure Master", self.procedure_code)
			follow_up_days = procedure_master.follow_up_days or 7
			self.follow_up_date = add_days(self.completed_date, follow_up_days)
	
	def cancel_procedure(self, reason=None):
		"""Cancel the procedure"""
		self.status = "Cancelled"
		if reason:
			self.notes = f"{self.notes}\nCancellation Reason: {reason}" if self.notes else f"Cancellation Reason: {reason}"
	
	def reschedule_procedure(self, new_date, reason=None):
		"""Reschedule the procedure"""
		self.planned_date = new_date
		self.status = "Planned"
		if reason:
			self.notes = f"{self.notes}\nRescheduled: {reason}" if self.notes else f"Rescheduled: {reason}" 