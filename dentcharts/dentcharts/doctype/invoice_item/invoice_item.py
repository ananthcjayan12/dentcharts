import frappe
from frappe.model.document import Document
from frappe.utils import flt

class InvoiceItem(Document):
	def validate(self):
		"""Validate invoice item data"""
		self.validate_item_details()
		self.calculate_total_amount()
		self.set_default_values()
	
	def validate_item_details(self):
		"""Validate item details"""
		if not self.procedure_code:
			frappe.throw(f"Procedure code is required for row {self.idx}")
		
		if not self.amount or self.amount <= 0:
			frappe.throw(f"Amount must be greater than 0 for row {self.idx}")
		
		if not self.quantity or self.quantity <= 0:
			frappe.throw(f"Quantity must be greater than 0 for row {self.idx}")
		
		# Validate tooth and surface combination
		if self.tooth_number and self.surface:
			self.validate_tooth_surface_combination()
	
	def validate_tooth_surface_combination(self):
		"""Validate that the surface is appropriate for the tooth"""
		if not self.tooth_number:
			return
		
		try:
			tooth = frappe.get_doc("Tooth Master", self.tooth_number)
			
			# Basic validation - you can enhance this based on dental rules
			if self.surface == "Incisal" and tooth.tooth_type not in ["Incisor", "Canine"]:
				frappe.throw(f"Incisal surface is not applicable for {tooth.tooth_type} teeth")
			
			if self.surface == "Occlusal" and tooth.tooth_type not in ["Premolar", "Molar"]:
				frappe.msgprint(f"Warning: Occlusal surface is typically for Premolar/Molar teeth, not {tooth.tooth_type}")
		
		except frappe.DoesNotExistError:
			pass  # Tooth master doesn't exist, skip validation
	
	def calculate_total_amount(self):
		"""Calculate total amount based on quantity and unit amount"""
		self.total_amount = flt(self.quantity) * flt(self.amount)
	
	def set_default_values(self):
		"""Set default values for new items"""
		# Auto-populate procedure details if missing
		if self.procedure_code and not self.description:
			try:
				procedure = frappe.get_doc("Dental Procedure Master", self.procedure_code)
				self.description = procedure.procedure_name
				
				# Auto-populate amount if not set
				if not self.amount:
					self.amount = procedure.standard_fee
			except frappe.DoesNotExistError:
				pass
		
		# Set default quantity if not set
		if not self.quantity:
			self.quantity = 1 