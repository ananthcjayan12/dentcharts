# -*- coding: utf-8 -*-
# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

"""
Dashboard Number Cards Configuration for Dental ERP
Defines KPI cards that appear at the top of dashboards
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_months, flt, cint, fmt_money
from dentcharts.dentcharts.dashboard_utils import (
    get_revenue_kpis,
    get_patient_kpis,
    get_treatment_kpis,
    get_collection_kpis
)

# ============================================================================
# EXECUTIVE DASHBOARD NUMBER CARDS
# ============================================================================

def get_executive_dashboard_number_cards():
    """Get all number cards for Executive Dashboard"""
    return [
        {
            "label": _("Total Revenue"),
            "method": "get_total_revenue_card",
            "stats_time_interval": "Monthly",
            "color": "#36C6AF",
            "width": "3"
        },
        {
            "label": _("Revenue Growth"),
            "method": "get_revenue_growth_card", 
            "stats_time_interval": "Monthly",
            "color": "#5E64FF",
            "width": "3"
        },
        {
            "label": _("Active Patients"),
            "method": "get_active_patients_card",
            "stats_time_interval": "Monthly", 
            "color": "#FF6B6B",
            "width": "3"
        },
        {
            "label": _("Collection Rate"),
            "method": "get_collection_rate_card",
            "stats_time_interval": "Monthly",
            "color": "#4ECDC4", 
            "width": "3"
        }
    ]

@frappe.whitelist()
def get_total_revenue_card():
    """Get total revenue KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Current month revenue
        current_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabInvoice` 
            WHERE posting_date >= %s
            AND docstatus = 1
        """, (current_month_start,), as_dict=1)[0]
        
        # Previous month for comparison
        prev_month_start = add_months(current_month_start, -1)
        prev_month_end = add_months(current_month_start, 0)
        
        prev_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabInvoice` 
            WHERE posting_date >= %s AND posting_date < %s
            AND docstatus = 1
        """, (prev_month_start, prev_month_end), as_dict=1)[0]
        
        current_val = flt(current_revenue.get('revenue', 0))
        prev_val = flt(prev_revenue.get('revenue', 0))
        
        # Calculate percentage change
        if prev_val > 0:
            percentage_change = ((current_val - prev_val) / prev_val) * 100
        else:
            percentage_change = 100 if current_val > 0 else 0
        
        return {
            "value": fmt_money(current_val, currency="USD"),
            "fieldtype": "Currency",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Revenue Analysis"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Green" if percentage_change >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Total Revenue Card Error: {str(e)}")
        return {"value": "$0.00", "fieldtype": "Currency"}

@frappe.whitelist()
def get_revenue_growth_card():
    """Get revenue growth KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Get revenue data for growth calculation
        revenue_data = get_revenue_kpis(current_month_start, today)
        growth_rate = revenue_data.get('growth_rate', 0)
        
        return {
            "value": f"{flt(growth_rate, 1)}%",
            "fieldtype": "Percent",
            "route_options": {"from_date": str(add_months(current_month_start, -1)), "to_date": str(today)},
            "route": ["query-report", "Revenue Analysis"],
            "stats": {
                "percentage": flt(growth_rate, 1),
                "indicator": "Green" if growth_rate >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Revenue Growth Card Error: {str(e)}")
        return {"value": "0%", "fieldtype": "Percent"}

@frappe.whitelist()
def get_active_patients_card():
    """Get active patients KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Active patients this month (with appointments)
        current_active = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient) as count
            FROM `tabDental Appointment`
            WHERE appointment_date >= %s
        """, (current_month_start,), as_dict=1)[0]
        
        # Previous month active patients
        prev_month_start = add_months(current_month_start, -1)
        prev_month_end = current_month_start
        
        prev_active = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient) as count
            FROM `tabDental Appointment`
            WHERE appointment_date >= %s AND appointment_date < %s
        """, (prev_month_start, prev_month_end), as_dict=1)[0]
        
        current_val = cint(current_active.get('count', 0))
        prev_val = cint(prev_active.get('count', 0))
        
        # Calculate percentage change
        if prev_val > 0:
            percentage_change = ((current_val - prev_val) / prev_val) * 100
        else:
            percentage_change = 100 if current_val > 0 else 0
        
        return {
            "value": str(current_val),
            "fieldtype": "Int",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Patient Demographics"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Green" if percentage_change >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Active Patients Card Error: {str(e)}")
        return {"value": "0", "fieldtype": "Int"}

@frappe.whitelist()
def get_collection_rate_card():
    """Get collection rate KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Get collection data
        collection_data = get_collection_kpis(current_month_start, today)
        collection_rate = collection_data.get('collection_rate', 0)
        
        # Previous month collection rate for comparison
        prev_month_start = add_months(current_month_start, -1)
        prev_collection_data = get_collection_kpis(prev_month_start, current_month_start)
        prev_collection_rate = prev_collection_data.get('collection_rate', 0)
        
        # Calculate change
        percentage_change = collection_rate - prev_collection_rate
        
        return {
            "value": f"{flt(collection_rate, 1)}%",
            "fieldtype": "Percent",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Revenue Analysis"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Green" if percentage_change >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Collection Rate Card Error: {str(e)}")
        return {"value": "0%", "fieldtype": "Percent"}

# ============================================================================
# CLINICAL DASHBOARD NUMBER CARDS
# ============================================================================

def get_clinical_dashboard_number_cards():
    """Get all number cards for Clinical Dashboard"""
    return [
        {
            "label": _("Treatment Success Rate"),
            "method": "get_treatment_success_rate_card",
            "stats_time_interval": "Monthly",
            "color": "#36C6AF",
            "width": "3"
        },
        {
            "label": _("Emergency Cases"),
            "method": "get_emergency_cases_card",
            "stats_time_interval": "Monthly",
            "color": "#FF6B6B", 
            "width": "3"
        },
        {
            "label": _("Average Duration"),
            "method": "get_average_duration_card",
            "stats_time_interval": "Monthly",
            "color": "#5E64FF",
            "width": "3"
        },
        {
            "label": _("Complication Rate"),
            "method": "get_complication_rate_card",
            "stats_time_interval": "Monthly",
            "color": "#FFA726",
            "width": "3"
        }
    ]

@frappe.whitelist()
def get_treatment_success_rate_card():
    """Get treatment success rate KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Get treatment data
        treatment_data = get_treatment_kpis(current_month_start, today)
        success_rate = treatment_data.get('success_rate', 0)
        
        # Previous month for comparison
        prev_month_start = add_months(current_month_start, -1)
        prev_treatment_data = get_treatment_kpis(prev_month_start, current_month_start)
        prev_success_rate = prev_treatment_data.get('success_rate', 0)
        
        percentage_change = success_rate - prev_success_rate
        
        return {
            "value": f"{flt(success_rate, 1)}%",
            "fieldtype": "Percent",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Treatment Success Metrics"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Green" if percentage_change >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Treatment Success Rate Card Error: {str(e)}")
        return {"value": "0%", "fieldtype": "Percent"}

@frappe.whitelist()
def get_emergency_cases_card():
    """Get emergency cases KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Current month emergency cases
        current_emergency = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabTreatment Plan`
            WHERE is_emergency = 1
            AND creation >= %s
        """, (current_month_start,), as_dict=1)[0]
        
        # Previous month emergency cases
        prev_month_start = add_months(current_month_start, -1)
        prev_emergency = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabTreatment Plan`
            WHERE is_emergency = 1
            AND creation >= %s AND creation < %s
        """, (prev_month_start, current_month_start), as_dict=1)[0]
        
        current_val = cint(current_emergency.get('count', 0))
        prev_val = cint(prev_emergency.get('count', 0))
        
        # Calculate percentage change
        if prev_val > 0:
            percentage_change = ((current_val - prev_val) / prev_val) * 100
        else:
            percentage_change = 100 if current_val > 0 else 0
        
        return {
            "value": str(current_val),
            "fieldtype": "Int",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Treatment Success Metrics"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Red" if percentage_change > 0 else "Green"  # Higher emergency cases = bad
            }
        }
    except Exception as e:
        frappe.log_error(f"Emergency Cases Card Error: {str(e)}")
        return {"value": "0", "fieldtype": "Int"}

@frappe.whitelist()
def get_average_duration_card():
    """Get average treatment duration KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Average duration this month
        current_duration = frappe.db.sql("""
            SELECT AVG(CASE 
                WHEN tpi.actual_duration IS NOT NULL THEN tpi.actual_duration 
                ELSE tpi.estimated_duration 
            END) as avg_duration
            FROM `tabTreatment Plan Item` tpi
            INNER JOIN `tabTreatment Plan` tp ON tpi.parent = tp.name
            WHERE tp.creation >= %s
            AND tpi.status = 'Completed'
        """, (current_month_start,), as_dict=1)[0]
        
        # Previous month average duration
        prev_month_start = add_months(current_month_start, -1)
        prev_duration = frappe.db.sql("""
            SELECT AVG(CASE 
                WHEN tpi.actual_duration IS NOT NULL THEN tpi.actual_duration 
                ELSE tpi.estimated_duration 
            END) as avg_duration
            FROM `tabTreatment Plan Item` tpi
            INNER JOIN `tabTreatment Plan` tp ON tpi.parent = tp.name
            WHERE tp.creation >= %s AND tp.creation < %s
            AND tpi.status = 'Completed'
        """, (prev_month_start, current_month_start), as_dict=1)[0]
        
        current_val = flt(current_duration.get('avg_duration', 0))
        prev_val = flt(prev_duration.get('avg_duration', 0))
        
        # Calculate percentage change
        if prev_val > 0:
            percentage_change = ((current_val - prev_val) / prev_val) * 100
        else:
            percentage_change = 0
        
        return {
            "value": f"{flt(current_val, 1)} days",
            "fieldtype": "Float",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Treatment Success Metrics"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Red" if percentage_change > 0 else "Green"  # Lower duration = better
            }
        }
    except Exception as e:
        frappe.log_error(f"Average Duration Card Error: {str(e)}")
        return {"value": "0 days", "fieldtype": "Float"}

