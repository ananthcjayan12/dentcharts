# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DentalProcedureMaster(Document):
	def validate(self):
		self.validate_duration()
		self.validate_follow_up()
		self.set_default_currency()
	
	def validate_duration(self):
		"""Validate procedure duration"""
		if self.duration_minutes <= 0:
			frappe.throw("Duration must be greater than 0 minutes")
		
		if self.duration_minutes > 480:  # 8 hours
			frappe.throw("Duration cannot exceed 8 hours (480 minutes)")
	
	def validate_follow_up(self):
		"""Validate follow-up requirements"""
		if self.follow_up_required and not self.follow_up_days:
			frappe.throw("Follow-up days required when follow-up is needed")
		
		if self.follow_up_days and self.follow_up_days < 1:
			frappe.throw("Follow-up days must be at least 1")
	
	def set_default_currency(self):
		"""Set default currency if not specified"""
		if self.standard_fee and not self.currency:
			company_currency = frappe.defaults.get_user_default("currency")
			self.currency = company_currency or "USD"

	@staticmethod
	def create_standard_procedures():
		"""Create all standard dental procedures"""
		procedures_data = [
			# Preventive Procedures
			{
				"code": "PREV001", "name": "Routine Cleaning", "category": "Preventive",
				"complexity": "Simple", "duration": 45, "anesthesia": "None",
				"fee": 150, "insurance": 80, "billing_code": "D1110",
				"description": "Routine prophylaxis and cleaning",
				"follow_up": False
			},
			{
				"code": "PREV002", "name": "Deep Cleaning (Scaling)", "category": "Preventive",
				"complexity": "Moderate", "duration": 90, "anesthesia": "Local",
				"fee": 300, "insurance": 60, "billing_code": "D4341",
				"description": "Deep scaling and root planing",
				"follow_up": True, "follow_up_days": 7
			},
			{
				"code": "PREV003", "name": "Fluoride Treatment", "category": "Preventive",
				"complexity": "Simple", "duration": 15, "anesthesia": "None",
				"fee": 50, "insurance": 80, "billing_code": "D1208",
				"description": "Professional fluoride application",
				"follow_up": False
			},
			
			# Restorative Procedures
			{
				"code": "REST001", "name": "Composite Filling", "category": "Restorative",
				"complexity": "Simple", "duration": 60, "anesthesia": "Local",
				"fee": 250, "insurance": 70, "billing_code": "D2391",
				"description": "Tooth-colored composite restoration",
				"follow_up": True, "follow_up_days": 14
			},
			{
				"code": "REST002", "name": "Amalgam Filling", "category": "Restorative",
				"complexity": "Simple", "duration": 45, "anesthesia": "Local",
				"fee": 200, "insurance": 80, "billing_code": "D2140",
				"description": "Silver amalgam restoration",
				"follow_up": True, "follow_up_days": 14
			},
			{
				"code": "REST003", "name": "Crown Preparation", "category": "Prosthodontic",
				"complexity": "Complex", "duration": 120, "anesthesia": "Local",
				"fee": 1200, "insurance": 50, "billing_code": "D2740",
				"description": "Full crown preparation and temporary crown",
				"follow_up": True, "follow_up_days": 21
			},
			
			# Endodontic Procedures
			{
				"code": "ENDO001", "name": "Root Canal - Anterior", "category": "Endodontic",
				"complexity": "Complex", "duration": 90, "anesthesia": "Local",
				"fee": 800, "insurance": 60, "billing_code": "D3310",
				"description": "Root canal therapy for anterior tooth",
				"follow_up": True, "follow_up_days": 7
			},
			{
				"code": "ENDO002", "name": "Root Canal - Posterior", "category": "Endodontic",
				"complexity": "Advanced", "duration": 120, "anesthesia": "Local",
				"fee": 1200, "insurance": 60, "billing_code": "D3330",
				"description": "Root canal therapy for posterior tooth",
				"follow_up": True, "follow_up_days": 7
			},
			
			# Periodontal Procedures
			{
				"code": "PERIO001", "name": "Gingivitis Treatment", "category": "Periodontal",
				"complexity": "Simple", "duration": 60, "anesthesia": "None",
				"fee": 200, "insurance": 70, "billing_code": "D4346",
				"description": "Non-surgical periodontal therapy",
				"follow_up": True, "follow_up_days": 14
			},
			{
				"code": "PERIO002", "name": "Gum Graft", "category": "Periodontal",
				"complexity": "Advanced", "duration": 180, "anesthesia": "Local",
				"fee": 1500, "insurance": 40, "billing_code": "D4273",
				"description": "Soft tissue graft procedure",
				"follow_up": True, "follow_up_days": 7
			},
			
			# Oral Surgery Procedures
			{
				"code": "SURG001", "name": "Simple Extraction", "category": "Oral Surgery",
				"complexity": "Moderate", "duration": 30, "anesthesia": "Local",
				"fee": 300, "insurance": 70, "billing_code": "D7140",
				"description": "Simple tooth extraction",
				"follow_up": True, "follow_up_days": 7
			},
			{
				"code": "SURG002", "name": "Surgical Extraction", "category": "Oral Surgery",
				"complexity": "Complex", "duration": 60, "anesthesia": "Local",
				"fee": 500, "insurance": 60, "billing_code": "D7210",
				"description": "Surgical tooth extraction",
				"follow_up": True, "follow_up_days": 7
			},
			{
				"code": "SURG003", "name": "Wisdom Tooth Extraction", "category": "Oral Surgery",
				"complexity": "Advanced", "duration": 90, "anesthesia": "IV Sedation",
				"fee": 800, "insurance": 50, "billing_code": "D7230",
				"description": "Impacted wisdom tooth extraction",
				"follow_up": True, "follow_up_days": 7
			},
			
			# Cosmetic Procedures
			{
				"code": "COSM001", "name": "Teeth Whitening", "category": "Cosmetic",
				"complexity": "Simple", "duration": 90, "anesthesia": "None",
				"fee": 500, "insurance": 0, "billing_code": "D9972",
				"description": "Professional teeth whitening treatment",
				"follow_up": False
			},
			{
				"code": "COSM002", "name": "Dental Veneer", "category": "Cosmetic",
				"complexity": "Complex", "duration": 120, "anesthesia": "Local",
				"fee": 1500, "insurance": 0, "billing_code": "D2962",
				"description": "Porcelain veneer placement",
				"follow_up": True, "follow_up_days": 14
			},
			
			# Emergency Procedures
			{
				"code": "EMER001", "name": "Emergency Pain Relief", "category": "Emergency",
				"complexity": "Simple", "duration": 30, "anesthesia": "Local",
				"fee": 200, "insurance": 80, "billing_code": "D9110",
				"description": "Emergency pain management",
				"follow_up": True, "follow_up_days": 3
			},
			{
				"code": "EMER002", "name": "Abscess Drainage", "category": "Emergency",
				"complexity": "Moderate", "duration": 45, "anesthesia": "Local",
				"fee": 300, "insurance": 70, "billing_code": "D7510",
				"description": "Drainage of dental abscess",
				"follow_up": True, "follow_up_days": 3
			},
			
			# Diagnostic Procedures
			{
				"code": "DIAG001", "name": "Comprehensive Oral Exam", "category": "Diagnostic",
				"complexity": "Simple", "duration": 45, "anesthesia": "None",
				"fee": 150, "insurance": 90, "billing_code": "D0150",
				"description": "Complete oral health examination",
				"follow_up": False
			},
			{
				"code": "DIAG002", "name": "Bite Wing X-Rays", "category": "Diagnostic",
				"complexity": "Simple", "duration": 15, "anesthesia": "None",
				"fee": 80, "insurance": 80, "billing_code": "D0274",
				"description": "Bite wing radiographs",
				"follow_up": False
			}
		]
		
		created_count = 0
		for proc_data in procedures_data:
			if not frappe.db.exists("Dental Procedure Master", proc_data["code"]):
				procedure = frappe.get_doc({
					"doctype": "Dental Procedure Master",
					"procedure_code": proc_data["code"],
					"procedure_name": proc_data["name"],
					"category": proc_data["category"],
					"complexity": proc_data["complexity"],
					"duration_minutes": proc_data["duration"],
					"anesthesia_required": proc_data["anesthesia"],
					"standard_fee": proc_data["fee"],
					"insurance_coverage": proc_data["insurance"],
					"billing_code": proc_data["billing_code"],
					"description": proc_data["description"],
					"follow_up_required": proc_data["follow_up"],
					"follow_up_days": proc_data.get("follow_up_days"),
					"is_active": 1
				})
				procedure.insert()
				created_count += 1
		
		return f"Created {created_count} dental procedures" 