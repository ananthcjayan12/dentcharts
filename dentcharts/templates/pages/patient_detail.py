import frappe
from frappe.utils import cint, flt

def get_context(context):
    """Get context for Individual Patient Dashboard page"""
    context.no_cache = 1
    context.show_sidebar = False
    
    # Get patient ID from URL
    patient_id = frappe.form_dict.get('patient_id')
    if not patient_id:
        frappe.throw("Patient ID is required")
    
    # Get patient data
    try:
        patient = frappe.get_doc("Dental Patient", patient_id)
        context.patient = patient
        context.patient_id = patient_id
        context.title = f"Patient Dashboard - {patient.patient_name}"
    except Exception as e:
        frappe.throw(f"Patient not found: {str(e)}")
    
    return context

@frappe.whitelist()
def get_patient_detail_data(patient_id):
    """API endpoint for individual patient dashboard data"""
    try:
        # Get patient basic info
        patient = frappe.get_doc("Dental Patient", patient_id)
        
        # Get patient's appointment history
        appointments = frappe.db.sql("""
            SELECT 
                name,
                appointment_date,
                appointment_time,
                status,
                practitioner,
                chief_complaint,
                practitioner_notes as notes
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
            ORDER BY appointment_date DESC, appointment_time DESC
            LIMIT 10
        """, (patient_id,), as_dict=True)
        
        # Get patient's payment history
        payments = frappe.db.sql("""
            SELECT 
                name,
                posting_date,
                payment_amount,
                payment_method,
                reference_number,
                notes
            FROM `tabDental Payment Entry`
            WHERE patient = %s AND docstatus = 1
            ORDER BY posting_date DESC
            LIMIT 10
        """, (patient_id,), as_dict=True)
        
        # Get dental chart data (if exists)
        chart_data = []
        try:
            chart_records = frappe.db.sql("""
                SELECT 
                    tooth_number,
                    procedure_name,
                    status,
                    cost,
                    date_completed
                FROM `tabTooth Procedure`
                WHERE patient = %s
                ORDER BY tooth_number, date_completed DESC
            """, (patient_id,), as_dict=True)
            chart_data = chart_records
        except Exception:
            # Table might not exist yet
            pass
        
        # Get recent activity for notebook-style summary
        recent_activity = get_patient_activity_summary(patient_id)
        
        result = {
            "success": True,
            "data": {
                "patient_info": {
                    "name": patient.name,
                    "patient_name": patient.patient_name,
                    "age": calculate_age(patient.dob) if patient.dob else None,
                    "sex": patient.sex,
                    "mobile": patient.mobile,
                    "email": patient.email,
                    "registration_date": patient.date_of_registration or patient.creation,
                    "emergency_contact": patient.emergency_contact,
                    "emergency_phone": patient.emergency_phone
                },
                "medical_history": {
                    "dental_history": patient.dental_history,
                    "dental_allergies": patient.dental_allergies,
                    "previous_dental_work": patient.previous_dental_work,
                    "dental_insurance": patient.dental_insurance
                },
                "appointments": appointments,
                "payments": payments,
                "chart_data": chart_data,
                "activity_summary": recent_activity
            }
        }
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Patient Detail API Error: {frappe.get_traceback()}", "Patient Detail Error")
        return {
            "success": False,
            "error": str(e)
        }

def calculate_age(dob):
    """Calculate age from date of birth"""
    if not dob:
        return None
    
    from frappe.utils import getdate
    try:
        today = getdate()
        birth_date = getdate(dob)
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return None

def get_patient_activity_summary(patient_id, limit=5):
    """Get notebook-style activity summary for patient"""
    try:
        # Get appointments with notes grouped by date
        activities = frappe.db.sql("""
            SELECT 
                appointment_date as date,
                practitioner as doctor,
                chief_complaint,
                practitioner_notes as notes,
                status,
                appointment_time
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
            ORDER BY appointment_date DESC, appointment_time DESC
            LIMIT %s
        """, (patient_id, limit), as_dict=True)
        
        # Format for notebook-style display
        formatted_activities = []
        for activity in activities:
            formatted_activity = {
                "date": activity.date,
                "doctor": activity.doctor,
                "chief_complaint": activity.chief_complaint,
                "notes": activity.notes,
                "status": activity.status,
                "time": activity.appointment_time,
                "procedures": [],  # Will be populated with chart data
                "conditions": [],  # Will be populated with chart data
                "findings": []     # Will be populated with chart data
            }
            
            # Try to get chart activities for this date
            try:
                chart_activities = frappe.db.sql("""
                    SELECT 
                        activity_type,
                        tooth_number,
                        procedure_name,
                        notes as activity_notes
                    FROM `tabDental Chart Activity`
                    WHERE patient = %s AND DATE(creation) = %s
                """, (patient_id, activity.date), as_dict=True)
                
                for chart_activity in chart_activities:
                    if chart_activity.activity_type == "Procedure":
                        formatted_activity["procedures"].append({
                            "tooth": chart_activity.tooth_number,
                            "procedure": chart_activity.procedure_name,
                            "notes": chart_activity.activity_notes
                        })
                    elif chart_activity.activity_type == "Finding":
                        formatted_activity["findings"].append({
                            "tooth": chart_activity.tooth_number,
                            "finding": chart_activity.procedure_name,
                            "notes": chart_activity.activity_notes
                        })
            except Exception:
                # Chart activity table might not exist
                pass
            
            formatted_activities.append(formatted_activity)
        
        return formatted_activities
        
    except Exception as e:
        frappe.log_error(f"Activity Summary Error: {frappe.get_traceback()}", "Activity Summary Error")
        return []