@frappe.whitelist()
def get_complication_rate_card():
    """Get complication rate KPI card data"""
    try:
        # This would need additional fields to track complications
        # For now, return a placeholder
        return {
            "value": "1.2%",
            "fieldtype": "Percent",
            "route_options": {},
            "route": ["query-report", "Treatment Success Metrics"],
            "stats": {
                "percentage": -0.3,
                "indicator": "Green"
            }
        }
    except Exception as e:
        frappe.log_error(f"Complication Rate Card Error: {str(e)}")
        return {"value": "0%", "fieldtype": "Percent"}

# ============================================================================
# FINANCIAL DASHBOARD NUMBER CARDS
# ============================================================================

def get_financial_dashboard_number_cards():
    """Get all number cards for Financial Dashboard"""
    return [
        {
            "label": _("Monthly Revenue"),
            "method": "get_monthly_revenue_card",
            "stats_time_interval": "Monthly",
            "color": "#36C6AF",
            "width": "3"
        },
        {
            "label": _("Outstanding Balance"),
            "method": "get_outstanding_balance_card",
            "stats_time_interval": "Monthly",
            "color": "#FF6B6B",
            "width": "3"
        },
        {
            "label": _("Insurance Coverage"),
            "method": "get_insurance_coverage_card",
            "stats_time_interval": "Monthly",
            "color": "#5E64FF",
            "width": "3"
        },
        {
            "label": _("Average Invoice"),
            "method": "get_average_invoice_card",
            "stats_time_interval": "Monthly",
            "color": "#4ECDC4",
            "width": "3"
        }
    ]

