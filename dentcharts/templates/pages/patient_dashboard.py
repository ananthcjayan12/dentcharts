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
        # Add debugging
        frappe.log_error("Dashboard API called", "Debug")
        
        from dentcharts.patient_management.patient_summary import get_patient_stats
        
        # Get patient statistics
        patient_stats = get_patient_stats()
        frappe.log_error(f"Patient stats: {patient_stats}", "Debug")
        
        # Get appointment statistics - Fixed query with proper error handling
        appointment_stats = frappe.db.sql("""
            SELECT 
                COUNT(CASE WHEN DATE(appointment_date) = CURDATE() THEN 1 END) as today,
                COUNT(CASE WHEN appointment_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 1 END) as upcoming,
                COUNT(CASE WHEN DATE(appointment_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND status = 'Completed' THEN 1 END) as completed_this_month
            FROM `tabDental Appointment`
            WHERE docstatus != 2
        """, as_dict=True)
        
        appointment_stats = appointment_stats[0] if appointment_stats else {
            "today": 0, "upcoming": 0, "completed_this_month": 0
        }
        frappe.log_error(f"Appointment stats: {appointment_stats}", "Debug")
        
        # Get payment statistics - Fixed query with proper error handling
        payment_stats = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(CASE WHEN docstatus = 1 AND DATE(posting_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN payment_amount END), 0) as received_this_month,
                COUNT(CASE WHEN docstatus = 1 AND DATE(posting_date) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 END) as recent_payments,
                COALESCE(SUM(CASE WHEN docstatus = 1 THEN payment_amount END), 0) as total_received
            FROM `tabDental Payment Entry`
        """, as_dict=True)
        
        payment_stats = payment_stats[0] if payment_stats else {
            "received_this_month": 0, "recent_payments": 0, "total_received": 0
        }
        frappe.log_error(f"Payment stats: {payment_stats}", "Debug")
        
        # Get recent activity
        recent_activity = frappe.db.sql("""
            SELECT 
                patient,
                status,
                practitioner,
                appointment_date,
                appointment_time
            FROM `tabDental Appointment`
            WHERE docstatus != 2
            ORDER BY creation DESC
            LIMIT 5
        """, as_dict=True)
        
        frappe.log_error(f"Recent activity: {recent_activity}", "Debug")
        
        result = {
            "success": True,
            "data": {
                "patient_stats": patient_stats,
                "appointment_stats": appointment_stats,
                "payment_stats": payment_stats,
                "recent_activity": recent_activity
            }
        }
        
        frappe.log_error(f"Final result: {result}", "Debug")
        return result
        
    except Exception as e:
        frappe.log_error(f"Dashboard API Error: {frappe.get_traceback()}", "Dashboard Error")
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
            AND status = 'Completed'
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
            SELECT SUM(payment_amount) 
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
                da.patient,
                da.appointment_date,
                da.appointment_time,
                da.status,
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
        frappe.log_error(f"Getting patient list with search term: {search_term}", "Debug")
        
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
        
        # Check if columns exist first
        columns_query = f"""
            SELECT 
                name,
                patient_name,
                COALESCE(mobile_number, '') as mobile_number,
                COALESCE(email, '') as email,
                COALESCE(sex, '') as sex,
                date_of_birth,
                creation,
                modified
            FROM `tabDental Patient`
            {where_clause}
            ORDER BY modified DESC
            LIMIT {limit}
        """
        
        patients = frappe.db.sql(columns_query, values, as_dict=True)
        frappe.log_error(f"Found {len(patients)} patients", "Debug")
        
        # Calculate age for each patient
        from frappe.utils import getdate
        for patient in patients:
            if patient.get('date_of_birth'):
                try:
                    today = getdate()
                    dob = getdate(patient.date_of_birth)
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    patient['age'] = age
                except:
                    patient['age'] = None
            else:
                patient['age'] = None
        
        return {
            "success": True,
            "patients": patients
        }
    except Exception as e:
        frappe.log_error(f"Patient List Error: {frappe.get_traceback()}", "Patient List Error")
        return {
            "success": False,
            "error": str(e),
            "patients": []
        }
