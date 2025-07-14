import frappe
from frappe import _
from frappe.utils import nowdate, getdate
from datetime import datetime, timedelta

def get_patient_summary_data(patient_id):
    """Get comprehensive patient summary data"""
    try:
        if not patient_id:
            return {"error": "Patient ID is required"}
        
        # Get all summary data
        summary_data = {
            "patient_info": get_patient_basic_info(patient_id),
            "summary_by_date": get_chronological_summary(patient_id),
            "recent_activities": get_recent_activities(patient_id),
            "treatment_summary": get_treatment_summary(patient_id),
            "financial_summary": get_financial_summary(patient_id)
        }
        
        return {"success": True, "data": summary_data}
    except Exception as e:
        frappe.log_error(f"Error getting patient summary data: {str(e)}")
        return {"error": str(e)}

def get_patient_basic_info(patient_id):
    """Get basic patient information for summary"""
    try:
        patient = frappe.get_doc("Dental Patient", patient_id)
        return {
            "name": patient.patient_name,
            "age": calculate_age(patient.date_of_birth),
            "sex": patient.sex,
            "patient_id": patient.name,
            "registration_date": patient.creation.strftime('%Y-%m-%d'),
            "last_visit": get_last_visit_date(patient_id),
            "total_visits": get_total_visits(patient_id)
        }
    except Exception as e:
        frappe.log_error(f"Error getting patient basic info: {str(e)}")
        return {}

def get_chronological_summary(patient_id):
    """Get chronological summary grouped by date"""
    try:
        summary_by_date = {}
        
        # Get all appointments
        appointments = frappe.db.sql("""
            SELECT 
                appointment_date,
                practitioner,
                notes,
                status,
                chief_complaint,
                creation
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
            ORDER BY appointment_date DESC
        """, patient_id, as_dict=True)
        
        # Get all chart activities
        activities = frappe.db.sql("""
            SELECT 
                DATE(creation) as activity_date,
                activity_type,
                description,
                tooth_number,
                condition_name,
                procedure_name,
                severity,
                status,
                cost,
                creation
            FROM `tabDental Chart Activity`
            WHERE patient = %s
            ORDER BY creation DESC
        """, patient_id, as_dict=True)
        
        # Get all payment entries
        payments = frappe.db.sql("""
            SELECT 
                payment_date,
                payment_amount,
                payment_method,
                reference_no,
                notes,
                creation
            FROM `tabDental Payment Entry`
            WHERE patient = %s AND docstatus = 1
            ORDER BY payment_date DESC
        """, patient_id, as_dict=True)
        
        # Group appointments by date
        for appointment in appointments:
            date_key = appointment.appointment_date.strftime('%Y-%m-%d')
            if date_key not in summary_by_date:
                summary_by_date[date_key] = create_date_entry(date_key, appointment.practitioner)
            
            summary_by_date[date_key]['chief_complaint'] = appointment.chief_complaint
            summary_by_date[date_key]['notes'] = appointment.notes
            summary_by_date[date_key]['appointment_status'] = appointment.status
        
        # Group activities by date
        for activity in activities:
            date_key = activity.activity_date.strftime('%Y-%m-%d')
            if date_key not in summary_by_date:
                summary_by_date[date_key] = create_date_entry(date_key, '')
            
            if activity.activity_type == 'Condition':
                summary_by_date[date_key]['conditions'].append({
                    'tooth': activity.tooth_number,
                    'condition': activity.condition_name,
                    'severity': activity.severity or 'Moderate',
                    'description': activity.description
                })
            elif activity.activity_type == 'Procedure':
                summary_by_date[date_key]['procedures'].append({
                    'tooth': activity.tooth_number,
                    'procedure': activity.procedure_name,
                    'status': activity.status or 'Completed',
                    'cost': activity.cost or 0,
                    'description': activity.description
                })
            elif activity.activity_type == 'Note':
                summary_by_date[date_key]['findings'].append(activity.description)
        
        # Group payments by date
        for payment in payments:
            date_key = payment.payment_date.strftime('%Y-%m-%d')
            if date_key not in summary_by_date:
                summary_by_date[date_key] = create_date_entry(date_key, '')
            
            summary_by_date[date_key]['payments'].append({
                'amount': payment.payment_amount,
                'method': payment.payment_method,
                'reference': payment.reference_no,
                'notes': payment.notes
            })
        
        # Convert to list and sort by date
        summary_list = list(summary_by_date.values())
        summary_list.sort(key=lambda x: x['date'], reverse=True)
        
        return summary_list
    except Exception as e:
        frappe.log_error(f"Error getting chronological summary: {str(e)}")
        return []

def create_date_entry(date, doctor):
    """Create a new date entry for summary"""
    return {
        'date': date,
        'doctor': doctor,
        'chief_complaint': '',
        'notes': '',
        'findings': [],
        'procedures': [],
        'conditions': [],
        'payments': [],
        'manual_notes': '',
        'appointment_status': ''
    }

def get_recent_activities(patient_id):
    """Get recent activities for quick overview"""
    try:
        activities = frappe.db.sql("""
            SELECT 
                'appointment' as type,
                appointment_date as date,
                status,
                practitioner as doctor,
                chief_complaint as description
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
            UNION ALL
            SELECT 
                'activity' as type,
                DATE(creation) as date,
                activity_type as status,
                '' as doctor,
                description
            FROM `tabDental Chart Activity`
            WHERE patient = %s
            ORDER BY date DESC
            LIMIT 20
        """, (patient_id, patient_id), as_dict=True)
        
        return activities
    except Exception as e:
        frappe.log_error(f"Error getting recent activities: {str(e)}")
        return []

