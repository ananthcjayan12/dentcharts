# -*- coding: utf-8 -*-
# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

"""
Dashboard Chart Configurations for Dental ERP
Defines all dashboard charts and their data sources
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_months, flt, cint, add_days
from dentcharts.dentcharts.dashboard_utils import (
    get_executive_dashboard_data,
    get_clinical_dashboard_data,
    get_financial_dashboard_data,
    get_operational_dashboard_data
)

# ============================================================================
# EXECUTIVE DASHBOARD CHARTS
# ============================================================================

def get_executive_dashboard_charts():
    """Get all charts for Executive Dashboard"""
    return [
        {
            "chart_name": _("Monthly Revenue Trend"),
            "chart_type": "Line",
            "timeseries": 1,
            "filters_json": '{}',
            "source": "Monthly Revenue Trend",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#36C6AF"
        },
        {
            "chart_name": _("Patient Demographics"),
            "chart_type": "Donut",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Patient Demographics",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#5E64FF"
        },
        {
            "chart_name": _("Treatment Success Rate"),
            "chart_type": "Bar",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Treatment Success Rate",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#FF6B6B"
        },
        {
            "chart_name": _("Collection Efficiency"),
            "chart_type": "Percentage",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Collection Efficiency",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#4ECDC4"
        }
    ]

@frappe.whitelist()
def get_monthly_revenue_trend_data(chart_name=None, filters=None):
    """Get data for Monthly Revenue Trend chart"""
    try:
        # Get last 12 months of data
        end_date = getdate()
        start_date = add_months(end_date, -12)
        
        data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%%Y-%%m') as month,
                SUM(grand_total) as revenue
            FROM `tabInvoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
            GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
            ORDER BY month
        """, (start_date, end_date), as_dict=1)
        
        # Format data for chart
        labels = []
        datasets = []
        values = []
        
        for item in data:
            labels.append(item.get('month'))
            values.append(flt(item.get('revenue', 0)))
        
        datasets.append({
            "name": "Revenue",
            "values": values
        })
        
        return {
            "labels": labels,
            "datasets": datasets
        }
    except Exception as e:
        frappe.log_error(f"Monthly Revenue Trend Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_patient_demographics_data(chart_name=None, filters=None):
    """Get data for Patient Demographics chart"""
    try:
        data = frappe.db.sql("""
            SELECT 
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
            GROUP BY age_group
            ORDER BY count DESC
        """, as_dict=1)
        
        # Format data for donut chart
        labels = []
        values = []
        
        for item in data:
            labels.append(item.get('age_group'))
            values.append(cint(item.get('count', 0)))
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Patients",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Patient Demographics Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_treatment_success_rate_data(chart_name=None, filters=None):
    """Get data for Treatment Success Rate chart"""
    try:
        # Get last 3 months of data
        end_date = getdate()
        start_date = add_months(end_date, -3)
        
        data = frappe.db.sql("""
            SELECT 
                tpi.procedure_name,
                COUNT(*) as total_count,
                SUM(CASE WHEN tpi.status = 'Completed' THEN 1 ELSE 0 END) as completed_count
            FROM `tabTreatment Plan Item` tpi
            INNER JOIN `tabTreatment Plan` tp ON tpi.parent = tp.name
            WHERE tp.creation BETWEEN %s AND %s
            GROUP BY tpi.procedure_name
            HAVING total_count >= 5
            ORDER BY completed_count DESC
            LIMIT 10
        """, (start_date, end_date), as_dict=1)
        
        # Calculate success rates
        labels = []
        values = []
        
        for item in data:
            total = cint(item.get('total_count', 0))
            completed = cint(item.get('completed_count', 0))
            success_rate = flt((completed / total * 100) if total > 0 else 0, 1)
            
            labels.append(item.get('procedure_name'))
            values.append(success_rate)
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Success Rate (%)",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Treatment Success Rate Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_collection_efficiency_data(chart_name=None, filters=None):
    """Get data for Collection Efficiency chart"""
    try:
        # Get current month collection data
        end_date = getdate()
        start_date = add_months(end_date, -1)
        
        financial_data = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(grand_total), 0) as total_billed,
                COALESCE(SUM(outstanding_amount), 0) as total_outstanding
            FROM `tabInvoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
        """, (start_date, end_date), as_dict=1)[0]
        
        total_billed = flt(financial_data.get('total_billed', 0))
        total_outstanding = flt(financial_data.get('total_outstanding', 0))
        total_collected = total_billed - total_outstanding
        
        # Calculate collection rate
        collection_rate = flt((total_collected / total_billed * 100) if total_billed > 0 else 0, 1)
        
        return {
            "labels": ["Collection Rate"],
            "datasets": [{
                "name": "Collection Rate (%)",
                "values": [collection_rate]
            }]
        }
    except Exception as e:
        frappe.log_error(f"Collection Efficiency Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

# ============================================================================
# CLINICAL DASHBOARD CHARTS
# ============================================================================

def get_clinical_dashboard_charts():
    """Get all charts for Clinical Dashboard"""
    return [
        {
            "chart_name": _("Procedure Success Rates"),
            "chart_type": "Bar",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Procedure Success Rates",
            "module": "Dentcharts",
            "width": "Full",
            "color": "#36C6AF"
        },
        {
            "chart_name": _("Emergency Cases Trend"),
            "chart_type": "Line",
            "timeseries": 1,
            "filters_json": '{}',
            "source": "Emergency Cases Trend",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#FF6B6B"
        },
        {
            "chart_name": _("Practitioner Performance"),
            "chart_type": "Bar",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Practitioner Performance",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#5E64FF"
        }
    ]

@frappe.whitelist()
def get_procedure_success_rates_data(chart_name=None, filters=None):
    """Get data for Procedure Success Rates chart"""
    try:
        end_date = getdate()
        start_date = add_months(end_date, -6)
        
        data = frappe.db.sql("""
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
            LIMIT 15
        """, (start_date, end_date), as_dict=1)
        
        labels = []
        success_rates = []
        
        for item in data:
            total = cint(item.get('total_count', 0))
            completed = cint(item.get('completed_count', 0))
            success_rate = flt((completed / total * 100) if total > 0 else 0, 1)
            
            labels.append(item.get('procedure_name'))
            success_rates.append(success_rate)
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Success Rate (%)",
                "values": success_rates
            }]
        }
    except Exception as e:
        frappe.log_error(f"Procedure Success Rates Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_emergency_cases_trend_data(chart_name=None, filters=None):
    """Get data for Emergency Cases Trend chart"""
    try:
        end_date = getdate()
        start_date = add_months(end_date, -6)
        
        data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(creation, '%%Y-%%m') as month,
                COUNT(*) as emergency_count
            FROM `tabTreatment Plan`
            WHERE is_emergency = 1
            AND creation BETWEEN %s AND %s
            GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
            ORDER BY month
        """, (start_date, end_date), as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            labels.append(item.get('month'))
            values.append(cint(item.get('emergency_count', 0)))
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Emergency Cases",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Emergency Cases Trend Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_practitioner_performance_data(chart_name=None, filters=None):
    """Get data for Practitioner Performance chart"""
    try:
        end_date = getdate()
        start_date = add_months(end_date, -3)
        
        data = frappe.db.sql("""
            SELECT 
                tp.assigned_practitioner,
                COUNT(*) as total_treatments,
                SUM(CASE WHEN tp.status = 'Completed' THEN 1 ELSE 0 END) as completed_treatments
            FROM `tabTreatment Plan` tp
            WHERE tp.creation BETWEEN %s AND %s
            AND tp.assigned_practitioner IS NOT NULL
            GROUP BY tp.assigned_practitioner
            ORDER BY completed_treatments DESC
            LIMIT 10
        """, (start_date, end_date), as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            total = cint(item.get('total_treatments', 0))
            completed = cint(item.get('completed_treatments', 0))
            completion_rate = flt((completed / total * 100) if total > 0 else 0, 1)
            
            labels.append(item.get('assigned_practitioner'))
            values.append(completion_rate)
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Completion Rate (%)",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Practitioner Performance Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

# ============================================================================
# FINANCIAL DASHBOARD CHARTS
# ============================================================================

def get_financial_dashboard_charts():
    """Get all charts for Financial Dashboard"""
    return [
        {
            "chart_name": _("Revenue by Payment Method"),
            "chart_type": "Pie",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Revenue by Payment Method",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#36C6AF"
        },
        {
            "chart_name": _("Outstanding Balances Aging"),
            "chart_type": "Bar",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Outstanding Balances Aging",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#FF6B6B"
        },
        {
            "chart_name": _("Monthly Revenue vs Collections"),
            "chart_type": "Line",
            "timeseries": 1,
            "filters_json": '{}',
            "source": "Monthly Revenue vs Collections",
            "module": "Dentcharts",
            "width": "Full",
            "color": "#5E64FF"
        }
    ]

@frappe.whitelist()
def get_revenue_by_payment_method_data(chart_name=None, filters=None):
    """Get data for Revenue by Payment Method chart"""
    try:
        end_date = getdate()
        start_date = add_months(end_date, -3)
        
        data = frappe.db.sql("""
            SELECT 
                pe.mode_of_payment,
                SUM(pe.paid_amount) as total_amount
            FROM `tabPayment Entry` pe
            WHERE pe.posting_date BETWEEN %s AND %s
            AND pe.docstatus = 1
            GROUP BY pe.mode_of_payment
            ORDER BY total_amount DESC
        """, (start_date, end_date), as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            labels.append(item.get('mode_of_payment'))
            values.append(flt(item.get('total_amount', 0)))
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Revenue",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Revenue by Payment Method Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_outstanding_balances_aging_data(chart_name=None, filters=None):
    """Get data for Outstanding Balances Aging chart"""
    try:
        data = frappe.db.sql("""
            SELECT 
                CASE 
                    WHEN DATEDIFF(CURDATE(), due_date) <= 30 THEN '0-30 days'
                    WHEN DATEDIFF(CURDATE(), due_date) <= 60 THEN '31-60 days'
                    WHEN DATEDIFF(CURDATE(), due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket,
                SUM(outstanding_amount) as amount
            FROM `tabInvoice`
            WHERE outstanding_amount > 0
            AND docstatus = 1
            GROUP BY aging_bucket
            ORDER BY 
                CASE aging_bucket
                    WHEN '0-30 days' THEN 1
                    WHEN '31-60 days' THEN 2
                    WHEN '61-90 days' THEN 3
                    ELSE 4
                END
        """, as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            labels.append(item.get('aging_bucket'))
            values.append(flt(item.get('amount', 0)))
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Outstanding Amount",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Outstanding Balances Aging Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_monthly_revenue_vs_collections_data(chart_name=None, filters=None):
    """Get data for Monthly Revenue vs Collections chart"""
    try:
        end_date = getdate()
        start_date = add_months(end_date, -12)
        
        # Get monthly revenue data
        revenue_data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%%Y-%%m') as month,
                SUM(grand_total) as revenue,
                SUM(grand_total - outstanding_amount) as collections
            FROM `tabInvoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
            GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
            ORDER BY month
        """, (start_date, end_date), as_dict=1)
        
        labels = []
        revenue_values = []
        collection_values = []
        
        for item in revenue_data:
            labels.append(item.get('month'))
            revenue_values.append(flt(item.get('revenue', 0)))
            collection_values.append(flt(item.get('collections', 0)))
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "name": "Revenue",
                    "values": revenue_values
                },
                {
                    "name": "Collections",
                    "values": collection_values
                }
            ]
        }
    except Exception as e:
        frappe.log_error(f"Monthly Revenue vs Collections Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

# ============================================================================
# OPERATIONAL DASHBOARD CHARTS
# ============================================================================

def get_operational_dashboard_charts():
    """Get all charts for Operational Dashboard"""
    return [
        {
            "chart_name": _("Today's Appointments Status"),
            "chart_type": "Donut",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Today's Appointments Status",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#36C6AF"
        },
        {
            "chart_name": _("Practitioner Utilization"),
            "chart_type": "Bar",
            "timeseries": 0,
            "filters_json": '{}',
            "source": "Practitioner Utilization",
            "module": "Dentcharts",
            "width": "Half",
            "color": "#5E64FF"
        },
        {
            "chart_name": _("Weekly Appointment Trend"),
            "chart_type": "Line",
            "timeseries": 1,
            "filters_json": '{}',
            "source": "Weekly Appointment Trend",
            "module": "Dentcharts",
            "width": "Full",
            "color": "#FF6B6B"
        }
    ]

@frappe.whitelist()
def get_todays_appointments_status_data(chart_name=None, filters=None):
    """Get data for Today's Appointments Status chart"""
    try:
        today = getdate()
        
        data = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            GROUP BY status
        """, (today,), as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            labels.append(item.get('status'))
            values.append(cint(item.get('count', 0)))
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Appointments",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Today's Appointments Status Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_practitioner_utilization_data(chart_name=None, filters=None):
    """Get data for Practitioner Utilization chart"""
    try:
        today = getdate()
        
        data = frappe.db.sql("""
            SELECT 
                practitioner,
                COUNT(*) as scheduled_appointments
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            GROUP BY practitioner
        """, (today,), as_dict=1)
        
        labels = []
        values = []
        
        # Calculate utilization rates (assuming 8-hour workday, 30-min slots = 16 slots)
        for item in data:
            scheduled = cint(item.get('scheduled_appointments', 0))
            utilization_rate = flt((scheduled / 16 * 100) if scheduled <= 16 else 100, 1)
            
            labels.append(item.get('practitioner'))
            values.append(utilization_rate)
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Utilization Rate (%)",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Practitioner Utilization Chart Error: {str(e)}")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def get_weekly_appointment_trend_data(chart_name=None, filters=None):
    """Get data for Weekly Appointment Trend chart"""
    try:
        end_date = getdate()
        start_date = add_days(end_date, -30)  # Last 30 days
        
        data = frappe.db.sql("""
            SELECT 
                DATE(appointment_date) as date,
                COUNT(*) as appointment_count
            FROM `tabDental Appointment`
            WHERE appointment_date BETWEEN %s AND %s
            GROUP BY DATE(appointment_date)
            ORDER BY date
        """, (start_date, end_date), as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            labels.append(str(item.get('date')))
            values.append(cint(item.get('appointment_count', 0)))
        
        return {
            "labels": labels,
            "datasets": [{
                "name": "Appointments",
                "values": values
            }]
        }
    except Exception as e:
        frappe.log_error(f"Weekly Appointment Trend Chart Error: {str(e)}")
        return {"labels": [], "datasets": []} 