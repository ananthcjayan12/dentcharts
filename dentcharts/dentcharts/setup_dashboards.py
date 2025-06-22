# -*- coding: utf-8 -*-
# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

"""
Dashboard Setup Script for Dental ERP
Creates all dashboards, charts, and number cards programmatically
"""

import frappe
from frappe import _
from frappe.utils import getdate

def setup_all_dashboards():
    """Setup all dashboards for the Dental ERP system"""
    try:
        # Create dashboards in order
        create_executive_dashboard()
        create_clinical_dashboard()
        create_financial_dashboard()
        create_operational_dashboard()
        
        frappe.db.commit()
        print("✅ All dashboards created successfully!")
        return True
        
    except Exception as e:
        frappe.log_error(f"Dashboard Setup Error: {str(e)}")
        print(f"❌ Dashboard setup failed: {str(e)}")
        return False

def create_executive_dashboard():
    """Create Executive Dashboard with charts and number cards"""
    try:
        # Check if dashboard already exists
        if frappe.db.exists("Dashboard", "Executive Dashboard"):
            print("📊 Executive Dashboard already exists, updating...")
            dashboard = frappe.get_doc("Dashboard", "Executive Dashboard")
        else:
            print("📊 Creating Executive Dashboard...")
            dashboard = frappe.new_doc("Dashboard")
            dashboard.dashboard_name = "Executive Dashboard"
        
        # Configure dashboard properties
        dashboard.module = "Dentcharts"
        dashboard.is_default = 1
        dashboard.color = "#36C6AF"
        
        # Clear existing charts and number cards
        dashboard.dashboard_charts = []
        dashboard.number_cards = []
        
        # Add Number Cards (KPIs)
        number_cards = [
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Total Revenue",
                "label": "Total Revenue",
                "function": "Sum",
                "aggregate_function_based_on": "grand_total",
                "document_type_based_on": "Invoice",
                "filters_json": '{"docstatus": 1}',
                "stats_time_interval": "Monthly",
                "color": "#36C6AF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card", 
                "card_name": "Active Patients",
                "label": "Active Patients",
                "function": "Count",
                "document_type_based_on": "Dental Patient",
                "filters_json": '{}',
                "stats_time_interval": "Monthly",
                "color": "#5E64FF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Collection Rate",
                "label": "Collection Rate",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Monthly", 
                "color": "#4ECDC4",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Treatment Success",
                "label": "Treatment Success",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Monthly",
                "color": "#FF6B6B", 
                "width": 3
            }
        ]
        
        # Add number cards to dashboard
        for card_data in number_cards:
            dashboard.append("number_cards", card_data)
        
        # Add Charts
        charts = [
            {
                "chart": "Monthly Revenue Trend",
                "width": "Half"
            },
            {
                "chart": "Patient Demographics", 
                "width": "Half"
            },
            {
                "chart": "Treatment Success Rate",
                "width": "Half"
            },
            {
                "chart": "Collection Efficiency",
                "width": "Half"
            }
        ]
        
        # Add charts to dashboard
        for chart_data in charts:
            dashboard.append("dashboard_charts", chart_data)
        
        # Save dashboard
        dashboard.save()
        print("✅ Executive Dashboard created successfully!")
        
        # Create associated charts
        create_executive_dashboard_charts()
        
    except Exception as e:
        frappe.log_error(f"Executive Dashboard Creation Error: {str(e)}")
        print(f"❌ Executive Dashboard creation failed: {str(e)}")

def create_executive_dashboard_charts():
    """Create charts for Executive Dashboard"""
    try:
        charts_config = [
            {
                "chart_name": "Monthly Revenue Trend",
                "chart_type": "Line",
                "document_type": "Invoice",
                "based_on": "posting_date",
                "value_based_on": "grand_total",
                "number_of_groups": 0,
                "filters_json": '{"docstatus": 1}',
                "timeseries": 1,
                "time_interval": "Monthly",
                "timespan": "Last Year",
                "color": "#36C6AF",
                "module": "Dentcharts"
            },
            {
                "chart_name": "Patient Demographics",
                "chart_type": "Donut", 
                "document_type": "Dental Patient",
                "based_on": "creation",
                "number_of_groups": 0,
                "filters_json": '{}',
                "timeseries": 0,
                "color": "#5E64FF",
                "module": "Dentcharts"
            },
            {
                "chart_name": "Treatment Success Rate",
                "chart_type": "Bar",
                "document_type": "Treatment Plan",
                "based_on": "status",
                "number_of_groups": 0,
                "filters_json": '{}',
                "timeseries": 0,
                "color": "#FF6B6B",
                "module": "Dentcharts"
            },
            {
                "chart_name": "Collection Efficiency",
                "chart_type": "Percentage",
                "document_type": "Invoice",
                "based_on": "posting_date",
                "value_based_on": "grand_total",
                "number_of_groups": 0,
                "filters_json": '{"docstatus": 1}',
                "timeseries": 0,
                "color": "#4ECDC4",
                "module": "Dentcharts"
            }
        ]
        
        for chart_config in charts_config:
            chart_name = chart_config["chart_name"]
            
            # Check if chart already exists
            if frappe.db.exists("Dashboard Chart", chart_name):
                print(f"📈 Chart '{chart_name}' already exists, updating...")
                chart = frappe.get_doc("Dashboard Chart", chart_name)
            else:
                print(f"📈 Creating chart '{chart_name}'...")
                chart = frappe.new_doc("Dashboard Chart")
                chart.chart_name = chart_name
            
            # Update chart properties
            for key, value in chart_config.items():
                if key != "chart_name":
                    setattr(chart, key, value)
            
            chart.save()
            print(f"✅ Chart '{chart_name}' created successfully!")
            
    except Exception as e:
        frappe.log_error(f"Executive Dashboard Charts Creation Error: {str(e)}")
        print(f"❌ Executive Dashboard charts creation failed: {str(e)}")

