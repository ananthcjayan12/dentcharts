# -*- coding: utf-8 -*-
# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

"""
Dashboard Utilities for Dental ERP
Provides data aggregation and KPI calculation functions for all dashboards
"""

import frappe
from frappe.utils import getdate, add_months, add_days, flt, cint, now_datetime
from datetime import datetime, timedelta
import json

# ============================================================================
# EXECUTIVE DASHBOARD DATA FUNCTIONS
# ============================================================================

@frappe.whitelist()
def get_executive_dashboard_data(from_date=None, to_date=None):
    """Get all KPI data for executive dashboard"""
    if not from_date:
        from_date = add_months(getdate(), -1)
    if not to_date:
        to_date = getdate()
    
    try:
        # Get aggregated data from all sources
        revenue_data = get_revenue_kpis(from_date, to_date)
        patient_data = get_patient_kpis(from_date, to_date)
        treatment_data = get_treatment_kpis(from_date, to_date)
        collection_data = get_collection_kpis(from_date, to_date)
        
        return {
            "success": True,
            "data": {
                "revenue": revenue_data,
                "patients": patient_data,
                "treatments": treatment_data,
                "collections": collection_data,
                "period": {
                    "from_date": from_date,
                    "to_date": to_date
                }
            }
        }
    except Exception as e:
        frappe.log_error(f"Executive Dashboard Error: {str(e)}")
        return {"success": False, "error": str(e)}

def get_revenue_kpis(from_date, to_date):
    """Calculate revenue KPIs"""
    try:
        # Current period revenue
        current_revenue = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(grand_total), 0) as total_revenue,
                COUNT(*) as invoice_count,
                COALESCE(AVG(grand_total), 0) as avg_invoice_value
            FROM `tabInvoice` 
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
        """, (from_date, to_date), as_dict=1)[0]
        
        # Previous period for comparison
        prev_from = add_months(from_date, -1)
        prev_to = add_months(to_date, -1)
        
        prev_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0) as total_revenue
            FROM `tabInvoice` 
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
        """, (prev_from, prev_to), as_dict=1)[0]
        
        # Calculate growth percentage
        growth_rate = 0
        if prev_revenue.get('total_revenue', 0) > 0:
            growth_rate = ((current_revenue.get('total_revenue', 0) - prev_revenue.get('total_revenue', 0)) / prev_revenue.get('total_revenue', 0)) * 100
        
        return {
            "total_revenue": flt(current_revenue.get('total_revenue', 0), 2),
            "invoice_count": cint(current_revenue.get('invoice_count', 0)),
            "avg_invoice_value": flt(current_revenue.get('avg_invoice_value', 0), 2),
            "growth_rate": flt(growth_rate, 2),
            "previous_revenue": flt(prev_revenue.get('total_revenue', 0), 2)
        }
    except Exception as e:
        frappe.log_error(f"Revenue KPI Error: {str(e)}")
        return {"total_revenue": 0, "growth_rate": 0, "invoice_count": 0, "avg_invoice_value": 0}