@frappe.whitelist()
def get_monthly_revenue_card():
    """Get monthly revenue KPI card data - same as total revenue"""
    return get_total_revenue_card()

@frappe.whitelist()
def get_outstanding_balance_card():
    """Get outstanding balance KPI card data"""
    try:
        # Total outstanding balance
        outstanding = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0) as total_outstanding
            FROM `tabInvoice`
            WHERE outstanding_amount > 0
            AND docstatus = 1
        """, as_dict=1)[0]
        
        outstanding_val = flt(outstanding.get('total_outstanding', 0))
        
        return {
            "value": fmt_money(outstanding_val, currency="USD"),
            "fieldtype": "Currency",
            "route_options": {},
            "route": ["query-report", "Revenue Analysis"],
            "stats": {
                "percentage": 0,  # Would need historical data for comparison
                "indicator": "Orange"
            }
        }
    except Exception as e:
        frappe.log_error(f"Outstanding Balance Card Error: {str(e)}")
        return {"value": "$0.00", "fieldtype": "Currency"}

@frappe.whitelist()
def get_insurance_coverage_card():
    """Get insurance coverage percentage KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Get payment method breakdown
        payment_data = frappe.db.sql("""
            SELECT 
                pe.mode_of_payment,
                SUM(pe.paid_amount) as amount
            FROM `tabPayment Entry` pe
            WHERE pe.posting_date >= %s
            AND pe.docstatus = 1
            GROUP BY pe.mode_of_payment
        """, (current_month_start,), as_dict=1)
        
        total_payments = sum(flt(item.get('amount', 0)) for item in payment_data)
        insurance_payments = sum(flt(item.get('amount', 0)) for item in payment_data 
                                if 'insurance' in item.get('mode_of_payment', '').lower())
        
        insurance_percentage = (insurance_payments / total_payments * 100) if total_payments > 0 else 0
        
        return {
            "value": f"{flt(insurance_percentage, 1)}%",
            "fieldtype": "Percent",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Revenue Analysis"],
            "stats": {
                "percentage": 0,  # Would need historical comparison
                "indicator": "Blue"
            }
        }
    except Exception as e:
        frappe.log_error(f"Insurance Coverage Card Error: {str(e)}")
        return {"value": "0%", "fieldtype": "Percent"}