def create_clinical_dashboard():
    """Create Clinical Dashboard"""
    try:
        # Check if dashboard already exists
        if frappe.db.exists("Dashboard", "Clinical Dashboard"):
            print("📊 Clinical Dashboard already exists, updating...")
            dashboard = frappe.get_doc("Dashboard", "Clinical Dashboard")
        else:
            print("📊 Creating Clinical Dashboard...")
            dashboard = frappe.new_doc("Dashboard")
            dashboard.dashboard_name = "Clinical Dashboard"
        
        # Configure dashboard properties
        dashboard.module = "Dentcharts"
        dashboard.is_default = 0
        dashboard.color = "#5E64FF"
        
        # Clear existing charts and number cards
        dashboard.dashboard_charts = []
        dashboard.number_cards = []
        
        # Add Number Cards
        number_cards = [
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Treatment Success Rate",
                "label": "Treatment Success Rate",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Monthly",
                "color": "#36C6AF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Emergency Cases",
                "label": "Emergency Cases", 
                "function": "Count",
                "document_type_based_on": "Treatment Plan",
                "filters_json": '{"is_emergency": 1}',
                "stats_time_interval": "Monthly",
                "color": "#FF6B6B",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Average Duration",
                "label": "Average Duration",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Monthly",
                "color": "#5E64FF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Complication Rate",
                "label": "Complication Rate",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Monthly",
                "color": "#FFA726",
                "width": 3
            }
        ]
        
        # Add number cards to dashboard
        for card_data in number_cards:
            dashboard.append("number_cards", card_data)
        
        # Add Charts
        charts = [
            {
                "chart": "Procedure Success Rates",
                "width": "Full"
            },
            {
                "chart": "Emergency Cases Trend",
                "width": "Half"
            },
            {
                "chart": "Practitioner Performance",
                "width": "Half"
            }
        ]
        
        # Add charts to dashboard
        for chart_data in charts:
            dashboard.append("dashboard_charts", chart_data)
        
        # Save dashboard
        dashboard.save()
        print("✅ Clinical Dashboard created successfully!")
        
    except Exception as e:
        frappe.log_error(f"Clinical Dashboard Creation Error: {str(e)}")
        print(f"❌ Clinical Dashboard creation failed: {str(e)}")

def create_financial_dashboard():
    """Create Financial Dashboard"""
    try:
        # Check if dashboard already exists
        if frappe.db.exists("Dashboard", "Financial Dashboard"):
            print("📊 Financial Dashboard already exists, updating...")
            dashboard = frappe.get_doc("Dashboard", "Financial Dashboard")
        else:
            print("📊 Creating Financial Dashboard...")
            dashboard = frappe.new_doc("Dashboard")
            dashboard.dashboard_name = "Financial Dashboard"
        
        # Configure dashboard properties
        dashboard.module = "Dentcharts"
        dashboard.is_default = 0
        dashboard.color = "#FF6B6B"
        
        # Clear existing charts and number cards
        dashboard.dashboard_charts = []
        dashboard.number_cards = []
        
        # Add Number Cards
        number_cards = [
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Monthly Revenue",
                "label": "Monthly Revenue",
                "function": "Sum",
                "aggregate_function_based_on": "grand_total",
                "document_type_based_on": "Invoice",
                "filters_json": '{"docstatus": 1}',
                "stats_time_interval": "Monthly",
                "color": "#36C6AF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Outstanding Balance",
                "label": "Outstanding Balance",
                "function": "Sum",
                "aggregate_function_based_on": "outstanding_amount",
                "document_type_based_on": "Invoice",
                "filters_json": '{"outstanding_amount": [">", 0]}',
                "stats_time_interval": "Monthly",
                "color": "#FF6B6B",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Insurance Coverage",
                "label": "Insurance Coverage",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Monthly",
                "color": "#5E64FF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Average Invoice",
                "label": "Average Invoice",
                "function": "Average",
                "aggregate_function_based_on": "grand_total",
                "document_type_based_on": "Invoice",
                "filters_json": '{"docstatus": 1}',
                "stats_time_interval": "Monthly",
                "color": "#4ECDC4",
                "width": 3
            }
        ]
        
        # Add number cards to dashboard
        for card_data in number_cards:
            dashboard.append("number_cards", card_data)
        
        # Add Charts
        charts = [
            {
                "chart": "Revenue by Payment Method",
                "width": "Half"
            },
            {
                "chart": "Outstanding Balances Aging",
                "width": "Half"
            },
            {
                "chart": "Monthly Revenue vs Collections",
                "width": "Full"
            }
        ]
        
        # Add charts to dashboard
        for chart_data in charts:
            dashboard.append("dashboard_charts", chart_data)
        
        # Save dashboard
        dashboard.save()
        print("✅ Financial Dashboard created successfully!")
        
    except Exception as e:
        frappe.log_error(f"Financial Dashboard Creation Error: {str(e)}")
        print(f"❌ Financial Dashboard creation failed: {str(e)}")

