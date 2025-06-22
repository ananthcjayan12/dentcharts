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
    """Get chart configurations for Executive Dashboard"""
    return [
        {
            "name": "Monthly Revenue Trend",
            "chart_type": "Line",
            "timeseries": 1,
            "filters_json": '{"period_type": "Monthly"}',
            "source": "Revenue Analysis",
            "x_field": "period",
            "y_axis": [{"y_field": "total_revenue", "color": "#36C6AF"}]
        },
        {
            "name": "Patient Demographics",
            "chart_type": "Donut",
            "source": "Patient Demographics",
            "x_field": "age_group",
            "y_axis": [{"y_field": "patient_count", "color": "#5E64FF"}]
        },
        {
            "name": "Top Procedures Revenue",
            "chart_type": "Bar",
            "source": "Treatment Success Metrics",
            "x_field": "procedure_name",
            "y_axis": [{"y_field": "total_revenue", "color": "#FF6B6B"}],
            "filters_json": '{"limit": 10}'
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
    """Get chart configurations for Clinical Dashboard"""
    return [
        {
            "name": "Treatment Success Rates",
            "chart_type": "Bar",
            "source": "Treatment Success Metrics",
            "x_field": "procedure_name",
            "y_axis": [{"y_field": "success_rate", "color": "#36C6AF"}]
        },
        {
            "name": "Emergency Treatments Trend",
            "chart_type": "Line",
            "timeseries": 1,
            "source": "Emergency Treatments",
            "x_field": "date",
            "y_axis": [{"y_field": "emergency_count", "color": "#FF6B6B"}]
        },
        {
            "name": "Procedure Categories",
            "chart_type": "Donut",
            "source": "Treatment Success Metrics",
            "x_field": "procedure_category",
            "y_axis": [{"y_field": "procedure_count", "color": "#4ECDC4"}]
        },
        {
            "name": "Complication Rates",
            "chart_type": "Bar",
            "source": "Treatment Success Metrics",
            "x_field": "procedure_name",
            "y_axis": [{"y_field": "complication_rate", "color": "#FFA726"}],
            "filters_json": '{"show_complications": 1}'
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
    """Get chart configurations for Financial Dashboard"""
    return [
        {
            "name": "Revenue by Payment Method",
            "chart_type": "Donut",
            "source": "Revenue Analysis",
            "x_field": "payment_method",
            "y_axis": [{"y_field": "amount", "color": "#36C6AF"}]
        },
        {
            "name": "Collection Efficiency Trend",
            "chart_type": "Line",
            "timeseries": 1,
            "source": "Revenue Analysis",
            "x_field": "period",
            "y_axis": [{"y_field": "collection_rate", "color": "#5E64FF"}]
        },
        {
            "name": "Outstanding Balances Aging",
            "chart_type": "Bar",
            "source": "Outstanding Balances",
            "x_field": "aging_period",
            "y_axis": [{"y_field": "balance_amount", "color": "#FF6B6B"}]
        },
        {
            "name": "Insurance vs Cash Revenue",
            "chart_type": "Line",
            "timeseries": 1,
            "source": "Revenue Analysis",
            "x_field": "period",
            "y_axis": [
                {"y_field": "insurance_revenue", "color": "#36C6AF"},
                {"y_field": "cash_revenue", "color": "#5E64FF"}
            ]
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
    """Get chart configurations for Operational Dashboard"""
    return [
        {
            "name": "Daily Appointment Status",
            "chart_type": "Donut",
            "source": "Daily Operations",
            "x_field": "appointment_status",
            "y_axis": [{"y_field": "count", "color": "#4ECDC4"}]
        },
        {
            "name": "Practitioner Utilization",
            "chart_type": "Bar",
            "source": "Practitioner Utilization",
            "x_field": "practitioner",
            "y_axis": [{"y_field": "utilization_rate", "color": "#36C6AF"}]
        },
        {
            "name": "Hourly Patient Flow",
            "chart_type": "Line",
            "source": "Patient Flow",
            "x_field": "hour",
            "y_axis": [{"y_field": "patient_count", "color": "#5E64FF"}]
        },
        {
            "name": "Weekly Capacity Utilization",
            "chart_type": "Bar",
            "source": "Capacity Analysis",
            "x_field": "day_of_week",
            "y_axis": [{"y_field": "utilization_percentage", "color": "#FFA726"}]
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

def get_dashboard_chart_data(chart_name, filters=None):
    """Get data for specific dashboard chart"""
    if not filters:
        filters = {}
    
    # Map chart names to data functions
    chart_data_map = {
        "Monthly Revenue Trend": get_revenue_trend_data,
        "Patient Demographics": get_patient_demographics_data,
        "Top Procedures Revenue": get_top_procedures_data,
        "Treatment Success Rates": get_treatment_success_data,
        "Emergency Treatments Trend": get_emergency_treatments_data,
        "Procedure Categories": get_procedure_categories_data,
        "Complication Rates": get_complication_rates_data,
        "Revenue by Payment Method": get_payment_method_data,
        "Collection Efficiency Trend": get_collection_efficiency_data,
        "Outstanding Balances Aging": get_outstanding_balances_data,
        "Insurance vs Cash Revenue": get_insurance_cash_data,
        "Daily Appointment Status": get_daily_appointments_data,
        "Practitioner Utilization": get_practitioner_utilization_data,
        "Hourly Patient Flow": get_patient_flow_data,
        "Weekly Capacity Utilization": get_capacity_utilization_data
    }
    
    data_function = chart_data_map.get(chart_name)
    if data_function:
        return data_function(filters)
    
    return {"labels": [], "datasets": []}

# Chart Data Functions
def get_revenue_trend_data(filters):
    """Get revenue trend data for charts"""
    from dentcharts.dentcharts.report.revenue_analysis.revenue_analysis import execute
    
    # Set default date range if not provided
    if not filters.get('from_date'):
        filters['from_date'] = add_months(getdate(), -12)
    if not filters.get('to_date'):
        filters['to_date'] = getdate()
    
    columns, data = execute(filters)
    
    labels = [row[0] for row in data if row[0]]  # Period column
    values = [flt(row[1]) for row in data if row[1]]  # Revenue column
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Revenue",
            "values": values,
            "chartType": "line"
        }]
    }

def get_patient_demographics_data(filters):
    """Get patient demographics data for donut chart"""
    from dentcharts.dentcharts.report.patient_demographics.patient_demographics import execute
    
    if not filters.get('from_date'):
        filters['from_date'] = add_months(getdate(), -12)
    if not filters.get('to_date'):
        filters['to_date'] = getdate()
    
    columns, data = execute(filters)
    
    labels = [row[0] for row in data if row[0]]  # Age group column
    values = [cint(row[2]) for row in data if row[2]]  # Patient count column
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Patients",
            "values": values,
            "chartType": "donut"
        }]
    }

def get_top_procedures_data(filters):
    """Get top procedures by revenue"""
    from dentcharts.dentcharts.report.treatment_success_metrics.treatment_success_metrics import execute
    
    if not filters.get('from_date'):
        filters['from_date'] = add_months(getdate(), -6)
    if not filters.get('to_date'):
        filters['to_date'] = getdate()
    
    columns, data = execute(filters)
    
    # Sort by revenue and take top 10
    sorted_data = sorted(data, key=lambda x: flt(x[6]) if len(x) > 6 else 0, reverse=True)[:10]
    
    labels = [row[0] for row in sorted_data if row[0]]  # Procedure name
    values = [flt(row[6]) for row in sorted_data if len(row) > 6]  # Revenue column
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Revenue",
            "values": values,
            "chartType": "bar"
        }]
    }