def get_patient_kpis(from_date, to_date):
    """Calculate patient KPIs"""
    try:
        # Active patients (those with appointments or treatments in period)
        active_patients = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient) as active_count
            FROM `tabDental Appointment`
            WHERE appointment_date BETWEEN %s AND %s
        """, (from_date, to_date), as_dict=1)[0]
        
        # New patients registered in period
        new_patients = frappe.db.sql("""
            SELECT COUNT(*) as new_count
            FROM `tabDental Patient`
            WHERE creation BETWEEN %s AND %s
        """, (from_date, to_date), as_dict=1)[0]
        
        # Total patients
        total_patients = frappe.db.sql("""
            SELECT COUNT(*) as total_count
            FROM `tabDental Patient`
        """, as_dict=1)[0]
        
        # Patient demographics
        demographics = frappe.db.sql("""
            SELECT 
                p.gender,
                CASE 
                    WHEN TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) < 18 THEN 'Under 18'
                    WHEN TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) BETWEEN 18 AND 35 THEN '18-35'
                    WHEN TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) BETWEEN 36 AND 50 THEN '36-50'
                    WHEN TIMESTAMPDIFF(YEAR, p.dob, CURDATE()) BETWEEN 51 AND 65 THEN '51-65'
                    ELSE 'Over 65'
                END as age_group,
                COUNT(*) as count
            FROM `tabPatient` p
            INNER JOIN `tabDental Patient` dp ON p.name = dp.healthcare_patient
            WHERE p.dob IS NOT NULL
            GROUP BY p.gender, age_group
        """, as_dict=1)
        
        return {
            "active_patients": cint(active_patients.get('active_count', 0)),
            "new_patients": cint(new_patients.get('new_count', 0)),
            "total_patients": cint(total_patients.get('total_count', 0)),
            "demographics": demographics
        }
    except Exception as e:
        frappe.log_error(f"Patient KPI Error: {str(e)}")
        return {"active_patients": 0, "new_patients": 0, "total_patients": 0, "demographics": []}

def get_treatment_kpis(from_date, to_date):
    """Calculate treatment success KPIs"""
    try:
        # Treatment completion rates
        treatments = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_treatments,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_treatments,
                SUM(CASE WHEN is_emergency = 1 THEN 1 ELSE 0 END) as emergency_treatments
            FROM `tabTreatment Plan`
            WHERE creation BETWEEN %s AND %s
        """, (from_date, to_date), as_dict=1)[0]
        
        # Calculate success rate
        total = cint(treatments.get('total_treatments', 0))
        completed = cint(treatments.get('completed_treatments', 0))
        success_rate = (completed / total * 100) if total > 0 else 0
        
        # Top procedures
        top_procedures = frappe.db.sql("""
            SELECT 
                tpi.procedure_name,
                COUNT(*) as count,
                AVG(tpi.estimated_cost) as avg_cost
            FROM `tabTreatment Plan Item` tpi
            INNER JOIN `tabTreatment Plan` tp ON tpi.parent = tp.name
            WHERE tp.creation BETWEEN %s AND %s
            GROUP BY tpi.procedure_name
            ORDER BY count DESC
            LIMIT 5
        """, (from_date, to_date), as_dict=1)
        
        return {
            "total_treatments": total,
            "completed_treatments": completed,
            "success_rate": flt(success_rate, 2),
            "emergency_treatments": cint(treatments.get('emergency_treatments', 0)),
            "top_procedures": top_procedures
        }
    except Exception as e:
        frappe.log_error(f"Treatment KPI Error: {str(e)}")
        return {"total_treatments": 0, "success_rate": 0, "emergency_treatments": 0, "top_procedures": []}

