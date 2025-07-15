import frappe
from frappe.utils import cint, flt

def get_context(context):
    """Get context for Patient Dashboard page"""
    context.no_cache = 1
    context.show_sidebar = False
    
    # Add any initial data needed for the page
    context.title = "Patient Dashboard"
    
    return context

@frappe.whitelist()
def get_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        from dentcharts.patient_management.patient_summary import get_patient_stats
        
        # Get patient statistics
        patient_stats = get_patient_stats()
        
        # Get appointment data (sample for now)
        appointment_data = {
            "today": 12,
            "upcoming": 8,
            "completed_this_month": 45
        }
        
        # Get payment data (sample for now)
        payment_data = {
            "outstanding": 5420,
            "received_this_month": 12500,
            "recent_payments": 8
        }
        
        return {
            "success": True,
            "data": {
                "patient_stats": patient_stats,
                "appointment_stats": appointment_data,
                "payment_stats": payment_data
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dashboard Data Error")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_patient_list(search_term="", limit=20):
    """Get patient list with search"""
    try:
        conditions = []
        values = []
        
        if search_term:
            conditions.append("""
                (patient_name LIKE %s OR 
                 mobile_number LIKE %s OR 
                 email LIKE %s OR 
                 name LIKE %s)
            """)
            search_value = f"%{search_term}%"
            values.extend([search_value, search_value, search_value, search_value])
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        patients = frappe.db.sql(f"""
            SELECT 
                name,
                patient_name,
                mobile_number,
                email,
                sex,
                date_of_birth,
                creation,
                modified
            FROM `tabdental_patient`
            {where_clause}
            ORDER BY modified DESC
            LIMIT {limit}
        """, values, as_dict=True)
        
        # Calculate age for each patient
        from frappe.utils import getdate
        for patient in patients:
            if patient.get('date_of_birth'):
                today = getdate()
                dob = getdate(patient.date_of_birth)
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                patient['age'] = age
            else:
                patient['age'] = None
        
        return {
            "success": True,
            "patients": patients
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient List Error")
        return {
            "success": False,
            "error": str(e),
            "patients": []
        }
