import unittest
import frappe
from frappe.utils import today, add_days, flt
import random
import time

class TestTreatmentPlan(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		# Use timestamp + random number to ensure unique test data
		self.timestamp = str(int(time.time())) + str(random.randint(1000, 9999))
		
		# Ensure required master data exists
		self.ensure_test_data()
		
		# Clean up any existing test data
		self.cleanup_test_data()
		
		# Create test records
		self.patient_id = self.create_test_patient()
		self.dentist_id = self.create_test_dentist()
		self.dental_chart_id = self.create_test_dental_chart()
	
	def create_test_patient(self):
		"""Create a test patient"""
		try:
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": f"TP Test Patient {self.timestamp}",
				"first_name": "TP",
				"last_name": f"Patient{self.timestamp}",
				"sex": "Male",
				"mobile": "1234567890"
			})
			patient.insert()
			return patient.name
		except Exception:
			# If creation fails, try to find existing patient
			existing = frappe.db.get_value("Patient", {"patient_name": f"TP Test Patient {self.timestamp}"}, "name")
			return existing
	
	def create_test_dentist(self):
		"""Create a test dentist"""
		try:
			dentist = frappe.get_doc({
				"doctype": "Healthcare Practitioner",
				"practitioner_name": f"Dr. TP Test {self.timestamp}",
				"first_name": "TP",
				"last_name": f"Test{self.timestamp}",
				"department": "Dental"
			})
			dentist.insert()
			return dentist.name
		except Exception:
			# If creation fails, try to find existing dentist
			existing = frappe.db.get_value("Healthcare Practitioner", {"practitioner_name": f"Dr. TP Test {self.timestamp}"}, "name")
			return existing
	
	def create_test_dental_chart(self):
		"""Create a test dental chart"""
		try:
			chart = frappe.get_doc({
				"doctype": "Dental Chart",
				"patient": self.patient_id,
				"dentist": self.dentist_id,
				"chart_type": "Comprehensive",
				"chief_complaint": "Test chart for treatment planning"
			})
			chart.insert()
			return chart.name
		except Exception:
			# If creation fails, try to find existing chart
			existing = frappe.db.get_value("Dental Chart", {"patient": self.patient_id}, "name")
			return existing
	
	def test_treatment_plan_creation(self):
		"""Test basic treatment plan creation"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"dental_chart": self.dental_chart_id,
			"treatment_goals": "Restore oral health",
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "PREV001",  # Routine Cleaning
					"priority": "Medium",
					"estimated_cost": 150.0,
					"estimated_duration": 60
				}
			]
		})
		plan.insert()
		
		# Verify plan was created successfully
		self.assertEqual(plan.plan_status, "Draft")
		self.assertEqual(len(plan.plan_items), 1)
		self.assertEqual(plan.total_estimated_cost, 150.0)
		self.assertEqual(plan.total_estimated_duration, 60)
	
	def test_cost_calculations(self):
		"""Test cost and insurance calculations"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"insurance_coverage_percentage": 70,
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "REST001",  # Composite Filling
					"estimated_cost": 250.0,
					"insurance_coverage_percentage": 80
				},
				{
					"treatment_sequence": 2,
					"procedure_code": "PREV001",  # Routine Cleaning
					"estimated_cost": 150.0,
					"insurance_coverage_percentage": 70
				}
			]
		})
		plan.insert()
		
		# Verify individual item calculations
		item1 = plan.plan_items[0]
		self.assertEqual(item1.insurance_amount, 200.0)  # 80% of 250
		self.assertEqual(item1.patient_portion, 50.0)    # 250 - 200
		
		item2 = plan.plan_items[1]
		self.assertEqual(item2.insurance_amount, 105.0)  # 70% of 150
		self.assertEqual(item2.patient_portion, 45.0)    # 150 - 105
		
		# Verify total calculations
		self.assertEqual(plan.total_estimated_cost, 400.0)  # 250 + 150
		self.assertEqual(plan.insurance_amount, 305.0)      # 200 + 105
		self.assertEqual(plan.patient_portion, 95.0)        # 400 - 305
	
	def test_progress_tracking(self):
		"""Test treatment plan progress tracking"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "REST001",
					"item_status": "Completed"
				},
				{
					"treatment_sequence": 2,
					"procedure_code": "PREV001",
					"item_status": "Planned"
				},
				{
					"treatment_sequence": 3,
					"procedure_code": "PREV002",
					"item_status": "Completed"
				}
			]
		})
		plan.insert()
		
		# Verify progress calculations
		self.assertEqual(plan.total_items, 3)
		self.assertEqual(plan.completed_items, 2)
		self.assertEqual(plan.plan_progress, 66.67)  # 2/3 * 100, rounded to 2 decimals
	
	def test_status_workflow(self):
		"""Test treatment plan status workflow"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "REST001",
					"item_status": "Planned"
				}
			]
		})
		plan.insert()
		
		# Initial status should be Draft
		self.assertEqual(plan.plan_status, "Draft")
		
		# Activate plan
		plan.activate_plan()
		self.assertEqual(plan.plan_status, "Active")
		self.assertEqual(plan.start_date, today())
		
		# Mark item as completed to trigger progress update
		plan.plan_items[0].item_status = "Completed"
		plan.save()
		
		# Plan should auto-complete when all items are done
		self.assertEqual(plan.plan_status, "Completed")
		self.assertEqual(plan.actual_completion_date, today())
	
	def test_sequence_validation(self):
		"""Test treatment sequence validation"""
		# Test duplicate sequence numbers should fail
		with self.assertRaises(frappe.ValidationError):
			plan = frappe.get_doc({
				"doctype": "Treatment Plan",
				"patient": self.patient_id,
				"dentist": self.dentist_id,
				"plan_items": [
					{
						"treatment_sequence": 1,
						"procedure_code": "REST001"
					},
					{
						"treatment_sequence": 1,  # Duplicate sequence
						"procedure_code": "PREV001"
					}
				]
			})
			plan.insert()
		
		# Test auto-assignment of sequence numbers
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"plan_items": [
				{
					"procedure_code": "REST001"
					# No sequence number provided
				},
				{
					"procedure_code": "PREV001"
					# No sequence number provided
				}
			]
		})
		plan.insert()
		
		# Verify auto-assigned sequences
		self.assertEqual(plan.plan_items[0].treatment_sequence, 1)
		self.assertEqual(plan.plan_items[1].treatment_sequence, 2)
	
	def test_date_validation(self):
		"""Test date validation"""
		# Test start date in past should fail
		with self.assertRaises(frappe.ValidationError):
			plan = frappe.get_doc({
				"doctype": "Treatment Plan",
				"patient": self.patient_id,
				"dentist": self.dentist_id,
				"start_date": add_days(today(), -1),  # Yesterday
				"plan_items": [
					{
						"treatment_sequence": 1,
						"procedure_code": "REST001"
					}
				]
			})
			plan.insert()
		
		# Test target completion before start date should fail
		with self.assertRaises(frappe.ValidationError):
			plan = frappe.get_doc({
				"doctype": "Treatment Plan",
				"patient": self.patient_id,
				"dentist": self.dentist_id,
				"start_date": add_days(today(), 7),
				"target_completion_date": add_days(today(), 3),  # Before start date
				"plan_items": [
					{
						"treatment_sequence": 1,
						"procedure_code": "REST001"
					}
				]
			})
			plan.insert()
	
	def test_treatment_summary(self):
		"""Test treatment plan summary generation"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "REST001",
					"tooth_number": "11",
					"surface": "Occlusal",
					"priority": "High",
					"item_status": "Completed",
					"estimated_cost": 250.0,
					"estimated_duration": 90
				}
			]
		})
		plan.insert()
		
		summary = plan.get_treatment_summary()
		
		# Verify summary structure
		self.assertIn("plan_id", summary)
		self.assertIn("patient", summary)
		self.assertIn("items", summary)
		self.assertEqual(len(summary["items"]), 1)
		
		item_summary = summary["items"][0]
		self.assertEqual(item_summary["sequence"], 1)
		self.assertEqual(item_summary["priority"], "High")
		self.assertEqual(item_summary["status"], "Completed")
		self.assertEqual(item_summary["cost"], 250.0)
	
	def test_plan_cancellation(self):
		"""Test treatment plan cancellation"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"plan_status": "Active",
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "REST001",
					"item_status": "Planned"
				}
			]
		})
		plan.insert()
		
		# Cancel the plan
		plan.cancel_plan("Patient request")
		
		# Verify cancellation
		self.assertEqual(plan.plan_status, "Cancelled")
	
	def test_auto_populate_procedure_details(self):
		"""Test auto-population of procedure details from master data"""
		plan = frappe.get_doc({
			"doctype": "Treatment Plan",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"plan_items": [
				{
					"treatment_sequence": 1,
					"procedure_code": "REST001"  # Should auto-populate details
				}
			]
		})
		plan.insert()
		
		item = plan.plan_items[0]
		# Should have auto-populated cost and duration (if master data exists)
		# If master data doesn't exist, should have default values
		self.assertIsNotNone(item.estimated_cost)
		self.assertIsNotNone(item.estimated_duration)
	
	def ensure_test_data(self):
		"""Ensure we have the required master data for testing"""
		# Create standard procedures if they don't exist
		if not frappe.db.exists("Dental Procedure Master", "REST001"):
			try:
				from dentcharts.dentcharts.doctype.dental_procedure_master.dental_procedure_master import DentalProcedureMaster
				DentalProcedureMaster.create_standard_procedures()
			except Exception:
				pass  # Skip if procedure creation fails
	
	def cleanup_test_data(self):
		"""Clean up any existing test data"""
		# Clean up treatment plans
		existing_plans = frappe.get_all("Treatment Plan", 
			filters={"patient": ["like", "%TP Test Patient%"]}, pluck="name")
		for plan_name in existing_plans:
			try:
				frappe.delete_doc("Treatment Plan", plan_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		"""Clean up test data"""
		try:
			# Clean up in reverse order due to dependencies
			if hasattr(self, 'dental_chart_id') and frappe.db.exists("Dental Chart", self.dental_chart_id):
				frappe.delete_doc("Dental Chart", self.dental_chart_id, force=True)
			if hasattr(self, 'patient_id') and frappe.db.exists("Patient", self.patient_id):
				frappe.delete_doc("Patient", self.patient_id, force=True)
			if hasattr(self, 'dentist_id') and frappe.db.exists("Healthcare Practitioner", self.dentist_id):
				frappe.delete_doc("Healthcare Practitioner", self.dentist_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors 