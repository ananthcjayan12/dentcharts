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
		self.track_changes()
	
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
		general_procedures = []
		for procedure in (self.tooth_procedures or []):
			tooth_key = str(procedure.tooth_number)
			
			# Handle general procedures separately
			if tooth_key == "General":
				general_procedures.append({
					"code": procedure.procedure_code,
					"surface": procedure.surface,
					"status": procedure.status,
					"notes": procedure.notes,
					"date": procedure.planned_date,
					"actual_fee": procedure.actual_fee,
					"standard_fee": procedure.standard_fee
				})
			elif tooth_key in chart_data["teeth"]:
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
		
		# Add general procedures to chart data
		chart_data["general_procedures"] = general_procedures
		
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
	
	def track_changes(self):
		"""Track changes made to conditions and procedures"""
		if self.is_new():
			return
		
		try:
			# Get the current document from database to compare
			old_doc = frappe.get_doc("Dental Chart", self.name)
			
			# Track condition changes
			self.track_condition_changes(old_doc)
			
			# Track procedure changes
			self.track_procedure_changes(old_doc)
		except Exception as e:
			# If we can't track changes (e.g., during first save), just continue
			frappe.log_error(f"Error tracking changes for {self.name}: {str(e)}")
			pass
	
	def track_condition_changes(self, old_doc):
		"""Track changes in tooth conditions"""
		old_conditions = {f"{c.tooth_number}_{c.condition_code}_{c.surface}": c for c in (old_doc.tooth_conditions or [])}
		new_conditions = {f"{c.tooth_number}_{c.condition_code}_{c.surface}": c for c in (self.tooth_conditions or [])}
		
		# Find added conditions
		for key, condition in new_conditions.items():
			if key not in old_conditions:
				self.log_activity(
					activity_type="Condition Added",
					tooth_number=condition.tooth_number,
					condition_code=condition.condition_code,
					new_value=f"{condition.condition_code} on {condition.surface}",
					additional_notes=condition.notes or ""
				)
		
		# Find removed conditions
		for key, condition in old_conditions.items():
			if key not in new_conditions:
				self.log_activity(
					activity_type="Condition Removed",
					tooth_number=condition.tooth_number,
					condition_code=condition.condition_code,
					old_value=f"{condition.condition_code} on {condition.surface}",
					additional_notes=f"Removed: {condition.notes or ''}"
				)
	
	def track_procedure_changes(self, old_doc):
		"""Track changes in tooth procedures with grouping for multi-tooth procedures"""
		old_procedures = {f"{p.tooth_number}_{p.procedure_code}_{p.surface}": p for p in (old_doc.tooth_procedures or [])}
		new_procedures = {f"{p.tooth_number}_{p.procedure_code}_{p.surface}": p for p in (self.tooth_procedures or [])}
		
		# Group new procedures by procedure_code and surface for batch tracking
		new_procedure_groups = {}
		for key, procedure in new_procedures.items():
			if key not in old_procedures:
				group_key = f"{procedure.procedure_code}_{procedure.surface}_{procedure.status}"
				if group_key not in new_procedure_groups:
					new_procedure_groups[group_key] = {
						'procedure_code': procedure.procedure_code,
						'surface': procedure.surface,
						'status': procedure.status,
						'teeth': [],
						'total_cost': 0,
						'notes': procedure.notes or ""
					}
				new_procedure_groups[group_key]['teeth'].append(procedure.tooth_number)
				cost = procedure.actual_fee or procedure.standard_fee or 0
				new_procedure_groups[group_key]['total_cost'] += cost
		
		# Log grouped activities for multi-tooth procedures
		for group_key, group_data in new_procedure_groups.items():
			if len(group_data['teeth']) > 1:
				# Multi-tooth procedure - create single grouped activity
				teeth_list = ', '.join(sorted(group_data['teeth']))
				description = f"Added procedure to multiple teeth ({len(group_data['teeth'])} teeth): {teeth_list}"
				
				self.log_activity(
					activity_type="Procedure Added",
					tooth_number=f"Multiple ({len(group_data['teeth'])})",
					procedure_code=group_data['procedure_code'],
					new_value=f"{group_data['procedure_code']} ({group_data['status']}) on {group_data['surface']} - {teeth_list}",
					cost_impact=group_data['total_cost'],
					additional_notes=f"Multi-tooth procedure: {group_data['notes']}"
				)
			elif len(group_data['teeth']) == 1:
				# Single tooth procedure - log normally
				tooth_number = group_data['teeth'][0]
				self.log_activity(
					activity_type="Procedure Added",
					tooth_number=tooth_number,
					procedure_code=group_data['procedure_code'],
					new_value=f"{group_data['procedure_code']} ({group_data['status']}) on {group_data['surface']}",
					cost_impact=group_data['total_cost'],
					additional_notes=group_data['notes']
				)
		
		# Find removed procedures
		for key, procedure in old_procedures.items():
			if key not in new_procedures:
				cost_impact = -(procedure.actual_fee or procedure.standard_fee or 0)
				self.log_activity(
					activity_type="Procedure Removed",
					tooth_number=procedure.tooth_number,
					procedure_code=procedure.procedure_code,
					old_value=f"{procedure.procedure_code} ({procedure.status}) on {procedure.surface}",
					cost_impact=cost_impact,
					additional_notes=f"Removed: {procedure.notes or ''}"
				)
		
		# Find modified procedures (status or cost changes)
		for key, new_procedure in new_procedures.items():
			if key in old_procedures:
				old_procedure = old_procedures[key]
				
				# Check for status changes
				if old_procedure.status != new_procedure.status:
					self.log_activity(
						activity_type="Procedure Status Changed",
						tooth_number=new_procedure.tooth_number,
						procedure_code=new_procedure.procedure_code,
						old_value=f"Status: {old_procedure.status}",
						new_value=f"Status: {new_procedure.status}",
						additional_notes=f"Status changed from {old_procedure.status} to {new_procedure.status}"
					)
				
				# Check for cost changes
				old_cost = old_procedure.actual_fee or old_procedure.standard_fee or 0
				new_cost = new_procedure.actual_fee or new_procedure.standard_fee or 0
				if old_cost != new_cost:
					cost_impact = new_cost - old_cost
					self.log_activity(
						activity_type="Procedure Cost Modified",
						tooth_number=new_procedure.tooth_number,
						procedure_code=new_procedure.procedure_code,
						old_value=f"Cost: {frappe.format_value(old_cost, {'fieldtype': 'Currency'})}",
						new_value=f"Cost: {frappe.format_value(new_cost, {'fieldtype': 'Currency'})}",
						cost_impact=cost_impact,
						additional_notes=f"Cost changed from {old_cost} to {new_cost}"
					)
	
	def log_activity(self, activity_type, tooth_number=None, condition_code=None, procedure_code=None, 
					old_value=None, new_value=None, cost_impact=None, additional_notes=None):
		"""Log an activity to the chart activities table"""
		
		# Generate activity description
		activity_description = self.generate_activity_description(
			activity_type, tooth_number, condition_code, procedure_code, cost_impact
		)
		
		activity = {
			"activity_type": activity_type,
			"activity_description": activity_description,
			"tooth_number": tooth_number,
			"condition_code": condition_code,
			"procedure_code": procedure_code,
			"old_value": old_value,
			"new_value": new_value,
			"cost_impact": cost_impact,
			"additional_notes": additional_notes,
			"activity_datetime": now(),
			"performed_by": frappe.session.user
		}
		
		self.append("chart_activities", activity)
	
	def generate_activity_description(self, activity_type, tooth_number=None, condition_code=None, procedure_code=None, cost_impact=None):
		"""Generate a human-readable activity description"""
		
		# Handle special cases for general and multi-tooth procedures
		if tooth_number == "General":
			descriptions = {
				"Condition Added": f"Added general condition",
				"Condition Removed": f"Removed general condition",
				"Condition Modified": f"Modified general condition",
				"Procedure Added": f"Added general procedure",
				"Procedure Removed": f"Removed general procedure",
				"Procedure Status Changed": f"Changed general procedure status",
				"Procedure Cost Modified": f"Modified general procedure cost",
				"Visit Recorded": "Recorded new patient visit",
				"Chart Updated": "Updated dental chart",
				"Treatment Completed": f"Completed general treatment"
			}
		elif tooth_number and tooth_number.startswith("Multiple"):
			descriptions = {
				"Condition Added": f"Added condition to {tooth_number.lower()}",
				"Condition Removed": f"Removed condition from {tooth_number.lower()}",
				"Condition Modified": f"Modified condition on {tooth_number.lower()}",
				"Procedure Added": f"Added procedure to {tooth_number.lower()}",
				"Procedure Removed": f"Removed procedure from {tooth_number.lower()}",
				"Procedure Status Changed": f"Changed procedure status on {tooth_number.lower()}",
				"Procedure Cost Modified": f"Modified procedure cost for {tooth_number.lower()}",
				"Visit Recorded": "Recorded new patient visit",
				"Chart Updated": "Updated dental chart",
				"Treatment Completed": f"Completed treatment on {tooth_number.lower()}"
			}
		else:
			descriptions = {
				"Condition Added": f"Added condition to tooth {tooth_number}",
				"Condition Removed": f"Removed condition from tooth {tooth_number}",
				"Condition Modified": f"Modified condition on tooth {tooth_number}",
				"Procedure Added": f"Added procedure to tooth {tooth_number}",
				"Procedure Removed": f"Removed procedure from tooth {tooth_number}",
				"Procedure Status Changed": f"Changed procedure status on tooth {tooth_number}",
				"Procedure Cost Modified": f"Modified procedure cost for tooth {tooth_number}",
				"Visit Recorded": "Recorded new patient visit",
				"Chart Updated": "Updated dental chart",
				"Treatment Completed": f"Completed treatment on tooth {tooth_number}"
			}
		
		description = descriptions.get(activity_type, f"{activity_type} on tooth {tooth_number}")
		
		# Add more specific details if available
		if condition_code:
			try:
				condition_name = frappe.db.get_value("Dental Condition Master", condition_code, "condition_name")
				if condition_name:
					description += f" ({condition_name})"
			except:
				pass
		
		if procedure_code:
			try:
				procedure_name = frappe.db.get_value("Dental Procedure Master", procedure_code, "procedure_name")
				if procedure_name:
					description += f" ({procedure_name})"
			except:
				pass
		
		if cost_impact:
			description += f" - Cost Impact: {frappe.format_value(cost_impact, {'fieldtype': 'Currency'})}"
		
		return description
	
	def record_visit(self, visit_notes, findings=None, treatment_provided=None):
		"""Record a new visit with detailed information"""
		self.log_activity(
			activity_type="Visit Recorded",
			new_value=visit_notes,
			additional_notes=f"Findings: {findings or 'None'}\nTreatment: {treatment_provided or 'None'}"
		)
		
		# Update chart notes with visit information
		visit_entry = f"\n--- Visit on {today()} ---\n{visit_notes}"
		if findings:
			visit_entry += f"\nFindings: {findings}"
		if treatment_provided:
			visit_entry += f"\nTreatment: {treatment_provided}"
		
		self.notes = (self.notes or "") + visit_entry

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

@frappe.whitelist()
def record_visit(chart_name, visit_data):
	"""Record a new visit with comprehensive details"""
	import json
	if isinstance(visit_data, str):
		visit_data = json.loads(visit_data)
	
	chart = frappe.get_doc("Dental Chart", chart_name)
	
	# Create comprehensive visit summary
	visit_summary = f"{visit_data.get('visit_type', 'Visit')} - {visit_data.get('chief_complaint', 'No complaint')}"
	
	# Build detailed notes
	visit_notes = f"=== {visit_data.get('visit_type', 'VISIT')} - {visit_data.get('visit_date', today())} ===\n"
	visit_notes += f"Attending Dentist: {visit_data.get('attending_dentist', chart.dentist)}\n"
	visit_notes += f"Chief Complaint: {visit_data.get('chief_complaint', 'None')}\n"
	
	if visit_data.get('examination_findings'):
		visit_notes += f"Examination Findings: {visit_data['examination_findings']}\n"
	
	if visit_data.get('treatment_provided'):
		visit_notes += f"Treatment Provided: {visit_data['treatment_provided']}\n"
	
	if visit_data.get('medications_prescribed'):
		visit_notes += f"Medications: {visit_data['medications_prescribed']}\n"
	
	if visit_data.get('follow_up_instructions'):
		visit_notes += f"Follow-up Instructions: {visit_data['follow_up_instructions']}\n"
	
	if visit_data.get('next_visit_date'):
		visit_notes += f"Next Visit: {visit_data['next_visit_date']}\n"
	
	if visit_data.get('visit_outcome'):
		visit_notes += f"Outcome: {visit_data['visit_outcome']}\n"
	
	if visit_data.get('visit_charges'):
		visit_notes += f"Charges: {frappe.format_value(visit_data['visit_charges'], {'fieldtype': 'Currency'})}\n"
	
	if visit_data.get('visit_notes'):
		visit_notes += f"Additional Notes: {visit_data['visit_notes']}\n"
	
	visit_notes += "=" * 50 + "\n"
	
	# Log the visit activity
	chart.log_activity(
		activity_type="Visit Recorded",
		new_value=visit_summary,
		cost_impact=visit_data.get('visit_charges', 0),
		additional_notes=visit_notes
	)
	
	# Update chart notes
	chart.notes = (chart.notes or "") + "\n" + visit_notes
	
	# Update chart date if this is a new visit
	if visit_data.get('visit_date'):
		chart.chart_date = visit_data['visit_date']
	
	chart.save()
	
	return {"success": True, "message": "Visit recorded successfully"} 