def get_treatment_success_data(filters):
    """Get treatment success rates"""
    from dentcharts.dentcharts.report.treatment_success_metrics.treatment_success_metrics import execute
    
    if not filters.get('from_date'):
        filters['from_date'] = add_months(getdate(), -6)
    if not filters.get('to_date'):
        filters['to_date'] = getdate()
    
    columns, data = execute(filters)
    
    labels = [row[0] for row in data if row[0]]  # Procedure name
    values = [flt(row[3]) for row in data if len(row) > 3]  # Success rate column
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Success Rate (%)",
            "values": values,
            "chartType": "bar"
        }]
    }

def get_emergency_treatments_data(filters):
    """Get emergency treatments trend"""
    # This would need to be implemented based on your emergency treatment tracking
    # For now, return sample data
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "datasets": [{
            "name": "Emergency Cases",
            "values": [12, 8, 15, 6, 10, 14],
            "chartType": "line"
        }]
    }

def get_procedure_categories_data(filters):
    """Get procedure categories distribution"""
    data = frappe.db.sql("""
        SELECT 
            dpm.procedure_category,
            COUNT(tp.name) as procedure_count
        FROM `tabTooth Procedure` tp
        JOIN `tabDental Procedure Master` dpm ON tp.procedure = dpm.name
        WHERE tp.status = 'Completed'
        AND tp.completion_date BETWEEN %s AND %s
        GROUP BY dpm.procedure_category
        ORDER BY procedure_count DESC
    """, (filters.get('from_date', add_months(getdate(), -6)), 
          filters.get('to_date', getdate())), as_dict=True)
    
    labels = [row.procedure_category for row in data]
    values = [row.procedure_count for row in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Procedures",
            "values": values,
            "chartType": "donut"
        }]
    }

