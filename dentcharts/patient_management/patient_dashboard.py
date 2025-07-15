# -*- coding: utf-8 -*-
# Copyright (c) 2024, Dentcharts and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

@frappe.whitelist()
def get_dashboard_data():
    """
    Main dashboard data aggregation - reuses existing functionality
    Returns data for overview cards and patient list
    """
    try:
        # Get patient statistics using existing queries
        patient_stats = get_patient_stats()
        
        # Get appointment statistics using existing queries
        appointment_stats = get_appointment_stats()
        
        # Get payment statistics using existing queries
        payment_stats = get_payment_stats()
        
        # Get recent patient activity
        recent_activity = get_recent_patient_activity()
        
        return {
            "success": True,
            "data": {
                "patient_stats": patient_stats,
                "appointment_stats": appointment_stats,
                "payment_stats": payment_stats,
                "recent_activity": recent_activity
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dashboard Data Error")
        return {
            "success": False,
            "error": str(e)
        }

def get_patient_stats():
    """
    Get patient statistics - reuses existing dental_patient queries
    """
    try:
        # Total patients count
        total_patients = frappe.db.count("dental_patient")
        
        # Active patients (those with recent appointments)
        active_patients = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient) 
            FROM `tabdental_appointment` 
            WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        # New patients this month
        new_patients = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabdental_patient` 
            WHERE DATE(creation) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)[0][0] or 0
        
        return {
            "total": total_patients,
            "active": active_patients,
            "new_this_month": new_patients,
            "title": "Patients",
            "icon": "users"
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Stats Error")
        return {
            "total": 0,
            "active": 0,
            "new_this_month": 0,
            "title": "Patients",
            "icon": "users"
        }

def get_appointment_stats():
    """
    Get appointment statistics - reuses existing dental_appointment queries
    """
    try:
        # Today's appointments
        today_appointments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabdental_appointment` 
            WHERE DATE(appointment_date) = CURDATE()
            AND docstatus = 1
        """)[0][0] or 0
        
        # Upcoming appointments (next 7 days)
        upcoming_appointments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabdental_appointment` 
            WHERE appointment_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        # Completed appointments this month
        completed_appointments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabdental_appointment` 
            WHERE DATE(appointment_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND appointment_status = 'Completed'
            AND docstatus = 1
        """)[0][0] or 0
        
        return {
            "today": today_appointments,
            "upcoming": upcoming_appointments,
            "completed_this_month": completed_appointments,
            "title": "Appointments",
            "icon": "calendar"
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Appointment Stats Error")
        return {
            "today": 0,
            "upcoming": 0,
            "completed_this_month": 0,
            "title": "Appointments",
            "icon": "calendar"
        }

def get_payment_stats():
    """
    Get payment statistics - reuses existing dental_payment_entry queries
    """
    try:
        # Total outstanding balance
        outstanding_balance = frappe.db.sql("""
            SELECT SUM(outstanding_amount) 
            FROM `tabSales Invoice` 
            WHERE docstatus = 1 
            AND outstanding_amount > 0
        """)[0][0] or 0
        
        # Payments received this month
        payments_this_month = frappe.db.sql("""
            SELECT SUM(paid_amount) 
            FROM `tabdental_payment_entry` 
            WHERE DATE(posting_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        # Recent payments count
        recent_payments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabdental_payment_entry` 
            WHERE DATE(posting_date) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        return {
            "outstanding": outstanding_balance,
            "received_this_month": payments_this_month,
            "recent_payments": recent_payments,
            "title": "Payments",
            "icon": "credit-card"
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Stats Error")
        return {
            "outstanding": 0,
            "received_this_month": 0,
            "recent_payments": 0,
            "title": "Payments",
            "icon": "credit-card"
        }

def get_recent_patient_activity():
    """
    Get recent patient activity - reuses existing queries
    """
    try:
        # Recent appointments with patient details
        recent_activity = frappe.db.sql("""
            SELECT 
                da.patient,
                da.patient_name,
                da.appointment_date,
                da.appointment_time,
                da.appointment_status,
                da.practitioner,
                dp.mobile_number
            FROM `tabdental_appointment` da
            LEFT JOIN `tabdental_patient` dp ON da.patient = dp.name
            WHERE da.docstatus = 1
            ORDER BY da.appointment_date DESC, da.appointment_time DESC
            LIMIT 10
        """, as_dict=True)
        
        return recent_activity
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Recent Activity Error")
        return []

@frappe.whitelist()
def get_patient_list(search_term="", limit=20):
    """
    Get patient list with search - reuses existing dental_patient queries
    """
    try:
        conditions = []
        values = []
        
        if search_term:
            conditions.append("""
                (patient_name LIKE %s OR 
                 mobile_number LIKE %s OR 
                 email LIKE %s OR 
                 name LIKE %s)
            """)
            search_value = f"%{search_term}%"
            values.extend([search_value, search_value, search_value, search_value])
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        patients = frappe.db.sql(f"""
            SELECT 
                name,
                patient_name,
                mobile_number,
                email,
                sex,
                date_of_birth,
                creation,
                modified
            FROM `tabdental_patient`
            {where_clause}
            ORDER BY modified DESC
            LIMIT {limit}
        """, values, as_dict=True)
        
        # Calculate age for each patient
        for patient in patients:
            if patient.get('date_of_birth'):
                today = getdate()
                dob = getdate(patient.date_of_birth)
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                patient['age'] = age
            else:
                patient['age'] = None
        
        return {
            "success": True,
            "patients": patients
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient List Error")
        return {
            "success": False,
            "error": str(e),
            "patients": []
        }

@frappe.whitelist()
def get_patient_dashboard_data(patient_id):
    """
    Get individual patient dashboard data - reuses existing queries
    """
    try:
        # Get patient basic info
        patient = frappe.get_doc("dental_patient", patient_id)
        
        # Get recent appointments
        recent_appointments = frappe.db.sql("""
            SELECT *
            FROM `tabdental_appointment`
            WHERE patient = %s
            AND docstatus = 1
            ORDER BY appointment_date DESC
            LIMIT 5
        """, patient_id, as_dict=True)
        
        # Get payment summary
        payment_summary = frappe.db.sql("""
            SELECT 
                SUM(paid_amount) as total_paid,
                COUNT(*) as payment_count
            FROM `tabdental_payment_entry`
            WHERE patient = %s
            AND docstatus = 1
        """, patient_id, as_dict=True)[0]
        
        # Calculate age
        age = None
        if patient.date_of_birth:
            today = getdate()
            dob = getdate(patient.date_of_birth)
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        return {
            "success": True,
            "patient": patient.as_dict(),
            "age": age,
            "recent_appointments": recent_appointments,
            "payment_summary": payment_summary
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Dashboard Data Error")
        return {
            "success": False,
            "error": str(e)
        }
