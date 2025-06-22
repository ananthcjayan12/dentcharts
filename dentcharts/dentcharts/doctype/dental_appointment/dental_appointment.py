# Copyright (c) 2024, Ananthu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_days, get_datetime, now_datetime
from datetime import datetime, timedelta


class DentalAppointment(Document):
	def validate(self):
		"""Validate appointment data"""
		self.validate_appointment_datetime()
		self.validate_practitioner_availability()
		self.validate_patient_conflicts()
		self.calculate_totals()
		self.set_default_values()
	
	def validate_appointment_datetime(self):
		"""Validate appointment date and time"""
		if not self.appointment_date or not self.appointment_time:
			frappe.throw("Appointment date and time are required")
		
		# Combine date and time for validation
		appointment_datetime = get_datetime(f"{self.appointment_date} {self.appointment_time}")
		
		# Check if appointment is in the past
		if appointment_datetime < now_datetime():
			frappe.throw("Cannot schedule appointments in the past")
		
		# Check business hours (8 AM to 6 PM)
		hour = appointment_datetime.hour
		if hour < 8 or hour >= 18:
			frappe.throw("Appointments can only be scheduled between 8:00 AM and 6:00 PM")
	
	def validate_practitioner_availability(self):
		"""Check if practitioner is available at the scheduled time"""
		if not self.practitioner or not self.appointment_date or not self.appointment_time:
			return
		
		# Get appointment datetime
		appointment_datetime = get_datetime(f"{self.appointment_date} {self.appointment_time}")
		end_datetime = appointment_datetime + timedelta(minutes=self.duration_minutes or 60)
		
		# Check for overlapping appointments
		overlapping_appointments = frappe.get_all("Dental Appointment",
			filters={
				"practitioner": self.practitioner,
				"appointment_date": self.appointment_date,
				"status": ["not in", ["Cancelled", "No Show"]],
				"name": ["!=", self.name or ""]
			},
			fields=["name", "appointment_time", "duration_minutes"]
		)
		
		for apt in overlapping_appointments:
			existing_start = get_datetime(f"{self.appointment_date} {apt.appointment_time}")
			existing_end = existing_start + timedelta(minutes=apt.duration_minutes or 60)
			
			# Check for overlap
			if (appointment_datetime < existing_end and end_datetime > existing_start):
				frappe.throw(f"Practitioner is not available at this time. Conflicts with appointment {apt.name}")
	
	def validate_patient_conflicts(self):
		"""Check for patient double-booking"""
		if not self.patient or not self.appointment_date or not self.appointment_time:
			return
		
		existing_appointments = frappe.get_all("Dental Appointment",
			filters={
				"patient": self.patient,
				"appointment_date": self.appointment_date,
				"status": ["not in", ["Cancelled", "No Show"]],
				"name": ["!=", self.name or ""]
			},
			fields=["name", "appointment_time"]
		)
		
		if existing_appointments:
			frappe.throw(f"Patient already has an appointment on {self.appointment_date}")
	
	def calculate_totals(self):
		"""Calculate total duration and cost from planned procedures"""
		total_duration = 0
		total_cost = 0
		
		for procedure in self.planned_procedures:
			# Auto-populate procedure details if missing
			if procedure.procedure_code and (not procedure.estimated_cost or not procedure.estimated_duration):
				try:
					procedure_master = frappe.get_doc("Dental Procedure Master", procedure.procedure_code)
					if not procedure.estimated_cost:
						procedure.estimated_cost = procedure_master.standard_fee
					if not procedure.estimated_duration:
						procedure.estimated_duration = procedure_master.duration_minutes
				except frappe.DoesNotExistError:
					# Set defaults if master data doesn't exist
					if not procedure.estimated_cost:
						procedure.estimated_cost = 100
					if not procedure.estimated_duration:
						procedure.estimated_duration = 60
			
			if procedure.estimated_duration:
				total_duration += procedure.estimated_duration
			if procedure.estimated_cost:
				total_cost += procedure.estimated_cost
		
		# Update main fields
		if total_duration > 0:
			self.duration_minutes = total_duration
		
		self.estimated_cost = total_cost
		
		# Calculate patient portion (assuming 70% insurance coverage on average)
		if total_cost > 0:
			insurance_coverage = 0.7  # This could be dynamic based on patient insurance
			self.patient_portion = total_cost * (1 - insurance_coverage)
	
	def set_default_values(self):
		"""Set default values for new appointments"""
		if not self.status:
			self.status = "Scheduled"
		
		if not self.confirmation_status:
			self.confirmation_status = "Pending"
		
		if not self.payment_status:
			self.payment_status = "Pending"
		
		if not self.duration_minutes:
			self.duration_minutes = 60
	
	def before_submit(self):
		"""Actions before submitting appointment"""
		if self.status not in ["Confirmed", "Completed"]:
			frappe.throw("Only confirmed or completed appointments can be submitted")
		
		# Create Healthcare Appointment if not exists
		self.create_healthcare_appointment()
		
		# Update dental chart if procedures were completed
		if self.status == "Completed":
			self.update_dental_chart()
	
	def create_healthcare_appointment(self):
		"""Create corresponding Healthcare Appointment"""
		if self.healthcare_appointment:
			return  # Already linked
		
		try:
			healthcare_apt = frappe.get_doc({
				"doctype": "Patient Appointment",
				"patient": self.patient,
				"practitioner": self.practitioner,
				"appointment_date": self.appointment_date,
				"appointment_time": self.appointment_time,
				"duration": self.duration_minutes,
				"status": "Open" if self.status == "Confirmed" else "Closed",
				"notes": self.chief_complaint or f"Dental appointment: {self.appointment_type}"
			})
			healthcare_apt.insert()
			
			# Link back to our appointment
			self.healthcare_appointment = healthcare_apt.name
			
		except Exception as e:
			frappe.log_error(f"Failed to create Healthcare Appointment: {str(e)}")
	
	def update_dental_chart(self):
		"""Update dental chart with completed procedures"""
		if not self.dental_chart or self.status != "Completed":
			return
		
		try:
			chart = frappe.get_doc("Dental Chart", self.dental_chart)
			
			for procedure in self.planned_procedures:
				if procedure.procedure_code and procedure.tooth_number:
					# Add procedure to dental chart
					chart.add_tooth_procedure(
						tooth_number=procedure.tooth_number,
						procedure_code=procedure.procedure_code,
						surface=procedure.surface or "Whole Tooth",
						status="Completed",
						notes=f"Completed during appointment {self.name}"
					)
			
			chart.save()
			
		except Exception as e:
			frappe.log_error(f"Failed to update dental chart: {str(e)}")
	
	def confirm_appointment(self):
		"""Confirm the appointment"""
		self.status = "Confirmed"
		self.confirmation_status = "Confirmed"
		self.save()
		
		# Send confirmation notification (placeholder)
		self.send_confirmation_notification()
	
	def cancel_appointment(self, reason=None):
		"""Cancel the appointment"""
		self.status = "Cancelled"
		if reason:
			self.cancellation_reason = reason
		self.save()
		
		# Cancel linked Healthcare Appointment
		if self.healthcare_appointment:
			try:
				healthcare_apt = frappe.get_doc("Patient Appointment", self.healthcare_appointment)
				healthcare_apt.status = "Cancelled"
				healthcare_apt.save()
			except Exception:
				pass
	
	def reschedule_appointment(self, new_date, new_time):
		"""Reschedule the appointment"""
		old_date = self.appointment_date
		old_time = self.appointment_time
		
		self.appointment_date = new_date
		self.appointment_time = new_time
		self.status = "Rescheduled"
		
		# Validate new time slot
		self.validate()
		self.save()
		
		# Create follow-up appointment with new details
		new_appointment = self.create_follow_up_appointment(new_date, new_time)
		
		return new_appointment
	
	def mark_completed(self):
		"""Mark appointment as completed"""
		self.status = "Completed"
		self.save()
		
		# Update dental chart
		self.update_dental_chart()
		
		# Check if follow-up is needed
		self.schedule_follow_up_if_needed()
	
	def mark_no_show(self):
		"""Mark appointment as no show"""
		self.status = "No Show"
		self.save()
	
	def schedule_follow_up_if_needed(self):
		"""Schedule follow-up appointment if required by procedures"""
		follow_up_needed = False
		follow_up_days = 0
		
		for procedure in self.planned_procedures:
			if procedure.procedure_code:
				proc_master = frappe.get_doc("Dental Procedure Master", procedure.procedure_code)
				if proc_master.follow_up_required:
					follow_up_needed = True
					if proc_master.follow_up_days > follow_up_days:
						follow_up_days = proc_master.follow_up_days
		
		if follow_up_needed:
			follow_up_date = add_days(self.appointment_date, follow_up_days)
			follow_up_apt = self.create_follow_up_appointment(follow_up_date)
			self.follow_up_appointment = follow_up_apt.name
			self.save()
	
	def create_follow_up_appointment(self, follow_up_date, follow_up_time=None):
		"""Create a follow-up appointment"""
		follow_up = frappe.get_doc({
			"doctype": "Dental Appointment",
			"patient": self.patient,
			"practitioner": self.practitioner,
			"dental_clinic": self.dental_clinic,
			"appointment_date": follow_up_date,
			"appointment_time": follow_up_time or "09:00:00",
			"appointment_type": "Follow-up",
			"chief_complaint": f"Follow-up for appointment {self.name}",
			"dental_chart": self.dental_chart,
			"duration_minutes": 30,
			"status": "Scheduled"
		})
		follow_up.insert()
		
		return follow_up
	
	def send_confirmation_notification(self):
		"""Send appointment confirmation notification"""
		# Placeholder for notification system
		# This could integrate with email, SMS, or in-app notifications
		frappe.log_error(f"Appointment confirmation sent for {self.name}")
	
	def send_reminder_notification(self):
		"""Send appointment reminder notification"""
		if not self.reminder_sent:
			# Placeholder for reminder system
			self.reminder_sent = 1
			self.save()
			frappe.log_error(f"Appointment reminder sent for {self.name}")
	
	def get_appointment_summary(self):
		"""Get comprehensive appointment summary"""
		summary = {
			"appointment_id": self.name,
			"patient": self.patient,
			"practitioner": self.practitioner,
			"date": self.appointment_date,
			"time": self.appointment_time,
			"duration": self.duration_minutes,
			"status": self.status,
			"type": self.appointment_type,
			"estimated_cost": self.estimated_cost,
			"patient_portion": self.patient_portion,
			"procedures": []
		}
		
		for procedure in self.planned_procedures:
			summary["procedures"].append({
				"procedure": procedure.procedure_code,
				"tooth": procedure.tooth_number,
				"surface": procedure.surface,
				"duration": procedure.estimated_duration,
				"cost": procedure.estimated_cost
			})
		
		return summary
	
	@staticmethod
	def get_practitioner_schedule(practitioner, date):
		"""Get practitioner's schedule for a specific date"""
		appointments = frappe.get_all("Dental Appointment",
			filters={
				"practitioner": practitioner,
				"appointment_date": date,
				"status": ["not in", ["Cancelled", "No Show"]]
			},
			fields=["name", "appointment_time", "duration_minutes", "patient", "appointment_type"],
			order_by="appointment_time"
		)
		
		return appointments
	
	@staticmethod
	def get_available_time_slots(practitioner, date, duration=60):
		"""Get available time slots for a practitioner on a specific date"""
		# Business hours: 8 AM to 6 PM
		business_start = 8
		business_end = 18
		slot_duration = 30  # 30-minute slots
		
		# Get existing appointments
		existing_appointments = DentalAppointment.get_practitioner_schedule(practitioner, date)
		
		# Generate all possible slots
		available_slots = []
		current_time = business_start * 60  # Convert to minutes
		end_time = business_end * 60
		
		while current_time + duration <= end_time:
			slot_start = f"{current_time // 60:02d}:{current_time % 60:02d}:00"
			slot_end_minutes = current_time + duration
			slot_end = f"{slot_end_minutes // 60:02d}:{slot_end_minutes % 60:02d}:00"
			
			# Check if slot conflicts with existing appointments
			is_available = True
			for apt in existing_appointments:
				# Handle both string and timedelta formats
				if isinstance(apt.appointment_time, str):
					time_parts = apt.appointment_time.split(':')
					apt_start_minutes = int(time_parts[0]) * 60 + int(time_parts[1])
				else:
					# Handle timedelta object
					apt_start_minutes = int(apt.appointment_time.total_seconds() // 60)
				apt_end_minutes = apt_start_minutes + (apt.duration_minutes or 60)
				
				if (current_time < apt_end_minutes and slot_end_minutes > apt_start_minutes):
					is_available = False
					break
			
			if is_available:
				available_slots.append({
					"start_time": slot_start,
					"end_time": slot_end,
					"duration": duration
				})
			
			current_time += slot_duration
		
		return available_slots 