def create_operational_dashboard():
    """Create Operational Dashboard"""
    try:
        # Check if dashboard already exists
        if frappe.db.exists("Dashboard", "Operational Dashboard"):
            print("📊 Operational Dashboard already exists, updating...")
            dashboard = frappe.get_doc("Dashboard", "Operational Dashboard")
        else:
            print("📊 Creating Operational Dashboard...")
            dashboard = frappe.new_doc("Dashboard")
            dashboard.dashboard_name = "Operational Dashboard"
        
        # Configure dashboard properties
        dashboard.module = "Dentcharts"
        dashboard.is_default = 0
        dashboard.color = "#4ECDC4"
        
        # Clear existing charts and number cards
        dashboard.dashboard_charts = []
        dashboard.number_cards = []
        
        # Add Number Cards
        number_cards = [
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Today's Appointments",
                "label": "Today's Appointments",
                "function": "Count",
                "document_type_based_on": "Dental Appointment",
                "filters_json": f'{{"appointment_date": "{getdate()}"}}',
                "stats_time_interval": "Daily",
                "color": "#36C6AF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Checked In",
                "label": "Checked In",
                "function": "Count",
                "document_type_based_on": "Dental Appointment",
                "filters_json": f'{{"appointment_date": "{getdate()}", "status": ["in", ["In Progress", "Confirmed"]]}}',
                "stats_time_interval": "Daily",
                "color": "#5E64FF",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Running Late",
                "label": "Running Late",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Daily",
                "color": "#FF6B6B",
                "width": 3
            },
            {
                "document_type": "Dashboard Number Card",
                "card_name": "Utilization Rate",
                "label": "Utilization Rate",
                "function": "Custom",
                "filters_json": '{}',
                "stats_time_interval": "Daily",
                "color": "#4ECDC4",
                "width": 3
            }
        ]
        
        # Add number cards to dashboard
        for card_data in number_cards:
            dashboard.append("number_cards", card_data)
        
        # Add Charts
        charts = [
            {
                "chart": "Today's Appointments Status",
                "width": "Half"
            },
            {
                "chart": "Practitioner Utilization",
                "width": "Half"
            },
            {
                "chart": "Weekly Appointment Trend",
                "width": "Full"
            }
        ]
        
        # Add charts to dashboard
        for chart_data in charts:
            dashboard.append("dashboard_charts", chart_data)
        
        # Save dashboard
        dashboard.save()
        print("✅ Operational Dashboard created successfully!")
        
    except Exception as e:
        frappe.log_error(f"Operational Dashboard Creation Error: {str(e)}")
        print(f"❌ Operational Dashboard creation failed: {str(e)}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def delete_existing_dashboards():
    """Delete existing dashboards for clean setup"""
    try:
        dashboard_names = ["Executive Dashboard", "Clinical Dashboard", "Financial Dashboard", "Operational Dashboard"]
        
        for dashboard_name in dashboard_names:
            if frappe.db.exists("Dashboard", dashboard_name):
                frappe.delete_doc("Dashboard", dashboard_name)
                print(f"🗑️ Deleted existing dashboard: {dashboard_name}")
        
        frappe.db.commit()
        print("✅ All existing dashboards deleted!")
        
    except Exception as e:
        frappe.log_error(f"Dashboard Deletion Error: {str(e)}")
        print(f"❌ Dashboard deletion failed: {str(e)}")

def setup_dashboard_permissions():
    """Setup permissions for dashboards"""
    try:
        # Add permissions for System Manager and Clinic Administrator
        roles = ["System Manager", "Healthcare Administrator", "Accounts Manager"]
        
        for role in roles:
            # Dashboard permissions
            if not frappe.db.exists("Custom DocPerm", {"parent": "Dashboard", "role": role}):
                frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "parent": "Dashboard",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                }).insert()
            
            # Dashboard Chart permissions
            if not frappe.db.exists("Custom DocPerm", {"parent": "Dashboard Chart", "role": role}):
                frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "parent": "Dashboard Chart",
                    "parenttype": "DocType", 
                    "parentfield": "permissions",
                    "role": role,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                }).insert()
        
        frappe.db.commit()
        print("✅ Dashboard permissions set up successfully!")
        
    except Exception as e:
        frappe.log_error(f"Dashboard Permissions Error: {str(e)}")
        print(f"❌ Dashboard permissions setup failed: {str(e)}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    setup_all_dashboards()
    setup_dashboard_permissions() 