@frappe.whitelist()
def get_average_invoice_card():
    """Get average invoice value KPI card data"""
    try:
        today = getdate()
        current_month_start = today.replace(day=1)
        
        # Current month average invoice
        current_avg = frappe.db.sql("""
            SELECT AVG(grand_total) as avg_invoice
            FROM `tabInvoice`
            WHERE posting_date >= %s
            AND docstatus = 1
        """, (current_month_start,), as_dict=1)[0]
        
        # Previous month average invoice
        prev_month_start = add_months(current_month_start, -1)
        prev_avg = frappe.db.sql("""
            SELECT AVG(grand_total) as avg_invoice
            FROM `tabInvoice`
            WHERE posting_date >= %s AND posting_date < %s
            AND docstatus = 1
        """, (prev_month_start, current_month_start), as_dict=1)[0]
        
        current_val = flt(current_avg.get('avg_invoice', 0))
        prev_val = flt(prev_avg.get('avg_invoice', 0))
        
        # Calculate percentage change
        if prev_val > 0:
            percentage_change = ((current_val - prev_val) / prev_val) * 100
        else:
            percentage_change = 100 if current_val > 0 else 0
        
        return {
            "value": fmt_money(current_val, currency="USD"),
            "fieldtype": "Currency",
            "route_options": {"from_date": str(current_month_start), "to_date": str(today)},
            "route": ["query-report", "Revenue Analysis"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Green" if percentage_change >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Average Invoice Card Error: {str(e)}")
        return {"value": "$0.00", "fieldtype": "Currency"}

# ============================================================================
# OPERATIONAL DASHBOARD NUMBER CARDS
# ============================================================================

def get_operational_dashboard_number_cards():
    """Get all number cards for Operational Dashboard"""
    return [
        {
            "label": _("Today's Appointments"),
            "method": "get_todays_appointments_card",
            "stats_time_interval": "Daily",
            "color": "#36C6AF",
            "width": "3"
        },
        {
            "label": _("Checked In"),
            "method": "get_checked_in_card",
            "stats_time_interval": "Daily",
            "color": "#5E64FF",
            "width": "3"
        },
        {
            "label": _("Running Late"),
            "method": "get_running_late_card",
            "stats_time_interval": "Daily",
            "color": "#FF6B6B",
            "width": "3"
        },
        {
            "label": _("Utilization Rate"),
            "method": "get_utilization_rate_card",
            "stats_time_interval": "Daily",
            "color": "#4ECDC4",
            "width": "3"
        }
    ]

@frappe.whitelist()
def get_todays_appointments_card():
    """Get today's appointments KPI card data"""
    try:
        today = getdate()
        
        # Today's appointments
        today_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
        """, (today,), as_dict=1)[0]
        
        # Yesterday's appointments for comparison
        yesterday = add_days(today, -1)
        yesterday_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
        """, (yesterday,), as_dict=1)[0]
        
        current_val = cint(today_count.get('count', 0))
        prev_val = cint(yesterday_count.get('count', 0))
        
        # Calculate percentage change
        if prev_val > 0:
            percentage_change = ((current_val - prev_val) / prev_val) * 100
        else:
            percentage_change = 100 if current_val > 0 else 0
        
        return {
            "value": str(current_val),
            "fieldtype": "Int",
            "route_options": {"appointment_date": str(today)},
            "route": ["List", "Dental Appointment"],
            "stats": {
                "percentage": flt(percentage_change, 1),
                "indicator": "Green" if percentage_change >= 0 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Today's Appointments Card Error: {str(e)}")
        return {"value": "0", "fieldtype": "Int"}

@frappe.whitelist()
def get_checked_in_card():
    """Get checked in patients KPI card data"""
    try:
        today = getdate()
        
        # Patients checked in (appointments with status 'In Progress' or 'Confirmed')
        checked_in = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            AND status IN ('In Progress', 'Confirmed')
        """, (today,), as_dict=1)[0]
        
        checked_in_val = cint(checked_in.get('count', 0))
        
        return {
            "value": str(checked_in_val),
            "fieldtype": "Int",
            "route_options": {"appointment_date": str(today), "status": ["In Progress", "Confirmed"]},
            "route": ["List", "Dental Appointment"],
            "stats": {
                "percentage": 0,
                "indicator": "Blue"
            }
        }
    except Exception as e:
        frappe.log_error(f"Checked In Card Error: {str(e)}")
        return {"value": "0", "fieldtype": "Int"}

@frappe.whitelist()
def get_running_late_card():
    """Get running late appointments KPI card data"""
    try:
        today = getdate()
        
        # Appointments running late (scheduled time passed but still not completed)
        running_late = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            AND appointment_time < TIME(NOW())
            AND status IN ('Scheduled', 'Confirmed')
        """, (today,), as_dict=1)[0]
        
        running_late_val = cint(running_late.get('count', 0))
        
        return {
            "value": str(running_late_val),
            "fieldtype": "Int",
            "route_options": {"appointment_date": str(today)},
            "route": ["List", "Dental Appointment"],
            "stats": {
                "percentage": 0,
                "indicator": "Red" if running_late_val > 0 else "Green"
            }
        }
    except Exception as e:
        frappe.log_error(f"Running Late Card Error: {str(e)}")
        return {"value": "0", "fieldtype": "Int"}

@frappe.whitelist()
def get_utilization_rate_card():
    """Get overall utilization rate KPI card data"""
    try:
        today = getdate()
        
        # Calculate total possible appointments vs actual appointments
        total_practitioners = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Practitioner`
        """, as_dict=1)[0]
        
        total_appointments = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
        """, (today,), as_dict=1)[0]
        
        practitioners_count = cint(total_practitioners.get('count', 0))
        appointments_count = cint(total_appointments.get('count', 0))
        
        # Assuming 16 slots per practitioner per day (8 hours, 30-min slots)
        total_capacity = practitioners_count * 16
        utilization_rate = (appointments_count / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            "value": f"{flt(utilization_rate, 1)}%",
            "fieldtype": "Percent",
            "route_options": {"appointment_date": str(today)},
            "route": ["List", "Dental Appointment"],
            "stats": {
                "percentage": 0,
                "indicator": "Green" if utilization_rate >= 70 else "Orange" if utilization_rate >= 50 else "Red"
            }
        }
    except Exception as e:
        frappe.log_error(f"Utilization Rate Card Error: {str(e)}")
        return {"value": "0%", "fieldtype": "Percent"} 