def get_complication_rates_data(filters):
    """Get complication rates by procedure"""
    # This would need to be implemented based on your complication tracking
    # For now, return sample data
    return {
        "labels": ["Root Canal", "Extraction", "Crown", "Filling", "Cleaning"],
        "datasets": [{
            "name": "Complication Rate (%)",
            "values": [2.1, 1.5, 0.8, 0.3, 0.1],
            "chartType": "bar"
        }]
    }

def get_payment_method_data(filters):
    """Get revenue by payment method"""
    data = frappe.db.sql("""
        SELECT 
            pe.mode_of_payment,
            SUM(pe.paid_amount) as amount
        FROM `tabPayment Entry` pe
        WHERE pe.docstatus = 1
        AND pe.posting_date BETWEEN %s AND %s
        GROUP BY pe.mode_of_payment
        ORDER BY amount DESC
    """, (filters.get('from_date', add_months(getdate(), -3)), 
          filters.get('to_date', getdate())), as_dict=True)
    
    labels = [row.mode_of_payment or 'Unknown' for row in data]
    values = [flt(row.amount) for row in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Amount",
            "values": values,
            "chartType": "donut"
        }]
    }

def get_collection_efficiency_data(filters):
    """Get collection efficiency trend"""
    # This would calculate collection efficiency over time
    # For now, return sample data
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "datasets": [{
            "name": "Collection Rate (%)",
            "values": [92.5, 94.2, 91.8, 93.6, 95.1, 94.7],
            "chartType": "line"
        }]
    }

def get_outstanding_balances_data(filters):
    """Get outstanding balances by aging"""
    # This would need to be implemented based on your payment tracking
    # For now, return sample data
    return {
        "labels": ["0-30 days", "31-60 days", "61-90 days", "90+ days"],
        "datasets": [{
            "name": "Outstanding Amount",
            "values": [15420, 8750, 4320, 2180],
            "chartType": "bar"
        }]
    }

def get_insurance_cash_data(filters):
    """Get insurance vs cash revenue trend"""
    # This would need to be implemented based on your payment tracking
    # For now, return sample data
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "datasets": [
            {
                "name": "Insurance Revenue",
                "values": [18500, 21200, 19800, 22100, 24300, 23800],
                "chartType": "line"
            },
            {
                "name": "Cash Revenue", 
                "values": [12400, 14100, 13200, 15800, 16900, 17200],
                "chartType": "line"
            }
        ]
    }

def get_daily_appointments_data(filters):
    """Get today's appointment status"""
    today = getdate()
    data = frappe.db.sql("""
        SELECT 
            da.status,
            COUNT(*) as count
        FROM `tabDental Appointment` da
        WHERE DATE(da.appointment_date) = %s
        GROUP BY da.status
    """, (today,), as_dict=True)
    
    labels = [row.status for row in data]
    values = [row.count for row in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Appointments",
            "values": values,
            "chartType": "donut"
        }]
    }

def get_practitioner_utilization_data(filters):
    """Get practitioner utilization rates"""
    # This would calculate utilization based on scheduled vs available time
    # For now, return sample data
    return {
        "labels": ["Dr. Smith", "Dr. Johnson", "Dr. Brown", "Dr. Davis"],
        "datasets": [{
            "name": "Utilization Rate (%)",
            "values": [87.5, 92.3, 78.9, 85.1],
            "chartType": "bar"
        }]
    }

def get_patient_flow_data(filters):
    """Get hourly patient flow"""
    # This would track patient check-ins by hour
    # For now, return sample data
    return {
        "labels": ["8 AM", "9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM"],
        "datasets": [{
            "name": "Patient Count",
            "values": [3, 8, 12, 15, 8, 10, 14, 12, 9, 4],
            "chartType": "line"
        }]
    }

def get_capacity_utilization_data(filters):
    """Get weekly capacity utilization"""
    # This would calculate capacity utilization by day of week
    # For now, return sample data
    return {
        "labels": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "datasets": [{
            "name": "Utilization (%)",
            "values": [85.2, 92.7, 88.4, 91.3, 87.9, 76.5],
            "chartType": "bar"
        }]
    } 