# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, today


class DentalChart(Document):
	def validate(self):
		self.validate_patient()
		self.validate_dentist()
		self.set_default_values()
		self.calculate_summary_fields()
	
	def before_save(self):
		self.update_timestamps()
		self.validate_chart_consistency()
	
	def validate_patient(self):
		"""Validate that the patient exists and is active"""
		if not self.patient:
			frappe.throw("Patient is required")
		
		if not frappe.db.exists("Patient", self.patient):
			frappe.throw("Selected patient does not exist")
	
	def validate_dentist(self):
		"""Validate that the dentist exists and is a healthcare practitioner"""
		if not self.dentist:
			frappe.throw("Dentist is required")
		
		if not frappe.db.exists("Healthcare Practitioner", self.dentist):
			frappe.throw("Selected dentist does not exist")
	
	def set_default_values(self):
		"""Set default values for various fields"""
		if not self.chart_date:
			self.chart_date = today()
		
		if not self.status:
			self.status = "Draft"
		
		if not self.chart_type:
			self.chart_type = "Comprehensive"
		
		if not self.dentition_type:
			self.dentition_type = "Permanent"
		
		# Set created by and created on for new documents
		if self.is_new():
			self.created_by = frappe.session.user
			self.created_on = now()
	
	def update_timestamps(self):
		"""Update last modified timestamps"""
		self.last_modified_by = frappe.session.user
		self.last_modified_on = now()
	
	def calculate_summary_fields(self):
		"""Calculate summary fields based on tooth conditions and procedures"""
		# Count total conditions
		self.total_conditions = len(self.tooth_conditions or [])
		
		# Count total procedures
		self.total_procedures = len(self.tooth_procedures or [])
		
		# Count emergency conditions
		emergency_count = 0
		for condition in (self.tooth_conditions or []):
			if condition.condition_code:
				condition_master = frappe.get_cached_doc("Dental Condition Master", condition.condition_code)
				if condition_master.is_emergency:
					emergency_count += 1
		self.emergency_conditions = emergency_count
		
		# Calculate estimated cost using actual fees (if set) or standard fees as fallback
		total_cost = 0
		for procedure in (self.tooth_procedures or []):
			if procedure.procedure_code:
				# Use actual_fee if set by doctor, otherwise fall back to standard_fee
				if hasattr(procedure, 'actual_fee') and procedure.actual_fee:
					total_cost += procedure.actual_fee
				else:
					# Fallback to standard fee from procedure master
					procedure_master = frappe.get_cached_doc("Dental Procedure Master", procedure.procedure_code)
					total_cost += procedure_master.standard_fee or 0
		self.estimated_cost = total_cost
		
		# Set treatment required flag
		self.treatment_required = 1 if (self.total_conditions > 0 or self.total_procedures > 0) else 0
	
	def validate_chart_consistency(self):
		"""Validate consistency between conditions and procedures"""
		# Check for duplicate tooth conditions
		tooth_condition_map = {}
		for condition in (self.tooth_conditions or []):
			key = f"{condition.tooth_number}_{condition.surface}_{condition.condition_code}"
			if key in tooth_condition_map:
				frappe.throw(f"Duplicate condition found for tooth {condition.tooth_number} surface {condition.surface}")
			tooth_condition_map[key] = True
		
		# Check for duplicate tooth procedures
		tooth_procedure_map = {}
		for procedure in (self.tooth_procedures or []):
			key = f"{procedure.tooth_number}_{procedure.surface}_{procedure.procedure_code}"
			if key in tooth_procedure_map:
				frappe.throw(f"Duplicate procedure found for tooth {procedure.tooth_number} surface {procedure.surface}")
			tooth_procedure_map[key] = True
	
	def add_tooth_condition(self, tooth_number, condition_code, surface=None, notes=None):
		"""Add a new tooth condition to the chart"""
		# Validate inputs
		if not frappe.db.exists("Tooth Master", tooth_number):
			frappe.throw(f"Invalid tooth number: {tooth_number}")
		
		if not frappe.db.exists("Dental Condition Master", condition_code):
			frappe.throw(f"Invalid condition code: {condition_code}")
		
		# Create new condition entry
		condition_entry = {
			"tooth_number": tooth_number,
			"condition_code": condition_code,
			"surface": surface or "Whole Tooth",
			"notes": notes or "",
			"date_identified": today(),
			"identified_by": frappe.session.user
		}
		
		# Add to tooth_conditions table
		self.append("tooth_conditions", condition_entry)
		
		# Recalculate summary fields
		self.calculate_summary_fields()
	
	def add_tooth_procedure(self, tooth_number, procedure_code, surface=None, notes=None, status="Planned"):
		"""Add a new tooth procedure to the chart"""
		# Validate inputs
		if not frappe.db.exists("Tooth Master", tooth_number):
			frappe.throw(f"Invalid tooth number: {tooth_number}")
		
		if not frappe.db.exists("Dental Procedure Master", procedure_code):
			frappe.throw(f"Invalid procedure code: {procedure_code}")
		
		# Create new procedure entry
		procedure_entry = {
			"tooth_number": tooth_number,
			"procedure_code": procedure_code,
			"surface": surface or "Whole Tooth",
			"notes": notes or "",
			"status": status,
			"planned_date": today(),
			"planned_by": frappe.session.user
		}
		
		# Add to tooth_procedures table
		self.append("tooth_procedures", procedure_entry)
		
		# Recalculate summary fields
		self.calculate_summary_fields()
	
	def get_tooth_chart_data(self):
		"""Get structured data for dental chart visualization"""
		chart_data = {
			"patient": self.patient_name,
			"chart_date": self.chart_date,
			"dentist": self.dentist_name,
			"dentition_type": self.dentition_type or "Permanent",
			"teeth": {}
		}
		
		# Initialize teeth based on dentition type
		if self.dentition_type in ["Permanent", "Mixed"]:
			# Add permanent teeth (32 teeth - FDI numbering)
			for i in range(11, 49):  # FDI numbering
				if i <= 18 or i >= 21 and i <= 28 or i >= 31 and i <= 38 or i >= 41 and i <= 48:
					chart_data["teeth"][str(i)] = {
						"conditions": [],
						"procedures": [],
						"status": "healthy",
						"type": "permanent"
					}
		
		if self.dentition_type in ["Primary", "Mixed"]:
			# Add primary teeth (20 teeth - Palmer notation)
			primary_teeth_codes = [
				# Upper Right (E, D, C, B, A)
				"UR-E", "UR-D", "UR-C", "UR-B", "UR-A",
				# Upper Left (A, B, C, D, E)
				"UL-A", "UL-B", "UL-C", "UL-D", "UL-E",
				# Lower Left (A, B, C, D, E)
				"LL-A", "LL-B", "LL-C", "LL-D", "LL-E",
				# Lower Right (E, D, C, B, A)
				"LR-E", "LR-D", "LR-C", "LR-B", "LR-A"
			]
			
			for tooth_code in primary_teeth_codes:
				chart_data["teeth"][tooth_code] = {
					"conditions": [],
					"procedures": [],
					"status": "healthy",
					"type": "primary"
				}
		
		# Add conditions
		for condition in (self.tooth_conditions or []):
			tooth_key = str(condition.tooth_number)
			if tooth_key in chart_data["teeth"]:
				chart_data["teeth"][tooth_key]["conditions"].append({
					"code": condition.condition_code,
					"surface": condition.surface,
					"notes": condition.notes,
					"date": condition.date_identified
				})
				chart_data["teeth"][tooth_key]["status"] = "has_condition"
		
		# Add procedures
		for procedure in (self.tooth_procedures or []):
			tooth_key = str(procedure.tooth_number)
			if tooth_key in chart_data["teeth"]:
				chart_data["teeth"][tooth_key]["procedures"].append({
					"code": procedure.procedure_code,
					"surface": procedure.surface,
					"status": procedure.status,
					"notes": procedure.notes,
					"date": procedure.planned_date
				})
				if procedure.status == "Completed":
					chart_data["teeth"][tooth_key]["status"] = "treated"
				elif procedure.status == "In Progress":
					chart_data["teeth"][tooth_key]["status"] = "in_treatment"
		
		return chart_data
	
	def get_emergency_conditions(self):
		"""Get list of emergency conditions that need immediate attention"""
		emergency_conditions = []
		
		for condition in (self.tooth_conditions or []):
			if condition.condition_code:
				condition_master = frappe.get_cached_doc("Dental Condition Master", condition.condition_code)
				if condition_master.is_emergency:
					emergency_conditions.append({
						"tooth_number": condition.tooth_number,
						"condition": condition_master.condition_name,
						"surface": condition.surface,
						"notes": condition.notes,
						"severity": condition_master.severity
					})
		
		return emergency_conditions
	
	def get_treatment_plan_summary(self):
		"""Get summary of planned treatments"""
		planned_procedures = []
		total_cost = 0
		
		for procedure in (self.tooth_procedures or []):
			if procedure.status in ["Planned", "In Progress"]:
				procedure_master = frappe.get_cached_doc("Dental Procedure Master", procedure.procedure_code)
				
				# Use actual_fee if set by doctor, otherwise use standard_fee
				procedure_cost = 0
				if hasattr(procedure, 'actual_fee') and procedure.actual_fee:
					procedure_cost = procedure.actual_fee
				else:
					procedure_cost = procedure_master.standard_fee or 0
				
				planned_procedures.append({
					"tooth_number": procedure.tooth_number,
					"procedure": procedure_master.procedure_name,
					"surface": procedure.surface,
					"cost": procedure_cost,
					"duration": procedure_master.duration_minutes or 0,
					"status": procedure.status
				})
				total_cost += procedure_cost
		
		return {
			"procedures": planned_procedures,
			"total_cost": total_cost,
			"total_procedures": len(planned_procedures)
		}
	
	def get_available_teeth(self):
		"""Get list of available teeth based on dentition type"""
		available_teeth = []
		
		if self.dentition_type in ["Permanent", "Mixed"]:
			# Add permanent teeth
			for i in range(11, 49):
				if i <= 18 or i >= 21 and i <= 28 or i >= 31 and i <= 38 or i >= 41 and i <= 48:
					available_teeth.append(str(i))
		
		if self.dentition_type in ["Primary", "Mixed"]:
			# Add primary teeth
			primary_teeth = [
				"UR-E", "UR-D", "UR-C", "UR-B", "UR-A",
				"UL-A", "UL-B", "UL-C", "UL-D", "UL-E",
				"LL-A", "LL-B", "LL-C", "LL-D", "LL-E",
				"LR-E", "LR-D", "LR-C", "LR-B", "LR-A"
			]
			available_teeth.extend(primary_teeth)
		
		return available_teeth
	
	def get_tooth_display_name(self, tooth_number):
		"""Get display name for a tooth"""
		try:
			tooth_master = frappe.get_cached_doc("Tooth Master", tooth_number)
			return tooth_master.tooth_name
		except:
			# Fallback for tooth numbers not in master
			if tooth_number.startswith(("UR-", "UL-", "LL-", "LR-")):
				# Primary tooth
				quadrant_map = {
					"UR": "Upper Right",
					"UL": "Upper Left", 
					"LL": "Lower Left",
					"LR": "Lower Right"
				}
				letter_map = {
					"A": "Central Incisor",
					"B": "Lateral Incisor", 
					"C": "Canine",
					"D": "First Molar",
					"E": "Second Molar"
				}
				parts = tooth_number.split("-")
				if len(parts) == 2:
					quadrant = quadrant_map.get(parts[0], parts[0])
					letter = letter_map.get(parts[1], parts[1])
					return f"{quadrant} {letter} (Primary)"
			return tooth_number

	@staticmethod
	def create_chart_for_patient(patient, dentist, chart_type="Comprehensive", dentition_type="Permanent"):
		"""Create a new dental chart for a patient"""
		chart = frappe.get_doc({
			"doctype": "Dental Chart",
			"patient": patient,
			"dentist": dentist,
			"chart_type": chart_type,
			"dentition_type": dentition_type,
			"chart_date": today(),
			"status": "Draft"
		})
		chart.insert()
		return chart


@frappe.whitelist()
def get_available_teeth_for_chart(dentition_type):
	"""Get list of available teeth based on dentition type"""
	available_teeth = []
	
	if dentition_type in ["Permanent", "Mixed"]:
		# Add permanent teeth
		for i in range(11, 49):
			if i <= 18 or i >= 21 and i <= 28 or i >= 31 and i <= 38 or i >= 41 and i <= 48:
				available_teeth.append(str(i))
	
	if dentition_type in ["Primary", "Mixed"]:
		# Add primary teeth
		primary_teeth = [
			"UR-E", "UR-D", "UR-C", "UR-B", "UR-A",
			"UL-A", "UL-B", "UL-C", "UL-D", "UL-E",
			"LL-A", "LL-B", "LL-C", "LL-D", "LL-E",
			"LR-E", "LR-D", "LR-C", "LR-B", "LR-A"
		]
		available_teeth.extend(primary_teeth)
	
	return sorted(available_teeth)


@frappe.whitelist()
def get_chart_data(chart_name):
	"""Get chart data for visualization"""
	chart = frappe.get_doc("Dental Chart", chart_name)
	return chart.get_tooth_chart_data() 