def get_treatment_summary(patient_id):
    """Get treatment summary statistics"""
    try:
        # Get total procedures
        total_procedures = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Chart Activity`
            WHERE patient = %s AND activity_type = 'Procedure'
        """, patient_id, as_dict=True)
        
        # Get total conditions
        total_conditions = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Chart Activity`
            WHERE patient = %s AND activity_type = 'Condition'
        """, patient_id, as_dict=True)
        
        # Get total cost
        total_cost = frappe.db.sql("""
            SELECT COALESCE(SUM(cost), 0) as total
            FROM `tabDental Chart Activity`
            WHERE patient = %s AND activity_type = 'Procedure'
        """, patient_id, as_dict=True)
        
        return {
            'total_procedures': total_procedures[0].count if total_procedures else 0,
            'total_conditions': total_conditions[0].count if total_conditions else 0,
            'total_cost': total_cost[0].total if total_cost else 0
        }
    except Exception as e:
        frappe.log_error(f"Error getting treatment summary: {str(e)}")
        return {}

def get_financial_summary(patient_id):
    """Get financial summary"""
    try:
        # Get total paid
        total_paid = frappe.db.sql("""
            SELECT COALESCE(SUM(payment_amount), 0) as total
            FROM `tabDental Payment Entry`
            WHERE patient = %s AND docstatus = 1
        """, patient_id, as_dict=True)
        
        # Get total outstanding
        total_outstanding = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0) as total
            FROM `tabInvoice`
            WHERE patient = %s AND outstanding_amount > 0
        """, patient_id, as_dict=True)
        
        return {
            'total_paid': total_paid[0].total if total_paid else 0,
            'total_outstanding': total_outstanding[0].total if total_outstanding else 0,
            'total_billed': (total_paid[0].total if total_paid else 0) + (total_outstanding[0].total if total_outstanding else 0)
        }
    except Exception as e:
        frappe.log_error(f"Error getting financial summary: {str(e)}")
        return {}

def get_last_visit_date(patient_id):
    """Get last visit date"""
    try:
        result = frappe.db.sql("""
            SELECT MAX(appointment_date) as last_visit
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
        """, patient_id, as_dict=True)
        
        if result and result[0].last_visit:
            return result[0].last_visit.strftime('%Y-%m-%d')
        return None
    except Exception as e:
        frappe.log_error(f"Error getting last visit date: {str(e)}")
        return None

def get_total_visits(patient_id):
    """Get total number of visits"""
    try:
        result = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
        """, patient_id, as_dict=True)
        
        return result[0].count if result else 0
    except Exception as e:
        frappe.log_error(f"Error getting total visits: {str(e)}")
        return 0

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    try:
        if not date_of_birth:
            return None
        
        today = getdate()
        dob = getdate(date_of_birth)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception as e:
        frappe.log_error(f"Error calculating age: {str(e)}")
        return None

def format_summary_for_display(summary_data):
    """Format summary data for notebook-style display"""
    try:
        formatted_summary = []
        
        for date_entry in summary_data:
            formatted_entry = {
                'date': date_entry['date'],
                'doctor': date_entry['doctor'],
                'display_text': generate_display_text(date_entry)
            }
            formatted_summary.append(formatted_entry)
        
        return formatted_summary
    except Exception as e:
        frappe.log_error(f"Error formatting summary for display: {str(e)}")
        return []

def generate_display_text(date_entry):
    """Generate readable text for a date entry"""
    try:
        text_parts = []
        
        # Add chief complaint
        if date_entry.get('chief_complaint'):
            text_parts.append(f"Chief Complaint: {date_entry['chief_complaint']}")
        
        # Add notes
        if date_entry.get('notes'):
            text_parts.append(f"Notes: {date_entry['notes']}")
        
        # Add findings
        if date_entry.get('findings'):
            text_parts.append("Findings:")
            for finding in date_entry['findings']:
                text_parts.append(f"• {finding}")
        
        # Add procedures
        if date_entry.get('procedures'):
            text_parts.append("Procedures:")
            for procedure in date_entry['procedures']:
                text_parts.append(f"• Tooth {procedure['tooth']}: {procedure['procedure']} ({procedure['status']}) - ${procedure['cost']}")
        
        # Add conditions
        if date_entry.get('conditions'):
            text_parts.append("Conditions:")
            for condition in date_entry['conditions']:
                text_parts.append(f"• Tooth {condition['tooth']}: {condition['condition']} ({condition['severity']})")
        
        # Add payments
        if date_entry.get('payments'):
            text_parts.append("Payments:")
            for payment in date_entry['payments']:
                text_parts.append(f"• ${payment['amount']} via {payment['method']}")
        
        # Add manual notes
        if date_entry.get('manual_notes'):
            text_parts.append(f"Manual Notes: {date_entry['manual_notes']}")
        
        return "\n".join(text_parts)
    except Exception as e:
        frappe.log_error(f"Error generating display text: {str(e)}")
        return "Error generating summary text" 