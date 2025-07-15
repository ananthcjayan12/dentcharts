# -*- coding: utf-8 -*-
# Copyright (c) 2024, Dentcharts and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate, format_date, add_months

def get_patient_basic_info(patient_id):
    """
    Get basic patient information - reuses existing dental_patient data
    """
    try:
        patient = frappe.get_doc("Dental Patient", patient_id)
        
        # Calculate age
        age = None
        if patient.date_of_birth:
            today = getdate()
            dob = getdate(patient.date_of_birth)
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        return {
            "success": True,
            "patient": {
                "name": patient.name,
                "patient_name": patient.patient_name,
                "age": age,
                "sex": patient.sex,
                "mobile_number": patient.mobile_number,
                "email": patient.email,
                "date_of_birth": patient.date_of_birth,
                "creation": patient.creation,
                "modified": patient.modified
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Basic Info Error")
        return {
            "success": False,
            "error": str(e)
        }

def get_patient_stats():
    """
    Get patient statistics - reuses existing dental_patient queries
    """
    try:
        # Total patients
        total_patients = frappe.db.count("Dental Patient") or 0
        
        # Active patients (with appointments in last 30 days)
        active_patients = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient) 
            FROM `tabDental Appointment` 
            WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        # New patients this month
        new_patients = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabDental Patient` 
            WHERE DATE(creation) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)[0][0] or 0
        
        # Patients with outstanding payments
        patients_with_outstanding = frappe.db.sql("""
            SELECT COUNT(DISTINCT si.customer) 
            FROM `tabSales Invoice` si
            WHERE si.docstatus = 1 
            AND si.outstanding_amount > 0
            AND si.customer IN (
                SELECT name FROM `tabdental_patient`
            )
        """)[0][0] or 0
        
        return {
            "total": total_patients,
            "active": active_patients,
            "new_this_month": new_patients,
            "with_outstanding": patients_with_outstanding
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Stats Error")
        return {
            "total": 0,
            "active": 0,
            "new_this_month": 0,
            "with_outstanding": 0
        }

def get_patient_summary_by_date(patient_id):
    """
    Get patient summary organized by date - pure data aggregation
    """
    try:
        # Get appointments with related data
        appointments = frappe.db.sql("""
            SELECT 
                da.appointment_date,
                da.appointment_time,
                da.practitioner,
                da.chief_complaint,
                da.appointment_status,
                da.notes,
                da.name as appointment_id
            FROM `tabdental_appointment` da
            WHERE da.patient = %s
            AND da.docstatus = 1
            ORDER BY da.appointment_date DESC, da.appointment_time DESC
        """, patient_id, as_dict=True)
        
        summary_by_date = []
        
        for appointment in appointments:
            appointment_date = appointment.appointment_date
            
            # Get procedures for this appointment
            procedures = frappe.db.sql("""
                SELECT 
                    tp.tooth_number,
                    tp.procedure_name,
                    tp.procedure_status,
                    tp.cost,
                    tp.notes
                FROM `tabtooth_procedure` tp
                WHERE tp.appointment = %s
                ORDER BY tp.tooth_number
            """, appointment.appointment_id, as_dict=True)
            
            # Get conditions for this appointment
            conditions = frappe.db.sql("""
                SELECT 
                    tc.tooth_number,
                    tc.condition_name,
                    tc.severity,
                    tc.notes
                FROM `tabtooth_condition` tc
                WHERE tc.appointment = %s
                ORDER BY tc.tooth_number
            """, appointment.appointment_id, as_dict=True)
            
            # Get chart activities for this appointment
            activities = frappe.db.sql("""
                SELECT 
                    dca.activity_type,
                    dca.description,
                    dca.tooth_number,
                    dca.findings
                FROM `tabdental_chart_activity` dca
                WHERE dca.appointment = %s
                ORDER BY dca.creation
            """, appointment.appointment_id, as_dict=True)
            
            summary_by_date.append({
                "date": appointment_date,
                "doctor": appointment.practitioner,
                "chief_complaint": appointment.chief_complaint,
                "notes": appointment.notes,
                "status": appointment.appointment_status,
                "procedures": procedures,
                "conditions": conditions,
                "activities": activities,
                "appointment_id": appointment.appointment_id
            })
        
        return {
            "success": True,
            "summary": summary_by_date
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Summary Error")
        return {
            "success": False,
            "error": str(e),
            "summary": []
        }

def get_patient_payment_summary(patient_id):
    """
    Get patient payment summary - reuses existing payment data
    """
    try:
        # Get payment history
        payments = frappe.db.sql("""
            SELECT 
                dpe.posting_date,
                dpe.paid_amount,
                dpe.mode_of_payment,
                dpe.reference_no,
                dpe.remarks
            FROM `tabdental_payment_entry` dpe
            WHERE dpe.patient = %s
            AND dpe.docstatus = 1
            ORDER BY dpe.posting_date DESC
        """, patient_id, as_dict=True)
        
        # Get outstanding invoices
        outstanding_invoices = frappe.db.sql("""
            SELECT 
                si.name as invoice_id,
                si.posting_date,
                si.grand_total,
                si.outstanding_amount,
                si.due_date
            FROM `tabSales Invoice` si
            WHERE si.customer = %s
            AND si.docstatus = 1
            AND si.outstanding_amount > 0
            ORDER BY si.due_date
        """, patient_id, as_dict=True)
        
        # Calculate totals
        total_paid = sum(payment.paid_amount for payment in payments)
        total_outstanding = sum(invoice.outstanding_amount for invoice in outstanding_invoices)
        
        return {
            "success": True,
            "payments": payments,
            "outstanding_invoices": outstanding_invoices,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Payment Summary Error")
        return {
            "success": False,
            "error": str(e),
            "payments": [],
            "outstanding_invoices": [],
            "total_paid": 0,
            "total_outstanding": 0
        }

def get_patient_chart_data(patient_id):
    """
    Get patient chart data - reuses existing dental_chart data
    """
    try:
        # Get existing chart data
        chart_data = frappe.db.sql("""
            SELECT 
                dc.tooth_number,
                dc.tooth_procedures,
                dc.tooth_conditions,
                dc.tooth_status,
                dc.modified
            FROM `tabdental_chart` dc
            WHERE dc.patient = %s
            ORDER BY dc.tooth_number
        """, patient_id, as_dict=True)
        
        # Get recent procedures
        recent_procedures = frappe.db.sql("""
            SELECT 
                tp.tooth_number,
                tp.procedure_name,
                tp.procedure_status,
                tp.cost,
                tp.creation
            FROM `tabtooth_procedure` tp
            WHERE tp.patient = %s
            ORDER BY tp.creation DESC
            LIMIT 10
        """, patient_id, as_dict=True)
        
        # Get recent conditions
        recent_conditions = frappe.db.sql("""
            SELECT 
                tc.tooth_number,
                tc.condition_name,
                tc.severity,
                tc.creation
            FROM `tabtooth_condition` tc
            WHERE tc.patient = %s
            ORDER BY tc.creation DESC
            LIMIT 10
        """, patient_id, as_dict=True)
        
        return {
            "success": True,
            "chart_data": chart_data,
            "recent_procedures": recent_procedures,
            "recent_conditions": recent_conditions
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Chart Data Error")
        return {
            "success": False,
            "error": str(e),
            "chart_data": [],
            "recent_procedures": [],
            "recent_conditions": []
        }

def get_patient_appointment_history(patient_id):
    """
    Get patient appointment history - reuses existing appointment data
    """
    try:
        appointments = frappe.db.sql("""
            SELECT 
                da.name,
                da.appointment_date,
                da.appointment_time,
                da.practitioner,
                da.appointment_status,
                da.chief_complaint,
                da.notes,
                da.creation
            FROM `tabdental_appointment` da
            WHERE da.patient = %s
            AND da.docstatus = 1
            ORDER BY da.appointment_date DESC, da.appointment_time DESC
        """, patient_id, as_dict=True)
        
        return {
            "success": True,
            "appointments": appointments
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Appointment History Error")
        return {
            "success": False,
            "error": str(e),
            "appointments": []
        }

def format_patient_summary(patient_id):
    """
    Format complete patient summary for display
    """
    try:
        # Get all patient data
        basic_info = get_patient_basic_info(patient_id)
        summary_data = get_patient_summary_by_date(patient_id)
        payment_summary = get_patient_payment_summary(patient_id)
        chart_data = get_patient_chart_data(patient_id)
        appointment_history = get_patient_appointment_history(patient_id)
        
        if not basic_info["success"]:
            return basic_info
        
        return {
            "success": True,
            "patient_info": basic_info["patient"],
            "summary_by_date": summary_data["summary"] if summary_data["success"] else [],
            "payment_summary": payment_summary if payment_summary["success"] else {},
            "chart_data": chart_data if chart_data["success"] else {},
            "appointment_history": appointment_history["appointments"] if appointment_history["success"] else []
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Format Patient Summary Error")
        return {
            "success": False,
            "error": str(e)
        }
