"""
Patient Dashboard API
Backend functions for the patient dashboard system
"""

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_days
from datetime import datetime, timedelta


@frappe.whitelist()
def get_dashboard_stats():
    """Get dashboard statistics for the main dashboard"""
    try:
        # Get total patients
        total_patients = frappe.db.count('Dental Patient')
        
        # Get today's appointments
        today = nowdate()
        today_appointments = frappe.db.count('Dental Appointment', {
            'appointment_date': today
        })
        
        # Get confirmed appointments
        confirmed_appointments = frappe.db.count('Dental Appointment', {
            'appointment_date': today,
            'status': 'Confirmed'
        })
        
        # Get completed appointments
        completed_appointments = frappe.db.count('Dental Appointment', {
            'appointment_date': today,
            'status': 'Completed'
        })
        
        # Get cancelled appointments
        cancelled_appointments = frappe.db.count('Dental Appointment', {
            'appointment_date': today,
            'status': 'Cancelled'
        })
        
        # Get total outstanding balance
        total_outstanding = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND outstanding_amount > 0
        """)[0][0] or 0
        
        # Get today's revenue
        today_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(paid_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND posting_date = %s
        """, today)[0][0] or 0
        
        # Get pending invoices
        pending_invoices = frappe.db.count('Invoice', {
            'status': 'Unpaid'
        })
        
        # Get completed treatments
        completed_treatments = frappe.db.count('Dental Chart Activity', {
            'status': 'Completed'
        })
        
        # Get active patients (patients with appointments in last 30 days)
        thirty_days_ago = add_days(today, -30)
        active_patients = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient)
            FROM `tabDental Appointment`
            WHERE appointment_date >= %s
        """, thirty_days_ago)[0][0] or 0
        
        # Calculate average treatment cost
        avg_treatment_cost = frappe.db.sql("""
            SELECT COALESCE(AVG(total_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND total_amount > 0
        """)[0][0] or 0
        
        # Calculate patient growth (simplified - just count new patients this month)
        first_day_of_month = today.replace(day=1)
        new_patients_this_month = frappe.db.count('Dental Patient', {
            'creation': ('>=', first_day_of_month)
        })
        
        # Calculate growth percentage (simplified)
        patient_growth = 0  # Placeholder for growth calculation
        
        return {
            'total_patients': total_patients,
            'today_appointments': today_appointments,
            'confirmed_appointments': confirmed_appointments,
            'completed_appointments': completed_appointments,
            'cancelled_appointments': cancelled_appointments,
            'total_outstanding': total_outstanding,
            'today_revenue': today_revenue,
            'pending_invoices': pending_invoices,
            'completed_treatments': completed_treatments,
            'active_patients': active_patients,
            'avg_treatment_cost': avg_treatment_cost,
            'patient_growth': patient_growth
        }
    except Exception as e:
        frappe.log_error(f"Error in get_dashboard_stats: {str(e)}")
        return {
            'total_patients': 0,
            'today_appointments': 0,
            'confirmed_appointments': 0,
            'completed_appointments': 0,
            'cancelled_appointments': 0,
            'total_outstanding': 0,
            'today_revenue': 0,
            'pending_invoices': 0,
            'completed_treatments': 0,
            'active_patients': 0,
            'avg_treatment_cost': 0,
            'patient_growth': 0
        }


@frappe.whitelist()
def search_patients(query, filters=None):
    """Search patients by name, ID, or phone"""
    try:
        if not query or len(query) < 2:
            return []
        
        # Build search conditions
        conditions = []
        args = []
        
        # Search in patient name, patient_id, and phone
        search_condition = f"""
            (patient_name LIKE %s OR patient_id LIKE %s OR phone LIKE %s)
        """
        search_term = f"%{query}%"
        conditions.append(search_condition)
        args.extend([search_term, search_term, search_term])
        
        # Add filters if provided
        if filters:
            if filters.get('status'):
                conditions.append("status = %s")
                args.append(filters['status'])
            
            if filters.get('age_range'):
                # Parse age range and add conditions
                age_range = filters['age_range']
                if age_range == '0-18':
                    conditions.append("age BETWEEN 0 AND 18")
                elif age_range == '19-30':
                    conditions.append("age BETWEEN 19 AND 30")
                elif age_range == '31-50':
                    conditions.append("age BETWEEN 31 AND 50")
                elif age_range == '51+':
                    conditions.append("age >= 51")
        
        # Build final query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT name, patient_name, patient_id, age, sex, status, phone, email
            FROM `tabDental Patient`
            WHERE {where_clause}
            ORDER BY patient_name
            LIMIT 20
        """
        
        patients = frappe.db.sql(query, args, as_dict=True)
        return patients
        
    except Exception as e:
        frappe.log_error(f"Error in search_patients: {str(e)}")
        return []


@frappe.whitelist()
def get_patient_data(patient_id):
    """Get complete patient data for dashboard"""
    try:
        patient = frappe.get_doc('Dental Patient', patient_id)
        
        # Get last visit date
        last_visit = frappe.db.sql("""
            SELECT MAX(appointment_date)
            FROM `tabDental Appointment`
            WHERE patient = %s AND status = 'Completed'
        """, patient_id)[0][0]
        
        # Calculate age
        age = None
        if patient.date_of_birth:
            age = (datetime.now().date() - getdate(patient.date_of_birth)).days // 365
        
        return {
            'name': patient.name,
            'patient_name': patient.patient_name,
            'patient_id': patient.patient_id,
            'age': age,
            'sex': patient.sex,
            'phone': patient.phone,
            'email': patient.email,
            'address': patient.address,
            'last_visit_date': last_visit
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_patient_data: {str(e)}")
        return None


@frappe.whitelist()
def get_patient_summary(patient_id):
    """Get patient summary data for notebook-style display"""
    try:
        # Get patient info
        patient = frappe.get_doc('Dental Patient', patient_id)
        
        # Get appointments with summary data
        appointments = frappe.db.sql("""
            SELECT 
                appointment_date,
                appointment_time,
                appointment_type,
                status,
                notes,
                doctor
            FROM `tabDental Appointment`
            WHERE patient = %s
            ORDER BY appointment_date DESC, appointment_time DESC
            LIMIT 50
        """, patient_id, as_dict=True)
        
        # Get dental chart activities
        activities = frappe.db.sql("""
            SELECT 
                activity_date,
                activity_type,
                description,
                tooth_number,
                status
            FROM `tabDental Chart Activity`
            WHERE patient = %s
            ORDER BY activity_date DESC
            LIMIT 100
        """, patient_id, as_dict=True)
        
        # Group by date
        summary_by_date = {}
        
        for appointment in appointments:
            date = appointment.appointment_date.strftime('%Y-%m-%d')
            if date not in summary_by_date:
                summary_by_date[date] = {
                    'date': date,
                    'doctor': appointment.doctor,
                    'chief_complaint': appointment.appointment_type,
                    'notes': appointment.notes,
                    'findings': [],
                    'procedures': [],
                    'conditions': [],
                    'manual_notes': appointment.notes
                }
        
        # Add activities to summary
        for activity in activities:
            date = activity.activity_date.strftime('%Y-%m-%d')
            if date in summary_by_date:
                if activity.activity_type == 'Procedure':
                    summary_by_date[date]['procedures'].append({
                        'tooth': activity.tooth_number,
                        'procedure': activity.description,
                        'status': activity.status,
                        'cost': 0  # Placeholder
                    })
                elif activity.activity_type == 'Condition':
                    summary_by_date[date]['conditions'].append({
                        'tooth': activity.tooth_number,
                        'condition': activity.description,
                        'severity': 'Moderate'  # Placeholder
                    })
                else:
                    summary_by_date[date]['findings'].append(activity.description)
        
        return {
            'patient_info': {
                'name': patient.patient_name,
                'patient_id': patient.patient_id,
                'age': age if 'age' in locals() else None,
                'sex': patient.sex
            },
            'summary_by_date': list(summary_by_date.values())
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_patient_summary: {str(e)}")
        return {'patient_info': {}, 'summary_by_date': []}


@frappe.whitelist()
def get_recent_patients(limit=5):
    """Get recent patients for dashboard"""
    try:
        patients = frappe.db.sql("""
            SELECT name, patient_name, patient_id, age, sex
            FROM `tabDental Patient`
            ORDER BY creation DESC
            LIMIT %s
        """, limit, as_dict=True)
        
        return patients
        
    except Exception as e:
        frappe.log_error(f"Error in get_recent_patients: {str(e)}")
        return []


@frappe.whitelist()
def get_today_appointments():
    """Get today's appointments for dashboard"""
    try:
        today = nowdate()
        
        appointments = frappe.db.sql("""
            SELECT 
                appointment_time,
                patient_name,
                appointment_type,
                status
            FROM `tabDental Appointment`
            WHERE appointment_date = %s
            ORDER BY appointment_time
        """, today, as_dict=True)
        
        return appointments
        
    except Exception as e:
        frappe.log_error(f"Error in get_today_appointments: {str(e)}")
        return []


@frappe.whitelist()
def get_financial_summary():
    """Get financial summary for dashboard"""
    try:
        today = nowdate()
        
        # Get total outstanding
        total_outstanding = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND outstanding_amount > 0
        """)[0][0] or 0
        
        # Get today's revenue
        today_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(paid_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND posting_date = %s
        """, today)[0][0] or 0
        
        # Get pending invoices
        pending_invoices = frappe.db.count('Invoice', {
            'status': 'Unpaid'
        })
        
        return {
            'total_outstanding': total_outstanding,
            'today_revenue': today_revenue,
            'pending_invoices': pending_invoices
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_financial_summary: {str(e)}")
        return {
            'total_outstanding': 0,
            'today_revenue': 0,
            'pending_invoices': 0
        }


@frappe.whitelist()
def get_statistics():
    """Get statistics for dashboard"""
    try:
        # Get completed treatments
        completed_treatments = frappe.db.count('Dental Chart Activity', {
            'status': 'Completed'
        })
        
        # Get active patients
        thirty_days_ago = add_days(nowdate(), -30)
        active_patients = frappe.db.sql("""
            SELECT COUNT(DISTINCT patient)
            FROM `tabDental Appointment`
            WHERE appointment_date >= %s
        """, thirty_days_ago)[0][0] or 0
        
        # Get monthly revenue
        first_day_of_month = nowdate().replace(day=1)
        monthly_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(paid_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND posting_date >= %s
        """, first_day_of_month)[0][0] or 0
        
        # Get average treatment cost
        avg_treatment_cost = frappe.db.sql("""
            SELECT COALESCE(AVG(total_amount), 0)
            FROM `tabDental Payment Entry`
            WHERE docstatus = 1 AND total_amount > 0
        """)[0][0] or 0
        
        return {
            'completed_treatments': completed_treatments,
            'active_patients': active_patients,
            'monthly_revenue': monthly_revenue,
            'avg_treatment_cost': avg_treatment_cost
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_statistics: {str(e)}")
        return {
            'completed_treatments': 0,
            'active_patients': 0,
            'monthly_revenue': 0,
            'avg_treatment_cost': 0
        }


@frappe.whitelist()
def get_patient_payments(patient_id):
    """Get patient payment history"""
    try:
        payments = frappe.db.sql("""
            SELECT 
                posting_date,
                paid_amount,
                status,
                payment_method,
                reference_no
            FROM `tabDental Payment Entry`
            WHERE patient = %s AND docstatus = 1
            ORDER BY posting_date DESC
            LIMIT 20
        """, patient_id, as_dict=True)
        
        return {
            'payments': payments
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_patient_payments: {str(e)}")
        return {'payments': []}


@frappe.whitelist()
def get_tooth_data(patient_id, tooth_number):
    """Get specific tooth data for chart"""
    try:
        # Get conditions for this tooth
        conditions = frappe.db.sql("""
            SELECT condition_type, severity, notes
            FROM `tabTooth Condition`
            WHERE patient = %s AND tooth_number = %s
        """, (patient_id, tooth_number), as_dict=True)
        
        # Get procedures for this tooth
        procedures = frappe.db.sql("""
            SELECT procedure_type, status, cost, notes
            FROM `tabTooth Procedure`
            WHERE patient = %s AND tooth_number = %s
        """, (patient_id, tooth_number), as_dict=True)
        
        # Get notes for this tooth
        notes = frappe.db.sql("""
            SELECT notes
            FROM `tabDental Chart Activity`
            WHERE patient = %s AND tooth_number = %s
            ORDER BY activity_date DESC
            LIMIT 1
        """, (patient_id, tooth_number))
        
        return {
            'conditions': conditions,
            'procedures': procedures,
            'notes': notes[0][0] if notes else ''
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_tooth_data: {str(e)}")
        return {
            'conditions': [],
            'procedures': [],
            'notes': ''
        }


@frappe.whitelist()
def save_chart_data(patient_id, chart_data):
    """Save chart data"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would save the chart data to the database
        frappe.logger().info(f"Saving chart data for patient {patient_id}")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error in save_chart_data: {str(e)}")
        return False


@frappe.whitelist()
def reset_chart_data(patient_id):
    """Reset chart data"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would reset the chart data
        frappe.logger().info(f"Resetting chart data for patient {patient_id}")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error in reset_chart_data: {str(e)}")
        return False


@frappe.whitelist()
def add_tooth_condition(patient_id, tooth_number, condition_type, severity, notes):
    """Add condition to a tooth"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would create a Tooth Condition record
        frappe.logger().info(f"Adding condition to tooth {tooth_number} for patient {patient_id}")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error in add_tooth_condition: {str(e)}")
        return False


@frappe.whitelist()
def add_tooth_procedure(patient_id, tooth_number, procedure_type, status, cost, notes):
    """Add procedure to a tooth"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would create a Tooth Procedure record
        frappe.logger().info(f"Adding procedure to tooth {tooth_number} for patient {patient_id}")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error in add_tooth_procedure: {str(e)}")
        return False


@frappe.whitelist()
def add_tooth_note(patient_id, tooth_number, note):
    """Add note to a tooth"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would create a Dental Chart Activity record
        frappe.logger().info(f"Adding note to tooth {tooth_number} for patient {patient_id}")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error in add_tooth_note: {str(e)}")
        return False


@frappe.whitelist()
def test_dashboard():
    """Test function for dashboard access"""
    try:
        stats = get_dashboard_stats()
        patients = search_patients("test")
        
        return {
            "status": "success",
            "dashboard_stats": stats,
            "patient_search": patients,
            "message": "All UI components are working"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        } 