# Copyright (c) 2024, Healthcare and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_months
from datetime import datetime, timedelta


def execute(filters=None):
    """
    Patient Demographics Report
    
    Provides comprehensive patient demographics analysis including:
    - Age group distribution
    - Gender analysis  
    - New patient acquisition trends
    - Active patient metrics
    """
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    chart_data = get_chart_data(data)
    
    return columns, data, None, chart_data


def get_columns():
    """Define report columns"""
    return [
        {
            "label": _("Age Group"),
            "fieldname": "age_group",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Gender"),
            "fieldname": "gender", 
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Patient Count"),
            "fieldname": "patient_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Percentage"),
            "fieldname": "percentage",
            "fieldtype": "Percent", 
            "width": 120
        },
        {
            "label": _("Average Age"),
            "fieldname": "avg_age",
            "fieldtype": "Float",
            "width": 120,
            "precision": 1
        },
        {
            "label": _("New (6 Months)"),
            "fieldname": "new_patients_last_6m",
            "fieldtype": "Int",
            "width": 140
        },
        {
            "label": _("Active Patients"),
            "fieldname": "active_patients", 
            "fieldtype": "Int",
            "width": 130
        }
    ]


def get_data(filters):
    """Get patient demographics data"""
    conditions = get_conditions(filters)
    
    # Main demographics query
    demographics_data = frappe.db.sql(f"""
        SELECT 
            CASE 
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 < 18 THEN 'Under 18'
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 BETWEEN 18 AND 35 THEN '18-35'
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 BETWEEN 36 AND 55 THEN '36-55'
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 BETWEEN 56 AND 70 THEN '56-70'
                ELSE 'Over 70'
            END as age_group,
            COALESCE(p.sex, 'Unknown') as gender,
            COUNT(*) as patient_count,
            AVG(DATEDIFF(CURDATE(), p.dob) / 365.25) as avg_age
        FROM `tabPatient` p
        INNER JOIN `tabDental Patient` dp ON p.name = dp.healthcare_patient
        WHERE 1=1 {conditions}
        GROUP BY age_group, gender
        ORDER BY 
            CASE age_group
                WHEN 'Under 18' THEN 1
                WHEN '18-35' THEN 2  
                WHEN '36-55' THEN 3
                WHEN '56-70' THEN 4
                ELSE 5
            END,
            gender
    """, as_dict=True)
    
    # Calculate total patients for percentage
    total_patients = sum(row.patient_count for row in demographics_data)
    
    # Get new patients in last 6 months
    six_months_ago = add_months(getdate(), -6)
    
    # Get active patients (had appointment in last 6 months)
    active_data = frappe.db.sql(f"""
        SELECT 
            CASE 
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 < 18 THEN 'Under 18'
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 BETWEEN 18 AND 35 THEN '18-35'
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 BETWEEN 36 AND 55 THEN '36-55'
                WHEN DATEDIFF(CURDATE(), p.dob) / 365.25 BETWEEN 56 AND 70 THEN '56-70'
                ELSE 'Over 70'
            END as age_group,
            COALESCE(p.sex, 'Unknown') as gender,
            COUNT(DISTINCT CASE WHEN p.creation >= %s THEN p.name END) as new_patients,
            COUNT(DISTINCT CASE WHEN da.appointment_date >= %s THEN p.name END) as active_patients
        FROM `tabPatient` p
        INNER JOIN `tabDental Patient` dp ON p.name = dp.healthcare_patient
        LEFT JOIN `tabDental Appointment` da ON p.name = da.patient 
            AND da.status IN ('Confirmed', 'Completed')
        WHERE 1=1 {conditions}
        GROUP BY age_group, gender
    """, (six_months_ago, six_months_ago), as_dict=True)
    
    # Create lookup dictionary for additional data
    additional_data = {}
    for row in active_data:
        key = f"{row.age_group}_{row.gender}"
        additional_data[key] = {
            'new_patients': row.new_patients or 0,
            'active_patients': row.active_patients or 0
        }
    
    # Merge data
    result = []
    for row in demographics_data:
        key = f"{row.age_group}_{row.gender}"
        additional = additional_data.get(key, {'new_patients': 0, 'active_patients': 0})
        
        result.append({
            'age_group': row.age_group,
            'gender': row.gender,
            'patient_count': row.patient_count,
            'percentage': flt((row.patient_count / total_patients) * 100, 1) if total_patients else 0,
            'avg_age': flt(row.avg_age, 1),
            'new_patients_last_6m': additional['new_patients'],
            'active_patients': additional['active_patients']
        })
    
    # Add summary row
    if result:
        result.append({
            'age_group': '<b>Total</b>',
            'gender': '',
            'patient_count': total_patients,
            'percentage': 100.0,
            'avg_age': sum(r['avg_age'] * r['patient_count'] for r in result[:-1]) / total_patients if total_patients else 0,
            'new_patients_last_6m': sum(r['new_patients_last_6m'] for r in result[:-1]),
            'active_patients': sum(r['active_patients'] for r in result[:-1])
        })
    
    return result


