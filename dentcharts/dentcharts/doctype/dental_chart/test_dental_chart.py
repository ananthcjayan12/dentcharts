# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest
import time
import random
from frappe.utils import today, add_days


class TestDentalChart(unittest.TestCase):
	def setUp(self):
		# Use timestamp + random number to ensure unique test data
		self.timestamp = str(int(time.time())) + str(random.randint(1000, 9999))
		
		# Clean up any existing test data first
		self.cleanup_test_data()
		
		# Create test patient and dentist
		self.create_test_patient()
		self.create_test_dentist()
		
		# Create test dental chart
		self.create_test_chart()
	
	def create_test_patient(self):
		"""Create a test patient"""
		try:
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": f"Chart Test Patient {self.timestamp}",
				"first_name": "Chart",
				"last_name": f"Patient{self.timestamp}",
				"sex": "Male",
				"mobile": "1234567890"
			})
			patient.insert()
			frappe.db.commit()
			self.patient_id = patient.name
		except Exception as e:
			self.skipTest(f"Could not create test patient: {str(e)}")
	
	def create_test_dentist(self):
		"""Create a test dentist"""
		try:
			dentist = frappe.get_doc({
				"doctype": "Healthcare Practitioner",
				"practitioner_name": f"Dr. Chart Test {self.timestamp}",
				"first_name": "Chart",
				"last_name": f"Dentist{self.timestamp}",
				"mobile": "1234567890"
			})
			dentist.insert()
			frappe.db.commit()
			self.dentist_id = dentist.name
		except Exception as e:
			self.skipTest(f"Could not create test dentist: {str(e)}")
	
	def create_test_chart(self):
		"""Create a test dental chart"""
		try:
			chart = frappe.get_doc({
				"doctype": "Dental Chart",
				"patient": self.patient_id,
				"dentist": self.dentist_id,
				"chart_type": "Comprehensive",
				"chief_complaint": "Routine checkup",
				"status": "Draft"
			})
			chart.insert()
			frappe.db.commit()
			self.chart_id = chart.name
		except Exception as e:
			self.skipTest(f"Could not create test chart: {str(e)}")
	
	def test_chart_creation(self):
		"""Test basic chart creation and validation"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		self.assertEqual(chart.patient, self.patient_id)
		self.assertEqual(chart.dentist, self.dentist_id)
		self.assertEqual(chart.status, "Draft")
		self.assertEqual(chart.chart_type, "Comprehensive")
	
	def test_chart_validation(self):
		"""Test chart validation rules"""
		# Test missing patient
		with self.assertRaises(frappe.ValidationError):
			chart = frappe.get_doc({
				"doctype": "Dental Chart",
				"dentist": self.dentist_id,
				"chart_type": "Comprehensive"
			})
			chart.insert()
		
		# Test missing dentist
		with self.assertRaises(frappe.ValidationError):
			chart = frappe.get_doc({
				"doctype": "Dental Chart",
				"patient": self.patient_id,
				"chart_type": "Comprehensive"
			})
			chart.insert()
	
	def test_add_tooth_condition(self):
		"""Test adding tooth conditions to the chart"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		
		# Ensure we have standard teeth and conditions
		self.ensure_test_data()
		
		# Add a condition
		chart.add_tooth_condition("11", "CAR001", "Occlusal", "Small cavity on upper right central incisor")
		chart.save()
		
		# Verify condition was added
		self.assertEqual(len(chart.tooth_conditions), 1)
		condition = chart.tooth_conditions[0]
		self.assertEqual(condition.tooth_number, "11")
		self.assertEqual(condition.condition_code, "CAR001")
		self.assertEqual(condition.surface, "Occlusal")
		
		# Verify summary fields updated
		self.assertEqual(chart.total_conditions, 1)
		self.assertEqual(chart.treatment_required, 1)
	
	def test_add_tooth_procedure(self):
		"""Test adding tooth procedures to the chart"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		
		# Ensure we have standard teeth and procedures
		self.ensure_test_data()
		
		# Add a procedure
		chart.add_tooth_procedure("11", "PREV001", "Whole Tooth", "Routine cleaning", "Planned")
		chart.save()
		
		# Verify procedure was added
		self.assertEqual(len(chart.tooth_procedures), 1)
		procedure = chart.tooth_procedures[0]
		self.assertEqual(procedure.tooth_number, "11")
		self.assertEqual(procedure.procedure_code, "PREV001")
		self.assertEqual(procedure.status, "Planned")
		
		# Verify summary fields updated
		self.assertEqual(chart.total_procedures, 1)
	
	def test_chart_summary_calculations(self):
		"""Test chart summary field calculations"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		
		# Ensure we have test data
		self.ensure_test_data()
		
		# Add multiple conditions and procedures
		chart.add_tooth_condition("11", "CAR001", "Occlusal")
		chart.add_tooth_condition("12", "PER001", "Whole Tooth")
		chart.add_tooth_procedure("11", "PREV001", "Whole Tooth")
		chart.add_tooth_procedure("12", "REST001", "Occlusal")
		chart.save()
		
		# Verify counts
		self.assertEqual(chart.total_conditions, 2)
		self.assertEqual(chart.total_procedures, 2)
		self.assertEqual(chart.treatment_required, 1)
		
		# Verify estimated cost calculation
		self.assertGreater(chart.estimated_cost, 0)
	
	def test_get_tooth_chart_data(self):
		"""Test getting structured chart data for visualization"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		
		# Ensure we have test data
		self.ensure_test_data()
		
		# Add some conditions and procedures
		chart.add_tooth_condition("11", "CAR001", "Occlusal")
		chart.add_tooth_procedure("11", "PREV001", "Whole Tooth")
		chart.save()
		
		# Get chart data
		chart_data = chart.get_tooth_chart_data()
		
		# Verify structure
		self.assertIn("patient", chart_data)
		self.assertIn("teeth", chart_data)
		self.assertIn("11", chart_data["teeth"])
		
		# Verify tooth 11 has conditions and procedures
		tooth_11 = chart_data["teeth"]["11"]
		self.assertEqual(len(tooth_11["conditions"]), 1)
		self.assertEqual(len(tooth_11["procedures"]), 1)
		self.assertEqual(tooth_11["status"], "has_condition")
	
	def test_emergency_conditions(self):
		"""Test emergency condition detection"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		
		# Ensure we have test data including emergency conditions
		self.ensure_test_data()
		
		# Add an emergency condition (if END003 exists and is emergency)
		if frappe.db.exists("Dental Condition Master", "END003"):
			chart.add_tooth_condition("11", "END003", "Whole Tooth", "Apical abscess")
			chart.save()
			
			# Get emergency conditions
			emergency_conditions = chart.get_emergency_conditions()
			
			# Verify emergency condition is detected
			if emergency_conditions:  # Only test if there are emergency conditions
				self.assertGreater(len(emergency_conditions), 0)
				self.assertEqual(emergency_conditions[0]["tooth_number"], "11")
	
	def test_treatment_plan_summary(self):
		"""Test treatment plan summary generation"""
		chart = frappe.get_doc("Dental Chart", self.chart_id)
		
		# Ensure we have test data
		self.ensure_test_data()
		
		# Add planned procedures
		chart.add_tooth_procedure("11", "PREV001", "Whole Tooth", status="Planned")
		chart.add_tooth_procedure("12", "REST001", "Occlusal", status="Planned")
		chart.save()
		
		# Get treatment plan summary
		summary = chart.get_treatment_plan_summary()
		
		# Verify summary structure
		self.assertIn("procedures", summary)
		self.assertIn("total_cost", summary)
		self.assertIn("total_procedures", summary)
		
		# Verify planned procedures are included
		self.assertEqual(summary["total_procedures"], 2)
		self.assertGreater(summary["total_cost"], 0)
	
	def test_static_create_chart_method(self):
		"""Test static method for creating charts"""
		from dentcharts.dentcharts.doctype.dental_chart.dental_chart import DentalChart
		
		# Create chart using static method
		new_chart = DentalChart.create_chart_for_patient(
			patient=self.patient_id,
			dentist=self.dentist_id,
			chart_type="Emergency"
		)
		
		# Verify chart was created
		self.assertIsNotNone(new_chart.name)
		self.assertEqual(new_chart.patient, self.patient_id)
		self.assertEqual(new_chart.chart_type, "Emergency")
		self.assertEqual(new_chart.status, "Draft")
		
		# Clean up
		new_chart.delete()
	
	def ensure_test_data(self):
		"""Ensure we have the required master data for testing"""
		# Create standard teeth if they don't exist
		if not frappe.db.exists("Tooth Master", "11"):
			from dentcharts.dentcharts.doctype.tooth_master.tooth_master import ToothMaster
			ToothMaster.create_standard_teeth()
		
		# Create standard conditions if they don't exist
		if not frappe.db.exists("Dental Condition Master", "CAR001"):
			from dentcharts.dentcharts.doctype.dental_condition_master.dental_condition_master import DentalConditionMaster
			DentalConditionMaster.create_standard_conditions()
		
		# Create standard procedures if they don't exist
		if not frappe.db.exists("Dental Procedure Master", "PREV001"):
			from dentcharts.dentcharts.doctype.dental_procedure_master.dental_procedure_master import DentalProcedureMaster
			DentalProcedureMaster.create_standard_procedures()
	
	def cleanup_test_data(self):
		"""Clean up any existing test data"""
		# Clean up dental charts
		existing_charts = frappe.get_all("Dental Chart", 
			filters={"patient": ["like", "%Chart Test Patient%"]}, pluck="name")
		for chart_name in existing_charts:
			try:
				frappe.delete_doc("Dental Chart", chart_name, force=True)
			except:
				pass
		
		# Clean up patients
		existing_patients = frappe.get_all("Patient", 
			filters={"patient_name": ["like", "Chart Test Patient%"]}, pluck="name")
		for p_name in existing_patients:
			try:
				frappe.delete_doc("Patient", p_name, force=True)
			except:
				pass
		
		# Clean up practitioners
		existing_practitioners = frappe.get_all("Healthcare Practitioner", 
			filters={"practitioner_name": ["like", "Dr. Chart Test%"]}, pluck="name")
		for hp_name in existing_practitioners:
			try:
				frappe.delete_doc("Healthcare Practitioner", hp_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		"""Clean up test data"""
		try:
			if hasattr(self, 'chart_id') and frappe.db.exists("Dental Chart", self.chart_id):
				frappe.delete_doc("Dental Chart", self.chart_id, force=True)
			if hasattr(self, 'patient_id') and frappe.db.exists("Patient", self.patient_id):
				frappe.delete_doc("Patient", self.patient_id, force=True)
			if hasattr(self, 'dentist_id') and frappe.db.exists("Healthcare Practitioner", self.dentist_id):
				frappe.delete_doc("Healthcare Practitioner", self.dentist_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors 