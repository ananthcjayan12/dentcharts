# Copyright (c) 2024, Healthcare and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_months, formatdate
from datetime import datetime, timedelta
import calendar


def execute(filters=None):
    """
    Revenue Analysis Report
    
    Provides comprehensive revenue analysis including:
    - Period-wise revenue trends
    - Payment method breakdown  
    - Collection efficiency
    - Outstanding balances analysis
    """
    if not filters:
        filters = {}
    
    # Set default dates if not provided
    if not filters.get("from_date"):
        filters["from_date"] = add_months(getdate(), -12)
    if not filters.get("to_date"):
        filters["to_date"] = getdate()
    
    columns = get_columns()
    data = get_data(filters)
    chart_data = get_chart_data(data, filters)
    
    return columns, data, None, chart_data


def get_columns():
    """Define report columns"""
    return [
        {
            "label": _("Period"),
            "fieldname": "period",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Total Revenue"),
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Invoices"),
            "fieldname": "invoice_count", 
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Avg Invoice"),
            "fieldname": "avg_invoice_value",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Cash Revenue"),
            "fieldname": "cash_revenue",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Insurance Revenue"),
            "fieldname": "insurance_revenue",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Outstanding"),
            "fieldname": "outstanding_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Collection Rate"),
            "fieldname": "collection_rate",
            "fieldtype": "Percent",
            "width": 130
        }
    ]


def get_data(filters):
    """Get revenue analysis data"""
    period_type = filters.get("period_type", "Monthly")
    conditions = get_conditions(filters)
    
    # Determine date format based on period type
    if period_type == "Monthly":
        date_format = "%Y-%m"
        period_label = "Month"
    elif period_type == "Weekly":
        date_format = "%Y-%u" 
        period_label = "Week"
    else:  # Daily
        date_format = "%Y-%m-%d"
        period_label = "Date"
    
    # Main revenue query
    revenue_data = frappe.db.sql(f"""
        SELECT 
            DATE_FORMAT(i.posting_date, '{date_format}') as period,
            SUM(i.grand_total) as total_revenue,
            COUNT(i.name) as invoice_count,
            AVG(i.grand_total) as avg_invoice_value,
            SUM(i.outstanding_amount) as outstanding_amount
        FROM `tabInvoice` i
        WHERE i.docstatus = 1 
        AND i.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {conditions}
        GROUP BY DATE_FORMAT(i.posting_date, '{date_format}')
        ORDER BY period
    """, {
        'from_date': filters.get('from_date'),
        'to_date': filters.get('to_date')
    }, as_dict=True)
    
    # Get payment method breakdown
    payment_data = get_payment_breakdown(filters, date_format)
    
    # Merge data
    result = []
    for row in revenue_data:
        period_payments = payment_data.get(row.period, {})
        
        cash_revenue = period_payments.get('cash', 0)
        insurance_revenue = period_payments.get('insurance', 0)
        
        # Calculate collection rate
        total_billed = row.total_revenue
        total_collected = total_billed - row.outstanding_amount
        collection_rate = (total_collected / total_billed * 100) if total_billed else 0
        
        # Format period display
        period_display = format_period_display(row.period, period_type)
        
        result.append({
            'period': period_display,
            'total_revenue': flt(row.total_revenue, 2),
            'invoice_count': cint(row.invoice_count),
            'avg_invoice_value': flt(row.avg_invoice_value, 2),
            'cash_revenue': flt(cash_revenue, 2),
            'insurance_revenue': flt(insurance_revenue, 2),
            'outstanding_amount': flt(row.outstanding_amount, 2),
            'collection_rate': flt(collection_rate, 1)
        })
    
    # Add summary row
    if result:
        total_revenue = sum(r['total_revenue'] for r in result)
        total_invoices = sum(r['invoice_count'] for r in result)
        total_cash = sum(r['cash_revenue'] for r in result)
        total_insurance = sum(r['insurance_revenue'] for r in result)
        total_outstanding = sum(r['outstanding_amount'] for r in result)
        
        avg_collection_rate = sum(r['collection_rate'] for r in result) / len(result) if result else 0
        
        result.append({
            'period': '<b>Total</b>',
            'total_revenue': total_revenue,
            'invoice_count': total_invoices,
            'avg_invoice_value': total_revenue / total_invoices if total_invoices else 0,
            'cash_revenue': total_cash,
            'insurance_revenue': total_insurance,
            'outstanding_amount': total_outstanding,
            'collection_rate': avg_collection_rate
        })
    
    return result