def get_collection_kpis(from_date, to_date):
    """Calculate collection efficiency KPIs"""
    try:
        # Outstanding vs collected amounts
        financial_data = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(grand_total), 0) as total_billed,
                COALESCE(SUM(outstanding_amount), 0) as total_outstanding
            FROM `tabInvoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
        """, (from_date, to_date), as_dict=1)[0]
        
        total_billed = flt(financial_data.get('total_billed', 0))
        total_outstanding = flt(financial_data.get('total_outstanding', 0))
        total_collected = total_billed - total_outstanding
        
        # Calculate collection rate
        collection_rate = (total_collected / total_billed * 100) if total_billed > 0 else 0
        
        # Payment method breakdown
        payment_methods = frappe.db.sql("""
            SELECT 
                pe.mode_of_payment,
                SUM(pe.paid_amount) as amount,
                COUNT(*) as count
            FROM `tabPayment Entry` pe
            WHERE pe.posting_date BETWEEN %s AND %s
            AND pe.docstatus = 1
            GROUP BY pe.mode_of_payment
        """, (from_date, to_date), as_dict=1)
        
        return {
            "total_billed": total_billed,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "collection_rate": flt(collection_rate, 2),
            "payment_methods": payment_methods
        }
    except Exception as e:
        frappe.log_error(f"Collection KPI Error: {str(e)}")
        return {"collection_rate": 0, "total_billed": 0, "total_collected": 0, "payment_methods": []}

# ============================================================================
# CLINICAL DASHBOARD DATA FUNCTIONS
# ============================================================================

@frappe.whitelist()
def get_clinical_dashboard_data(from_date=None, to_date=None):
    """Get clinical performance data"""
    if not from_date:
        from_date = add_months(getdate(), -1)
    if not to_date:
        to_date = getdate()
    
    try:
        return {
            "success": True,
            "data": {
                "treatment_success": get_treatment_success_data(from_date, to_date),
                "emergency_metrics": get_emergency_metrics(from_date, to_date),
                "practitioner_performance": get_practitioner_performance(from_date, to_date),
                "complication_rates": get_complication_rates(from_date, to_date)
            }
        }
    except Exception as e:
        frappe.log_error(f"Clinical Dashboard Error: {str(e)}")
        return {"success": False, "error": str(e)}

def get_treatment_success_data(from_date, to_date):
    """Get treatment success metrics by procedure type"""
    try:
        success_data = frappe.db.sql("""
            SELECT 
                tpi.procedure_name,
                COUNT(*) as total_count,
                SUM(CASE WHEN tpi.status = 'Completed' THEN 1 ELSE 0 END) as completed_count,
                AVG(CASE WHEN tpi.actual_duration IS NOT NULL THEN tpi.actual_duration ELSE tpi.estimated_duration END) as avg_duration
            FROM `tabTreatment Plan Item` tpi
            INNER JOIN `tabTreatment Plan` tp ON tpi.parent = tp.name
            WHERE tp.creation BETWEEN %s AND %s
            GROUP BY tpi.procedure_name
            HAVING total_count >= 3
            ORDER BY completed_count DESC
        """, (from_date, to_date), as_dict=1)
        
        # Calculate success rates
        for item in success_data:
            total = cint(item.get('total_count', 0))
            completed = cint(item.get('completed_count', 0))
            item['success_rate'] = flt((completed / total * 100) if total > 0 else 0, 2)
        
        return success_data
    except Exception as e:
        frappe.log_error(f"Treatment Success Data Error: {str(e)}")
        return []

def get_emergency_metrics(from_date, to_date):
    """Get emergency treatment metrics"""
    try:
        emergency_data = frappe.db.sql("""
            SELECT 
                DATE(creation) as date,
                COUNT(*) as emergency_count,
                AVG(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) * 100 as resolution_rate
            FROM `tabTreatment Plan`
            WHERE is_emergency = 1
            AND creation BETWEEN %s AND %s
            GROUP BY DATE(creation)
            ORDER BY date
        """, (from_date, to_date), as_dict=1)
        
        return emergency_data
    except Exception as e:
        frappe.log_error(f"Emergency Metrics Error: {str(e)}")
        return []

def get_practitioner_performance(from_date, to_date):
    """Get practitioner performance comparison"""
    try:
        performance_data = frappe.db.sql("""
            SELECT 
                tp.assigned_practitioner,
                COUNT(*) as total_treatments,
                SUM(CASE WHEN tp.status = 'Completed' THEN 1 ELSE 0 END) as completed_treatments,
                AVG(tp.total_estimated_cost) as avg_treatment_value,
                COUNT(DISTINCT tp.patient) as unique_patients
            FROM `tabTreatment Plan` tp
            WHERE tp.creation BETWEEN %s AND %s
            AND tp.assigned_practitioner IS NOT NULL
            GROUP BY tp.assigned_practitioner
            ORDER BY completed_treatments DESC
        """, (from_date, to_date), as_dict=1)
        
        # Calculate completion rates
        for practitioner in performance_data:
            total = cint(practitioner.get('total_treatments', 0))
            completed = cint(practitioner.get('completed_treatments', 0))
            practitioner['completion_rate'] = flt((completed / total * 100) if total > 0 else 0, 2)
        
        return performance_data
    except Exception as e:
        frappe.log_error(f"Practitioner Performance Error: {str(e)}")
        return []

def get_complication_rates(from_date, to_date):
    """Get complication rates by procedure"""
    try:
        # This would need additional fields in the system to track complications
        # For now, return mock data structure
        return []
    except Exception as e:
        frappe.log_error(f"Complication Rates Error: {str(e)}")
        return []

# ============================================================================
# FINANCIAL DASHBOARD DATA FUNCTIONS
# ============================================================================

@frappe.whitelist()
def get_financial_dashboard_data(from_date=None, to_date=None):
    """Get financial performance data"""
    if not from_date:
        from_date = add_months(getdate(), -1)
    if not to_date:
        to_date = getdate()
    
    try:
        return {
            "success": True,
            "data": {
                "revenue_breakdown": get_revenue_breakdown(from_date, to_date),
                "outstanding_analysis": get_outstanding_analysis(from_date, to_date),
                "profit_margins": get_profit_margins(from_date, to_date),
                "insurance_analysis": get_insurance_analysis(from_date, to_date)
            }
        }
    except Exception as e:
        frappe.log_error(f"Financial Dashboard Error: {str(e)}")
        return {"success": False, "error": str(e)}

def get_revenue_breakdown(from_date, to_date):
    """Get revenue breakdown by various dimensions"""
    try:
        # Monthly revenue trend
        monthly_revenue = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%Y-%m') as month,
                SUM(grand_total) as revenue,
                COUNT(*) as invoice_count
            FROM `tabInvoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
            GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
            ORDER BY month
        """, (from_date, to_date), as_dict=1)
        
        return {"monthly_trend": monthly_revenue}
    except Exception as e:
        frappe.log_error(f"Revenue Breakdown Error: {str(e)}")
        return {"monthly_trend": []}

def get_outstanding_analysis(from_date, to_date):
    """Get outstanding balances analysis"""
    try:
        outstanding_data = frappe.db.sql("""
            SELECT 
                CASE 
                    WHEN DATEDIFF(CURDATE(), due_date) <= 30 THEN '0-30 days'
                    WHEN DATEDIFF(CURDATE(), due_date) <= 60 THEN '31-60 days'
                    WHEN DATEDIFF(CURDATE(), due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket,
                SUM(outstanding_amount) as amount,
                COUNT(*) as count
            FROM `tabInvoice`
            WHERE outstanding_amount > 0
            AND docstatus = 1
            GROUP BY aging_bucket
        """, as_dict=1)
        
        return outstanding_data
    except Exception as e:
        frappe.log_error(f"Outstanding Analysis Error: {str(e)}")
        return []

def get_profit_margins(from_date, to_date):
    """Get profit margin analysis by procedure"""
    try:
        # This would need cost tracking to be implemented
        # Return structure for future implementation
        return []
    except Exception as e:
        frappe.log_error(f"Profit Margins Error: {str(e)}")
        return []

def get_insurance_analysis(from_date, to_date):
    """Get insurance vs cash payment analysis"""
    try:
        payment_analysis = frappe.db.sql("""
            SELECT 
                pe.mode_of_payment,
                SUM(pe.paid_amount) as total_amount,
                COUNT(*) as transaction_count,
                AVG(pe.paid_amount) as avg_amount
            FROM `tabPayment Entry` pe
            WHERE pe.posting_date BETWEEN %s AND %s
            AND pe.docstatus = 1
            GROUP BY pe.mode_of_payment
            ORDER BY total_amount DESC
        """, (from_date, to_date), as_dict=1)
        
        return payment_analysis
    except Exception as e:
        frappe.log_error(f"Insurance Analysis Error: {str(e)}")
        return []

# ============================================================================
# OPERATIONAL DASHBOARD DATA FUNCTIONS
# ============================================================================

@frappe.whitelist()
def get_operational_dashboard_data(date=None):
    """Get today's operational data"""
    if not date:
        date = getdate()
    
    try:
        return {
            "success": True,
            "data": {
                "todays_appointments": get_todays_appointments(date),
                "practitioner_utilization": get_practitioner_utilization(date),
                "patient_flow": get_patient_flow(date),
                "capacity_metrics": get_capacity_metrics(date)
            }
        }
    except Exception as e:
        frappe.log_error(f"Operational Dashboard Error: {str(e)}")
        return {"success": False, "error": str(e)}

def get_todays_appointments(date):
    """Get today's appointment status"""
    try:
        appointments = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(CASE WHEN appointment_time < TIME(NOW()) AND status = 'Scheduled' THEN 1 ELSE 0 END) as running_late
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            GROUP BY status
        """, (date,), as_dict=1)
        
        # Calculate summary metrics
        total_appointments = sum(apt.get('count', 0) for apt in appointments)
        running_late = sum(apt.get('running_late', 0) for apt in appointments)
        
        return {
            "appointments_by_status": appointments,
            "total_appointments": total_appointments,
            "running_late": running_late
        }
    except Exception as e:
        frappe.log_error(f"Today's Appointments Error: {str(e)}")
        return {"appointments_by_status": [], "total_appointments": 0, "running_late": 0}

def get_practitioner_utilization(date):
    """Get practitioner utilization for today"""
    try:
        utilization = frappe.db.sql("""
            SELECT 
                practitioner,
                COUNT(*) as scheduled_appointments,
                SUM(CASE WHEN status IN ('Completed', 'In Progress') THEN 1 ELSE 0 END) as active_appointments
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            GROUP BY practitioner
        """, (date,), as_dict=1)
        
        # Calculate utilization rates (assuming 8-hour workday, 30-min slots = 16 slots)
        for prac in utilization:
            scheduled = cint(prac.get('scheduled_appointments', 0))
            prac['utilization_rate'] = flt((scheduled / 16 * 100) if scheduled <= 16 else 100, 2)
        
        return utilization
    except Exception as e:
        frappe.log_error(f"Practitioner Utilization Error: {str(e)}")
        return []

def get_patient_flow(date):
    """Get patient flow metrics for today"""
    try:
        # This would need check-in/check-out tracking
        # Return structure for future implementation
        return {
            "checked_in": 0,
            "waiting": 0,
            "in_treatment": 0,
            "completed": 0
        }
    except Exception as e:
        frappe.log_error(f"Patient Flow Error: {str(e)}")
        return {"checked_in": 0, "waiting": 0, "in_treatment": 0, "completed": 0}

def get_capacity_metrics(date):
    """Get capacity planning metrics"""
    try:
        # Calculate available vs booked slots
        total_slots = frappe.db.sql("""
            SELECT COUNT(DISTINCT practitioner) * 16 as total_possible_slots
            FROM `tabDental Practitioner`
        """, as_dict=1)[0]
        
        booked_slots = frappe.db.sql("""
            SELECT COUNT(*) as booked_slots
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
        """, (date,), as_dict=1)[0]
        
        total_possible = cint(total_slots.get('total_possible_slots', 0))
        booked = cint(booked_slots.get('booked_slots', 0))
        
        return {
            "total_capacity": total_possible,
            "booked_slots": booked,
            "available_slots": total_possible - booked,
            "utilization_rate": flt((booked / total_possible * 100) if total_possible > 0 else 0, 2)
        }
    except Exception as e:
        frappe.log_error(f"Capacity Metrics Error: {str(e)}")
        return {"total_capacity": 0, "booked_slots": 0, "available_slots": 0, "utilization_rate": 0}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_currency(amount, currency="USD"):
    """Format currency values consistently"""
    return f"{currency} {flt(amount, 2):,.2f}"

def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0 if current == 0 else 100
    return flt(((current - previous) / previous) * 100, 2)

def get_trend_indicator(percentage):
    """Get trend indicator (up/down/flat) based on percentage"""
    if percentage > 5:
        return "up"
    elif percentage < -5:
        return "down"
    else:
        return "flat"

@frappe.whitelist()
def get_dashboard_summary():
    """Get high-level summary for all dashboards"""
    try:
        today = getdate()
        last_month = add_months(today, -1)
        
        # Get key metrics
        executive_data = get_executive_dashboard_data(last_month, today)
        
        if executive_data.get("success"):
            revenue = executive_data["data"]["revenue"]
            patients = executive_data["data"]["patients"]
            treatments = executive_data["data"]["treatments"]
            collections = executive_data["data"]["collections"]
            
            return {
                "success": True,
                "summary": {
                    "total_revenue": format_currency(revenue.get("total_revenue", 0)),
                    "active_patients": patients.get("active_patients", 0),
                    "success_rate": f"{treatments.get('success_rate', 0)}%",
                    "collection_rate": f"{collections.get('collection_rate', 0)}%",
                    "revenue_growth": f"{revenue.get('growth_rate', 0)}%"
                }
            }
        else:
            return {"success": False, "error": "Could not fetch dashboard summary"}
            
    except Exception as e:
        frappe.log_error(f"Dashboard Summary Error: {str(e)}")
        return {"success": False, "error": str(e)} 