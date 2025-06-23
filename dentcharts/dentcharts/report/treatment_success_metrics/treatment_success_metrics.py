# Copyright (c) 2024, Healthcare and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_months
from datetime import datetime, timedelta


def execute(filters=None):
    """
    Treatment Success Metrics Report
    
    Provides comprehensive treatment success analysis including:
    - Procedure completion rates
    - Success rate analysis
    - Duration and cost metrics
    - Complication tracking
    """
    if not filters:
        filters = {}
    
    # Set default dates if not provided
    if not filters.get("from_date"):
        filters["from_date"] = add_months(getdate(), -6)
    if not filters.get("to_date"):
        filters["to_date"] = getdate()
    
    columns = get_columns()
    data = get_data(filters)
    chart_data = get_chart_data(data)
    
    return columns, data, None, chart_data


def get_columns():
    """Define report columns"""
    return [
        {
            "label": _("Procedure"),
            "fieldname": "procedure_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Total Procedures"),
            "fieldname": "total_procedures",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": _("Completed"),
            "fieldname": "completed_procedures",
            "fieldtype": "Int",
            "width": 110
        },
        {
            "label": _("Success Rate"),
            "fieldname": "success_rate",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Avg Duration (Days)"),
            "fieldname": "avg_duration_days",
            "fieldtype": "Float",
            "width": 150,
            "precision": 1
        },
        {
            "label": _("Average Cost"),
            "fieldname": "avg_cost",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Total Revenue"),
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Complication Rate"),
            "fieldname": "complication_rate",
            "fieldtype": "Percent",
            "width": 140
        }
    ]


def get_data(filters):
    """Get treatment success metrics data"""
    conditions = get_conditions(filters)
    
    # Main treatment success query - use parameterized query to avoid % conflicts
    query = """
        SELECT 
            dpm.procedure_name,
            dpm.category,
            COUNT(tp.name) as total_procedures,
            SUM(CASE WHEN tp.status = 'Completed' THEN 1 ELSE 0 END) as completed_procedures,
            SUM(CASE WHEN tp.status IN ('Completed', 'In Progress') THEN 1 ELSE 0 END) as active_procedures,
            AVG(CASE 
                WHEN tp.completion_date IS NOT NULL AND tp.planned_date IS NOT NULL 
                THEN DATEDIFF(tp.completion_date, tp.planned_date) 
                ELSE NULL 
            END) as avg_duration_days,
            AVG(COALESCE(tp.actual_cost, tp.estimated_cost, dpm.standard_fee)) as avg_cost,
            SUM(COALESCE(tp.actual_cost, tp.estimated_cost, dpm.standard_fee)) as total_revenue,
            COUNT(CASE WHEN tp.notes LIKE %s OR tp.notes LIKE %s THEN 1 END) as complications
        FROM `tabDental Procedure Master` dpm
        LEFT JOIN `tabTooth Procedure` tp ON dpm.name = tp.procedure
            AND tp.creation BETWEEN %s AND %s
            {conditions}
        GROUP BY dpm.name, dpm.procedure_name, dpm.category
        HAVING total_procedures > 0
        ORDER BY total_procedures DESC
    """.format(conditions=conditions)
    
    treatment_data = frappe.db.sql(query, [
        '%complication%',
        '%problem%',
        filters.get('from_date'),
        filters.get('to_date')
    ], as_dict=True)
    
    # Process data
    result = []
    for row in treatment_data:
        # Calculate success rate
        success_rate = (row.completed_procedures / row.total_procedures * 100) if row.total_procedures else 0
        
        # Calculate complication rate
        complication_rate = (row.complications / row.total_procedures * 100) if row.total_procedures else 0
        
        result.append({
            'procedure_name': row.procedure_name,
            'total_procedures': cint(row.total_procedures),
            'completed_procedures': cint(row.completed_procedures),
            'success_rate': flt(success_rate, 1),
            'avg_duration_days': flt(row.avg_duration_days, 1) if row.avg_duration_days else 0,
            'avg_cost': flt(row.avg_cost, 2),
            'total_revenue': flt(row.total_revenue, 2),
            'complication_rate': flt(complication_rate, 1)
        })
    
    # Add summary row
    if result:
        total_procedures = sum(r['total_procedures'] for r in result)
        total_completed = sum(r['completed_procedures'] for r in result)
        total_revenue = sum(r['total_revenue'] for r in result)
        total_complications = sum(r['complication_rate'] * r['total_procedures'] / 100 for r in result)
        
        # Weighted averages
        avg_duration = sum(r['avg_duration_days'] * r['total_procedures'] for r in result) / total_procedures if total_procedures else 0
        avg_cost = total_revenue / total_procedures if total_procedures else 0
        overall_success_rate = (total_completed / total_procedures * 100) if total_procedures else 0
        overall_complication_rate = (total_complications / total_procedures * 100) if total_procedures else 0
        
        result.append({
            'procedure_name': '<b>Overall</b>',
            'total_procedures': total_procedures,
            'completed_procedures': total_completed,
            'success_rate': flt(overall_success_rate, 1),
            'avg_duration_days': flt(avg_duration, 1),
            'avg_cost': flt(avg_cost, 2),
            'total_revenue': total_revenue,
            'complication_rate': flt(overall_complication_rate, 1)
        })
    
    return result