def get_payment_breakdown(filters, date_format):
    """Get payment method breakdown by period"""
    try:
        payment_data = frappe.db.sql(f"""
            SELECT 
                DATE_FORMAT(pe.posting_date, '{date_format}') as period,
                CASE 
                    WHEN pe.mode_of_payment IN ('Cash', 'Check') THEN 'cash'
                    ELSE 'insurance'
                END as payment_type,
                SUM(pe.paid_amount) as amount
            FROM `tabPayment Entry` pe
            WHERE pe.docstatus = 1
            AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND pe.party_type = 'Customer'
            GROUP BY period, payment_type
        """, {
            'from_date': filters.get('from_date'),
            'to_date': filters.get('to_date')
        }, as_dict=True)
        
        # Organize by period
        result = {}
        for row in payment_data:
            if row.period not in result:
                result[row.period] = {}
            result[row.period][row.payment_type] = row.amount
            
        return result
        
    except Exception:
        # If Payment Entry structure is different, return empty dict
        return {}


def get_conditions(filters):
    """Build WHERE conditions based on filters"""
    conditions = []
    
    if filters.get("clinic"):
        # Add clinic condition if needed
        pass
    
    if filters.get("practitioner"):
        conditions.append(f"""
            EXISTS (
                SELECT 1 FROM `tabDental Appointment` da 
                WHERE da.patient = i.patient 
                AND da.practitioner = '{filters.get('practitioner')}'
                AND da.appointment_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'
            )
        """)
    
    return " AND " + " AND ".join(conditions) if conditions else ""


def format_period_display(period, period_type):
    """Format period for display"""
    try:
        if period_type == "Monthly":
            # Convert YYYY-MM to Month Year
            year, month = period.split('-')
            month_name = calendar.month_name[int(month)]
            return f"{month_name} {year}"
        elif period_type == "Weekly":
            # Convert YYYY-WW to Week format
            year, week = period.split('-')
            return f"Week {week}, {year}"
        else:  # Daily
            # Convert YYYY-MM-DD to readable date
            return formatdate(period)
    except:
        return period


def get_chart_data(data, filters):
    """Generate chart data for visualization"""
    if not data or len(data) <= 1:  # Skip if no data or only total row
        return None
    
    # Remove total row for chart
    chart_data = [row for row in data if not row.get('period', '').startswith('<b>')]
    
    if not chart_data:
        return None
    
    periods = [row['period'] for row in chart_data]
    revenues = [row['total_revenue'] for row in chart_data]
    
    return {
        "data": {
            "labels": periods,
            "datasets": [
                {
                    "name": "Total Revenue",
                    "values": revenues
                }
            ]
        },
        "type": "line",
        "height": 300,
        "colors": ["#5e64ff"]
    }


def get_revenue_summary_data(filters=None):
    """
    Helper function to get revenue summary statistics
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
        summary = frappe.db.sql(f"""
            SELECT 
                SUM(i.grand_total) as total_revenue,
                COUNT(i.name) as total_invoices,
                AVG(i.grand_total) as avg_invoice_value,
                SUM(i.outstanding_amount) as total_outstanding,
                SUM(CASE WHEN i.outstanding_amount = 0 THEN i.grand_total ELSE 0 END) as collected_amount
            FROM `tabInvoice` i
            WHERE i.docstatus = 1
            AND i.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {conditions}
        """, {
            'from_date': filters.get('from_date'),
            'to_date': filters.get('to_date')
        }, as_dict=True)
        
        if summary and summary[0]:
            result = summary[0]
            # Calculate collection rate
            if result.total_revenue:
                result.collection_rate = ((result.total_revenue - result.total_outstanding) / result.total_revenue) * 100
            else:
                result.collection_rate = 0
            
            return result
            
    except Exception as e:
        frappe.log_error(f"Error in revenue summary: {str(e)}")
    
    return {
        'total_revenue': 0,
        'total_invoices': 0,
        'avg_invoice_value': 0,
        'total_outstanding': 0,
        'collected_amount': 0,
        'collection_rate': 0
    }


def get_top_procedures_by_revenue(filters=None, limit=10):
    """
    Get top procedures by revenue
    Used by other reports and dashboards
    """
    if not filters:
        filters = {}
    
    try:
        top_procedures = frappe.db.sql("""
            SELECT 
                dpm.procedure_name,
                COUNT(tp.name) as procedure_count,
                SUM(tp.actual_cost) as total_revenue,
                AVG(tp.actual_cost) as avg_cost
            FROM `tabTooth Procedure` tp
            JOIN `tabDental Procedure Master` dpm ON tp.procedure = dpm.name
            WHERE tp.status = 'Completed'
            AND tp.completion_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY dpm.procedure_name
            ORDER BY total_revenue DESC
            LIMIT %(limit)s
        """, {
            'from_date': filters.get('from_date', add_months(getdate(), -12)),
            'to_date': filters.get('to_date', getdate()),
            'limit': limit
        }, as_dict=True)
        
        return top_procedures
        
    except Exception:
        return [] 