def get_conditions(filters):
    """Build WHERE conditions based on filters"""
    conditions = []
    
    if filters.get("from_date"):
        conditions.append(f"p.creation >= '{filters.get('from_date')}'")
    
    if filters.get("to_date"):
        conditions.append(f"p.creation <= '{filters.get('to_date')}'")
    
    if filters.get("clinic"):
        # If clinic filter is needed, add appropriate join and condition
        pass
    
    if filters.get("practitioner"):
        conditions.append(f"""
            EXISTS (
                SELECT 1 FROM `tabDental Appointment` da 
                WHERE da.patient = p.name 
                AND da.practitioner = '{filters.get('practitioner')}'
            )
        """)
    
    return " AND " + " AND ".join(conditions) if conditions else ""


def get_chart_data(data):
    """Generate chart data for visualization"""
    if not data or len(data) <= 1:  # Skip if no data or only total row
        return None
    
    # Remove total row for chart
    chart_data = [row for row in data if not row.get('age_group', '').startswith('<b>')]
    
    # Age group distribution chart
    age_groups = []
    age_counts = []
    
    for row in chart_data:
        if row['age_group'] not in age_groups:
            age_groups.append(row['age_group'])
            age_counts.append(0)
        
        idx = age_groups.index(row['age_group'])
        age_counts[idx] += row['patient_count']
    
    return {
        "data": {
            "labels": age_groups,
            "datasets": [
                {
                    "name": "Patient Count",
                    "values": age_counts
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#7cd6fd", "#5e64ff", "#743ee2", "#ff5858", "#ffa00a"]
    }


def get_patient_summary_data(filters=None):
    """
    Helper function to get patient summary statistics
    Used by other reports and dashboards
    """
    conditions = get_conditions(filters or {})
    
    summary = frappe.db.sql(f"""
        SELECT 
            COUNT(*) as total_patients,
            COUNT(CASE WHEN p.sex = 'Male' THEN 1 END) as male_patients,
            COUNT(CASE WHEN p.sex = 'Female' THEN 1 END) as female_patients,
            AVG(DATEDIFF(CURDATE(), p.dob) / 365.25) as avg_age,
            COUNT(CASE WHEN p.creation >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) THEN 1 END) as new_patients_6m,
            COUNT(CASE WHEN p.creation >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) THEN 1 END) as new_patients_1m
        FROM `tabPatient` p
        INNER JOIN `tabDental Patient` dp ON p.name = dp.healthcare_patient
        WHERE 1=1 {conditions}
    """, as_dict=True)
    
    return summary[0] if summary else {}


# Additional utility functions for other reports
def get_age_group(dob):
    """Utility function to categorize age groups"""
    if not dob:
        return "Unknown"
    
    age = (datetime.now().date() - dob).days / 365.25
    
    if age < 18:
        return "Under 18"
    elif age <= 35:
        return "18-35"
    elif age <= 55:
        return "36-55"
    elif age <= 70:
        return "56-70"
    else:
        return "Over 70" 