def get_conditions(filters):
    """Build WHERE conditions based on filters"""
    conditions = []
    
    if filters.get("practitioner"):
        conditions.append("tp.practitioner = '{}'".format(filters.get('practitioner')))
    
    if filters.get("procedure_category"):
        conditions.append("dpm.category = '{}'".format(filters.get('procedure_category')))
    
    return " AND " + " AND ".join(conditions) if conditions else ""


def get_chart_data(data):
    """Generate chart data for visualization"""
    if not data or len(data) <= 1:  # Skip if no data or only total row
        return None
    
    # Remove total row for chart
    chart_data = [row for row in data if not row.get('procedure_name', '').startswith('<b>')]
    
    if not chart_data:
        return None
    
    # Top 10 procedures by volume
    top_procedures = sorted(chart_data, key=lambda x: x['total_procedures'], reverse=True)[:10]
    
    procedure_names = [row['procedure_name'] for row in top_procedures]
    success_rates = [row['success_rate'] for row in top_procedures]
    procedure_counts = [row['total_procedures'] for row in top_procedures]
    
    return {
        "data": {
            "labels": procedure_names,
            "datasets": [
                {
                    "name": "Success Rate (%)",
                    "values": success_rates
                },
                {
                    "name": "Procedure Count",
                    "values": procedure_counts
                }
            ]
        },
        "type": "bar",
        "height": 400,
        "colors": ["#28a745", "#17a2b8"]
    }


def get_treatment_summary_data(filters=None):
    """
    Helper function to get treatment summary statistics
    Used by dashboards and other reports
    """
    if not filters:
        filters = {}
    
    # Set default date range if not provided
    if not filters.get("from_date"):
        filters["from_date"] = add_months(getdate(), -1)
    if not filters.get("to_date"):
        filters["to_date"] = getdate()
    
    conditions = get_conditions(filters)
    
    try:
        query = """
            SELECT 
                COUNT(tp.name) as total_treatments,
                SUM(CASE WHEN tp.status = 'Completed' THEN 1 ELSE 0 END) as completed_treatments,
                SUM(CASE WHEN tp.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_treatments,
                SUM(CASE WHEN tp.status = 'Planned' THEN 1 ELSE 0 END) as planned_treatments,
                AVG(CASE 
                    WHEN tp.completion_date IS NOT NULL AND tp.planned_date IS NOT NULL 
                    THEN DATEDIFF(tp.completion_date, tp.planned_date) 
                    ELSE NULL 
                END) as avg_treatment_duration,
                AVG(COALESCE(tp.actual_cost, tp.estimated_cost)) as avg_treatment_cost,
                COUNT(CASE WHEN tp.notes LIKE %s OR tp.notes LIKE %s THEN 1 END) as complications
            FROM `tabTooth Procedure` tp
            WHERE tp.creation BETWEEN %s AND %s
            {conditions}
        """.format(conditions=conditions)
        
        summary = frappe.db.sql(query, [
            '%complication%',
            '%problem%',
            filters.get('from_date'),
            filters.get('to_date')
        ], as_dict=True)
        
        if summary and summary[0]:
            result = summary[0]
            
            # Calculate rates
            if result.total_treatments:
                result.completion_rate = (result.completed_treatments / result.total_treatments) * 100
                result.complication_rate = (result.complications / result.total_treatments) * 100
            else:
                result.completion_rate = 0
                result.complication_rate = 0
            
            return result
            
    except Exception as e:
        frappe.log_error(f"Error in treatment summary: {str(e)}")
    
    return {
        'total_treatments': 0,
        'completed_treatments': 0,
        'in_progress_treatments': 0,
        'planned_treatments': 0,
        'avg_treatment_duration': 0,
        'avg_treatment_cost': 0,
        'complications': 0,
        'completion_rate': 0,
        'complication_rate': 0
    }


def get_emergency_treatments_data(filters=None):
    """
    Get emergency treatment data
    Used by clinical dashboard
    """
    if not filters:
        filters = {}
    
    try:
        emergency_data = frappe.db.sql("""
            SELECT 
                COUNT(*) as emergency_count,
                AVG(DATEDIFF(tp.completion_date, tp.planned_date)) as avg_response_time
            FROM `tabTooth Procedure` tp
            JOIN `tabDental Procedure Master` dpm ON tp.procedure = dpm.name
            WHERE dpm.category = 'Emergency'
            AND tp.creation BETWEEN %s AND %s
            AND tp.status = 'Completed'
        """, [
            filters.get('from_date', add_months(getdate(), -1)),
            filters.get('to_date', getdate())
        ], as_dict=True)
        
        return emergency_data[0] if emergency_data else {'emergency_count': 0, 'avg_response_time': 0}
        
    except Exception:
        return {'emergency_count': 0, 'avg_response_time': 0}


def get_most_common_conditions(filters=None, limit=10):
    """
    Get most common dental conditions
    Used by various reports and dashboards
    """
    if not filters:
        filters = {}
    
    try:
        conditions = frappe.db.sql("""
            SELECT 
                dcm.condition_name,
                COUNT(tc.name) as condition_count,
                dcm.severity_level
            FROM `tabTooth Condition` tc
            JOIN `tabDental Condition Master` dcm ON tc.condition = dcm.name
            WHERE tc.creation BETWEEN %s AND %s
            GROUP BY dcm.condition_name, dcm.severity_level
            ORDER BY condition_count DESC
            LIMIT %s
        """, [
            filters.get('from_date', add_months(getdate(), -6)),
            filters.get('to_date', getdate()),
            limit
        ], as_dict=True)
        
        return conditions
        
    except Exception:
        return [] 