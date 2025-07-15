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
        
        # Get real appointment data
        appointment_data = get_appointment_stats()
        
        # Get real payment data
        payment_data = get_payment_stats()
        
        # Get recent activity
        recent_activity = get_recent_activity()
        
        return {
            "success": True,
            "data": {
                "patient_stats": patient_stats,
                "appointment_stats": appointment_data,
                "payment_stats": payment_data,
                "recent_activity": recent_activity
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dashboard Data Error")
        return {
            "success": False,
            "error": str(e)
        }

def get_appointment_stats():
    """Get real appointment statistics"""
    try:
        # Today's appointments
        today_appointments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabDental Appointment` 
            WHERE DATE(appointment_date) = CURDATE()
            AND docstatus = 1
        """)[0][0] or 0
        
        # Upcoming appointments (next 7 days)
        upcoming_appointments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabDental Appointment` 
            WHERE appointment_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        # Completed appointments this month
        completed_appointments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabDental Appointment` 
            WHERE DATE(appointment_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND appointment_status = 'Completed'
            AND docstatus = 1
        """)[0][0] or 0
        
        return {
            "today": today_appointments,
            "upcoming": upcoming_appointments,
            "completed_this_month": completed_appointments
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Appointment Stats Error")
        return {
            "today": 0,
            "upcoming": 0,
            "completed_this_month": 0
        }

def get_payment_stats():
    """Get real payment statistics"""
    try:
        # Total outstanding balance
        outstanding_balance = frappe.db.sql("""
            SELECT SUM(outstanding_amount) 
            FROM `tabSales Invoice` 
            WHERE docstatus = 1 
            AND outstanding_amount > 0
        """)[0][0] or 0
        
        # Payments received this month
        payments_this_month = frappe.db.sql("""
            SELECT SUM(paid_amount) 
            FROM `tabDental Payment Entry` 
            WHERE DATE(posting_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        # Recent payments count
        recent_payments = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabDental Payment Entry` 
            WHERE DATE(posting_date) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            AND docstatus = 1
        """)[0][0] or 0
        
        return {
            "outstanding": outstanding_balance,
            "received_this_month": payments_this_month,
            "recent_payments": recent_payments
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Stats Error")
        return {
            "outstanding": 0,
            "received_this_month": 0,
            "recent_payments": 0
        }

def get_recent_activity():
    """Get recent activity from appointments"""
    try:
        recent_activity = frappe.db.sql("""
            SELECT 
                da.patient_name,
                da.appointment_date,
                da.appointment_time,
                da.appointment_status,
                da.practitioner
            FROM `tabDental Appointment` da
            WHERE da.docstatus = 1
            ORDER BY da.appointment_date DESC, da.appointment_time DESC
            LIMIT 10
        """, as_dict=True)
        
        return recent_activity
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Recent Activity Error")
        return []

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
            FROM `tabDental Patient`
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
