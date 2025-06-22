# -*- coding: utf-8 -*-
# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

"""
Executive Dashboard Web Page Controller
Handles data fetching and page rendering for the Executive Dashboard
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_months
from frappe.website.utils import get_comment_list
from dentcharts.dentcharts.dashboard_utils import get_executive_dashboard_data

def get_context(context):
    """Get context data for Executive Dashboard page"""
    try:
        # Check if user has permission to view dashboard
        if not frappe.has_permission("Dashboard"):
            frappe.throw(_("Not permitted to view dashboards"), frappe.PermissionError)
        
        # Set page metadata
        context.title = _("Executive Dashboard")
        context.show_sidebar = False
        context.no_breadcrumbs = True
        context.no_header = True
        
        # Get current date range (last month to today)
        today = getdate()
        last_month = add_months(today, -1)
        
        # Fetch dashboard data
        dashboard_data = get_executive_dashboard_data(last_month, today)
        
        if dashboard_data and dashboard_data.get("success"):
            context.dashboard_data = dashboard_data.get("data", {})
            context.data_loaded = True
        else:
            context.dashboard_data = {}
            context.data_loaded = False
            context.error_message = dashboard_data.get("error", "Failed to load dashboard data")
        
        # Set date range for display
        context.date_range = {
            "from_date": last_month,
            "to_date": today
        }
        
        # Add user info
        context.user = frappe.session.user
        context.user_roles = frappe.get_roles()
        
        # Add navigation items
        context.nav_items = get_dashboard_navigation()
        
        return context
        
    except Exception as e:
        frappe.log_error(f"Executive Dashboard Context Error: {str(e)}")
        context.error_message = str(e)
        context.data_loaded = False
        return context

def get_dashboard_navigation():
    """Get navigation items for dashboard switcher"""
    return [
        {
            "label": _("Executive Dashboard"),
            "url": "/executive_dashboard",
            "active": True,
            "icon": "📊"
        },
        {
            "label": _("Clinical Dashboard"),
            "url": "/clinical_dashboard",
            "active": False,
            "icon": "🏥"
        },
        {
            "label": _("Financial Dashboard"),
            "url": "/financial_dashboard",
            "active": False,
            "icon": "💰"
        },
        {
            "label": _("Operational Dashboard"),
            "url": "/operational_dashboard",
            "active": False,
            "icon": "⚙️"
        }
    ]

@frappe.whitelist()
def get_dashboard_summary():
    """Get high-level dashboard summary for quick overview"""
    try:
        today = getdate()
        last_month = add_months(today, -1)
        
        # Get executive dashboard data
        dashboard_data = get_executive_dashboard_data(last_month, today)
        
        if dashboard_data and dashboard_data.get("success"):
            data = dashboard_data.get("data", {})
            
            # Extract key metrics
            revenue = data.get("revenue", {})
            patients = data.get("patients", {})
            treatments = data.get("treatments", {})
            collections = data.get("collections", {})
            
            summary = {
                "total_revenue": revenue.get("total_revenue", 0),
                "revenue_growth": revenue.get("growth_rate", 0),
                "active_patients": patients.get("active_patients", 0),
                "new_patients": patients.get("new_patients", 0),
                "treatment_success_rate": treatments.get("success_rate", 0),
                "collection_rate": collections.get("collection_rate", 0),
                "total_billed": collections.get("total_billed", 0),
                "total_outstanding": collections.get("total_outstanding", 0)
            }
            
            return {
                "success": True,
                "data": summary,
                "period": {
                    "from_date": str(last_month),
                    "to_date": str(today)
                }
            }
        else:
            return {
                "success": False,
                "error": dashboard_data.get("error", "Failed to fetch dashboard data")
            }
            
    except Exception as e:
        frappe.log_error(f"Dashboard Summary Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_chart_data(chart_type, filters=None):
    """Get specific chart data for AJAX requests"""
    try:
        if not filters:
            filters = {}
        
        today = getdate()
        from_date = filters.get("from_date", add_months(today, -12))
        to_date = filters.get("to_date", today)
        
        if chart_type == "revenue_trend":
            return get_revenue_trend_data(from_date, to_date)
        elif chart_type == "patient_demographics":
            return get_patient_demographics_data()
        elif chart_type == "treatment_success":
            return get_treatment_success_data(from_date, to_date)
        elif chart_type == "collection_efficiency":
            return get_collection_efficiency_data(from_date, to_date)
        else:
            return {"success": False, "error": "Invalid chart type"}
            
    except Exception as e:
        frappe.log_error(f"Chart Data Error: {str(e)}")
        return {"success": False, "error": str(e)}

def get_revenue_trend_data(from_date, to_date):
    """Get revenue trend data for line chart"""
    try:
        data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%%Y-%%m') as month,
                SUM(grand_total) as revenue,
                COUNT(*) as invoice_count
            FROM `tabInvoice`
            WHERE posting_date BETWEEN %s AND %s
            AND docstatus = 1
            GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
            ORDER BY month
        """, (from_date, to_date), as_dict=1)
        
        labels = []
        values = []
        
        for item in data:
            labels.append(item.get('month'))
            values.append(float(item.get('revenue', 0)))
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Revenue",
                    "data": values,
                    "borderColor": "#36C6AF",
                    "backgroundColor": "rgba(54, 198, 175, 0.1)",
                    "fill": True
                }]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_patient_demographics_data():
    """Get patient demographics data for donut chart"""
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
        
        labels = []
        values = []
        colors = ['#36C6AF', '#5E64FF', '#FF6B6B', '#4ECDC4', '#FFA726']
        
        for i, item in enumerate(data):
            labels.append(item.get('age_group'))
            values.append(int(item.get('count', 0)))
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": colors[:len(values)]
                }]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_treatment_success_data(from_date, to_date):
    """Get treatment success data for bar chart"""
    try:
        data = frappe.db.sql("""
            SELECT 
                tpi.procedure_name,
                COUNT(*) as total_count,
                SUM(CASE WHEN tpi.status = 'Completed' THEN 1 ELSE 0 END) as completed_count
            FROM `tabTreatment Plan Item` tpi
            INNER JOIN `tabTreatment Plan` tp ON tpi.parent = tp.name
            WHERE tp.creation BETWEEN %s AND %s
            GROUP BY tpi.procedure_name
            HAVING total_count >= 3
            ORDER BY completed_count DESC
            LIMIT 10
        """, (from_date, to_date), as_dict=1)
        
        labels = []
        values = []
        colors = ['#36C6AF', '#5E64FF', '#FF6B6B', '#4ECDC4', '#FFA726']
        
        for item in data:
            total = int(item.get('total_count', 0))
            completed = int(item.get('completed_count', 0))
            success_rate = (completed / total * 100) if total > 0 else 0
            
            labels.append(item.get('procedure_name'))
            values.append(round(success_rate, 1))
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Success Rate (%)",
                    "data": values,
                    "backgroundColor": colors[:len(values)]
                }]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_collection_efficiency_data(from_date, to_date):
    """Get collection efficiency data for pie chart"""
    try:
        data = frappe.db.sql("""
            SELECT 
                pe.mode_of_payment,
                SUM(pe.paid_amount) as amount
            FROM `tabPayment Entry` pe
            WHERE pe.posting_date BETWEEN %s AND %s
            AND pe.docstatus = 1
            GROUP BY pe.mode_of_payment
            ORDER BY amount DESC
        """, (from_date, to_date), as_dict=1)
        
        labels = []
        values = []
        colors = ['#36C6AF', '#5E64FF', '#FF6B6B', '#4ECDC4', '#FFA726']
        
        for item in data:
            labels.append(item.get('mode_of_payment'))
            values.append(float(item.get('amount', 0)))
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": colors[:len(values)]
                }]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)} 