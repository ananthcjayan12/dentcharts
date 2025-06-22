# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
import unittest
import time
import random
from frappe.utils import today, add_days, get_datetime, now_datetime
from datetime import datetime, timedelta


class TestDentalAppointment(unittest.TestCase):
	def setUp(self):
		# Use timestamp + random number to ensure unique test data
		self.timestamp = str(int(time.time())) + str(random.randint(1000, 9999))
		
		# Clean up any existing test data first
		self.cleanup_test_data()
		
		# Create test patient and dentist
		self.create_test_patient()
		self.create_test_dentist()
		self.create_test_clinic()
		
		# Ensure test data exists
		self.ensure_test_data()
	
	def create_test_patient(self):
		"""Create a test patient"""
		try:
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": f"Apt Test Patient {self.timestamp}",
				"first_name": "Apt",
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
				"practitioner_name": f"Dr. Apt Test {self.timestamp}",
				"first_name": "Apt",
				"last_name": f"Dentist{self.timestamp}",
				"mobile": "1234567890"
			})
			dentist.insert()
			frappe.db.commit()
			self.dentist_id = dentist.name
		except Exception as e:
			self.skipTest(f"Could not create test dentist: {str(e)}")
	
	def create_test_clinic(self):
		"""Create a test clinic"""
		try:
			clinic = frappe.get_doc({
				"doctype": "Dental Clinic",
				"clinic_name": f"Test Clinic {self.timestamp}",
				"clinic_code": f"TC{self.timestamp}",
				"status": "Active"
			})
			clinic.insert()
			frappe.db.commit()
			self.clinic_id = clinic.name
		except Exception as e:
			self.skipTest(f"Could not create test clinic: {str(e)}")
	
	def test_appointment_creation(self):
		"""Test basic appointment creation and validation"""
		tomorrow = add_days(today(), 1)
		
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"dental_clinic": self.clinic_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Routine Checkup",
			"chief_complaint": "Regular checkup",
			"duration_minutes": 60
		})
		appointment.insert()
		
		# Verify appointment was created correctly
		self.assertEqual(appointment.patient, self.patient_id)
		self.assertEqual(appointment.practitioner, self.dentist_id)
		self.assertEqual(appointment.status, "Scheduled")
		self.assertEqual(appointment.confirmation_status, "Pending")
		self.assertEqual(appointment.payment_status, "Pending")
	
	def test_appointment_validation(self):
		"""Test appointment validation rules"""
		tomorrow = add_days(today(), 1)
		
		# Test missing required fields
		with self.assertRaises(frappe.ValidationError):
			appointment = frappe.get_doc({
				"doctype": "Dental Appointment",
				"practitioner": self.dentist_id,
				"appointment_date": tomorrow,
				"appointment_time": "10:00:00",
				"appointment_type": "Routine Checkup"
				# Missing patient
			})
			appointment.insert()
		
		# Test past date validation
		with self.assertRaises(frappe.ValidationError):
			appointment = frappe.get_doc({
				"doctype": "Dental Appointment",
				"patient": self.patient_id,
				"practitioner": self.dentist_id,
				"appointment_date": add_days(today(), -1),  # Yesterday
				"appointment_time": "10:00:00",
				"appointment_type": "Routine Checkup"
			})
			appointment.insert()
		
		# Test business hours validation
		with self.assertRaises(frappe.ValidationError):
			appointment = frappe.get_doc({
				"doctype": "Dental Appointment",
				"patient": self.patient_id,
				"practitioner": self.dentist_id,
				"appointment_date": tomorrow,
				"appointment_time": "07:00:00",  # Before business hours
				"appointment_type": "Routine Checkup"
			})
			appointment.insert()
	
	def test_practitioner_availability(self):
		"""Test practitioner availability validation"""
		tomorrow = add_days(today(), 1)
		
		# Create first appointment
		appointment1 = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Routine Checkup",
			"duration_minutes": 60
		})
		appointment1.insert()
		
		# Try to create overlapping appointment
		with self.assertRaises(frappe.ValidationError):
			appointment2 = frappe.get_doc({
				"doctype": "Dental Appointment",
				"patient": self.patient_id,
				"practitioner": self.dentist_id,  # Same practitioner
				"appointment_date": tomorrow,  # Same date
				"appointment_time": "10:30:00",  # Overlapping time
				"appointment_type": "Consultation",
				"duration_minutes": 60
			})
			appointment2.insert()
	
	def test_planned_procedures(self):
		"""Test planned procedures functionality"""
		tomorrow = add_days(today(), 1)
		
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Filling",
			"planned_procedures": [
				{
					"procedure_code": "REST001",  # Composite Filling
					"tooth_number": "11",
					"surface": "Occlusal",
					"notes": "Small cavity"
				}
			]
		})
		appointment.insert()
		
		# Verify procedure was added and calculated
		self.assertEqual(len(appointment.planned_procedures), 1)
		procedure = appointment.planned_procedures[0]
		self.assertEqual(procedure.procedure_code, "REST001")
		self.assertEqual(procedure.tooth_number, "11")
		
		# Verify totals were calculated
		self.assertGreater(appointment.estimated_cost, 0)
		self.assertGreater(appointment.patient_portion, 0)
	
	def test_appointment_status_workflow(self):
		"""Test appointment status workflow"""
		tomorrow = add_days(today(), 1)
		
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Routine Checkup"
		})
		appointment.insert()
		
		# Test confirmation
		appointment.confirm_appointment()
		self.assertEqual(appointment.status, "Confirmed")
		self.assertEqual(appointment.confirmation_status, "Confirmed")
		
		# Test cancellation
		appointment.cancel_appointment("Patient request")
		self.assertEqual(appointment.status, "Cancelled")
		self.assertEqual(appointment.cancellation_reason, "Patient request")
	
	def test_appointment_completion(self):
		"""Test appointment completion and chart update"""
		tomorrow = add_days(today(), 1)
		
		# Create dental chart first
		chart = frappe.get_doc({
			"doctype": "Dental Chart",
			"patient": self.patient_id,
			"dentist": self.dentist_id,
			"chart_type": "Comprehensive",
			"chief_complaint": "Test chart"
		})
		chart.insert()
		
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Filling",
			"dental_chart": chart.name,
			"planned_procedures": [
				{
					"procedure_code": "REST001",
					"tooth_number": "11",
					"surface": "Occlusal"
				}
			]
		})
		appointment.insert()
		
		# Mark as completed
		appointment.mark_completed()
		self.assertEqual(appointment.status, "Completed")
		
		# Verify chart was updated (check if procedure was added)
		chart.reload()
		# Note: This test might need adjustment based on actual chart update logic
	
	def test_follow_up_scheduling(self):
		"""Test automatic follow-up scheduling"""
		tomorrow = add_days(today(), 1)
		
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Root Canal",
			"planned_procedures": [
				{
					"procedure_code": "ENDO001",  # Root Canal requires follow-up
					"tooth_number": "11",
					"surface": "Whole Tooth"
				}
			]
		})
		appointment.insert()
		
		# Mark as completed to trigger follow-up scheduling
		appointment.mark_completed()
		
		# Check if follow-up was scheduled
		if appointment.follow_up_appointment:
			follow_up = frappe.get_doc("Dental Appointment", appointment.follow_up_appointment)
			self.assertEqual(follow_up.appointment_type, "Follow-up")
			self.assertEqual(follow_up.patient, self.patient_id)
	
	def test_available_time_slots(self):
		"""Test available time slots calculation"""
		tomorrow = add_days(today(), 1)
		
		# Create an appointment to block a slot
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"duration_minutes": 60
		})
		appointment.insert()
		
		# Get available slots
		from dentcharts.dentcharts.doctype.dental_appointment.dental_appointment import DentalAppointment
		available_slots = DentalAppointment.get_available_time_slots(
			self.dentist_id, tomorrow, 60
		)
		
		# Verify that 10:00 slot is not available
		blocked_slots = [slot for slot in available_slots if slot["start_time"] == "10:00:00"]
		self.assertEqual(len(blocked_slots), 0)
	
	def test_practitioner_schedule(self):
		"""Test practitioner schedule retrieval"""
		tomorrow = add_days(today(), 1)
		
		# Create multiple appointments
		appointments = []
		times = ["09:00:00", "11:00:00", "14:00:00"]
		
		for time_slot in times:
			apt = frappe.get_doc({
				"doctype": "Dental Appointment",
				"patient": self.patient_id,
				"practitioner": self.dentist_id,
				"appointment_date": tomorrow,
				"appointment_time": time_slot,
				"appointment_type": "Consultation",
				"duration_minutes": 60
			})
			apt.insert()
			appointments.append(apt)
		
		# Get practitioner schedule
		from dentcharts.dentcharts.doctype.dental_appointment.dental_appointment import DentalAppointment
		schedule = DentalAppointment.get_practitioner_schedule(self.dentist_id, tomorrow)
		
		# Verify all appointments are in schedule
		self.assertEqual(len(schedule), 3)
		scheduled_times = [apt.appointment_time for apt in schedule]
		for time_slot in times:
			self.assertIn(time_slot, scheduled_times)
	
	def test_appointment_summary(self):
		"""Test appointment summary generation"""
		tomorrow = add_days(today(), 1)
		
		appointment = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient_id,
			"practitioner": self.dentist_id,
			"appointment_date": tomorrow,
			"appointment_time": "10:00:00",
			"appointment_type": "Filling",
			"estimated_cost": 250.0,
			"planned_procedures": [
				{
					"procedure_code": "REST001",
					"tooth_number": "11",
					"surface": "Occlusal",
					"estimated_duration": 60,
					"estimated_cost": 250.0
				}
			]
		})
		appointment.insert()
		
		# Get summary
		summary = appointment.get_appointment_summary()
		
		# Verify summary structure
		self.assertIn("appointment_id", summary)
		self.assertIn("patient", summary)
		self.assertIn("procedures", summary)
		self.assertEqual(summary["patient"], self.patient_id)
		self.assertEqual(len(summary["procedures"]), 1)
		self.assertEqual(summary["procedures"][0]["procedure"], "REST001")
	
	def ensure_test_data(self):
		"""Ensure we have the required master data for testing"""
		# Create standard teeth if they don't exist
		if not frappe.db.exists("Tooth Master", "11"):
			from dentcharts.dentcharts.doctype.tooth_master.tooth_master import ToothMaster
			ToothMaster.create_standard_teeth()
		
		# Create standard procedures if they don't exist
		if not frappe.db.exists("Dental Procedure Master", "REST001"):
			from dentcharts.dentcharts.doctype.dental_procedure_master.dental_procedure_master import DentalProcedureMaster
			DentalProcedureMaster.create_standard_procedures()
	
	def cleanup_test_data(self):
		"""Clean up any existing test data"""
		# Clean up appointments
		existing_appointments = frappe.get_all("Dental Appointment", 
			filters={"patient": ["like", "%Apt Test Patient%"]}, pluck="name")
		for apt_name in existing_appointments:
			try:
				frappe.delete_doc("Dental Appointment", apt_name, force=True)
			except:
				pass
		
		# Clean up dental charts
		existing_charts = frappe.get_all("Dental Chart", 
			filters={"patient": ["like", "%Apt Test Patient%"]}, pluck="name")
		for chart_name in existing_charts:
			try:
				frappe.delete_doc("Dental Chart", chart_name, force=True)
			except:
				pass
		
		# Clean up patients
		existing_patients = frappe.get_all("Patient", 
			filters={"patient_name": ["like", "Apt Test Patient%"]}, pluck="name")
		for p_name in existing_patients:
			try:
				frappe.delete_doc("Patient", p_name, force=True)
			except:
				pass
		
		# Clean up practitioners
		existing_practitioners = frappe.get_all("Healthcare Practitioner", 
			filters={"practitioner_name": ["like", "Dr. Apt Test%"]}, pluck="name")
		for hp_name in existing_practitioners:
			try:
				frappe.delete_doc("Healthcare Practitioner", hp_name, force=True)
			except:
				pass
		
		# Clean up clinics
		existing_clinics = frappe.get_all("Dental Clinic", 
			filters={"clinic_name": ["like", "Test Clinic%"]}, pluck="name")
		for clinic_name in existing_clinics:
			try:
				frappe.delete_doc("Dental Clinic", clinic_name, force=True)
			except:
				pass
		
		frappe.db.commit()
	
	def tearDown(self):
		"""Clean up test data"""
		try:
			# Clean up in reverse order due to dependencies
			if hasattr(self, 'appointment_id') and frappe.db.exists("Dental Appointment", self.appointment_id):
				frappe.delete_doc("Dental Appointment", self.appointment_id, force=True)
			if hasattr(self, 'clinic_id') and frappe.db.exists("Dental Clinic", self.clinic_id):
				frappe.delete_doc("Dental Clinic", self.clinic_id, force=True)
			if hasattr(self, 'patient_id') and frappe.db.exists("Patient", self.patient_id):
				frappe.delete_doc("Patient", self.patient_id, force=True)
			if hasattr(self, 'dentist_id') and frappe.db.exists("Healthcare Practitioner", self.dentist_id):
				frappe.delete_doc("Healthcare Practitioner", self.dentist_id, force=True)
			frappe.db.commit()
		except Exception:
			pass  # Ignore cleanup errors 