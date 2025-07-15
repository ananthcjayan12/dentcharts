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
        
        # Get patient's payment history with enhanced details
        payments = frappe.db.sql("""
            SELECT 
                name,
                posting_date,
                payment_date,
                payment_amount,
                payment_method,
                payment_status,
                reference_number,
                notes,
                invoice,
                received_by,
                payment_account
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

@frappe.whitelist()
def get_patient_billing_summary(patient_id):
    """Get comprehensive billing and payment summary for a patient"""
    try:
        # Get payment summary
        payment_summary = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_payments,
                COALESCE(SUM(payment_amount), 0) as total_paid,
                COALESCE(AVG(payment_amount), 0) as average_payment,
                MAX(posting_date) as last_payment_date,
                COUNT(CASE WHEN payment_method = 'Cash' THEN 1 END) as cash_payments,
                COUNT(CASE WHEN payment_method = 'Card' THEN 1 END) as card_payments,
                COUNT(CASE WHEN payment_method = 'Bank Transfer' THEN 1 END) as bank_payments,
                COUNT(CASE WHEN payment_method = 'Insurance' THEN 1 END) as insurance_payments
            FROM `tabDental Payment Entry`
            WHERE patient = %s AND docstatus = 1
        """, (patient_id,), as_dict=True)
        
        payment_summary = payment_summary[0] if payment_summary else {}
        
        # Get recent payment trends (last 6 months)
        payment_trends = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(posting_date, '%%Y-%%m') as month,
                COUNT(*) as payment_count,
                SUM(payment_amount) as monthly_total
            FROM `tabDental Payment Entry`
            WHERE patient = %s AND docstatus = 1
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
            ORDER BY month DESC
        """, (patient_id,), as_dict=True)
        
        # Get outstanding invoices (if invoice system exists)
        outstanding_invoices = []
        try:
            outstanding_invoices = frappe.db.sql("""
                SELECT 
                    name,
                    posting_date,
                    grand_total,
                    outstanding_amount,
                    due_date,
                    status
                FROM `tabSales Invoice`
                WHERE customer = %s AND docstatus = 1 
                AND outstanding_amount > 0
                ORDER BY due_date ASC
            """, (patient_id,), as_dict=True)
        except Exception:
            # Invoice table might not exist or have different structure
            pass
        
        result = {
            "success": True,
            "data": {
                "payment_summary": payment_summary,
                "payment_trends": payment_trends,
                "outstanding_invoices": outstanding_invoices,
                "total_outstanding": sum(inv.get('outstanding_amount', 0) for inv in outstanding_invoices)
            }
        }
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Billing Summary Error: {frappe.get_traceback()}", "Billing Summary Error")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_patient_notebook_summary(patient_id, limit=10):
    """Get comprehensive notebook-style summary for patient"""
    try:
        # Get detailed appointment history with all relevant information
        notebook_entries = frappe.db.sql("""
            SELECT 
                appointment_date as date,
                appointment_time as time,
                practitioner as doctor,
                chief_complaint,
                practitioner_notes as notes,
                patient_notes,
                status,
                appointment_type,
                treatment_plan,
                special_instructions,
                estimated_cost,
                payment_status,
                cancellation_reason
            FROM `tabDental Appointment`
            WHERE patient = %s AND docstatus != 2
            ORDER BY appointment_date DESC, appointment_time DESC
            LIMIT %s
        """, (patient_id, limit), as_dict=True)
        
        # Enhance each entry with related data
        for entry in notebook_entries:
            # Get procedures performed on this date
            try:
                procedures = frappe.db.sql("""
                    SELECT 
                        tooth_number,
                        procedure_name,
                        status,
                        cost,
                        notes
                    FROM `tabTooth Procedure`
                    WHERE patient = %s AND DATE(date_completed) = %s
                    ORDER BY tooth_number
                """, (patient_id, entry.date), as_dict=True)
                entry['procedures'] = procedures
            except Exception:
                entry['procedures'] = []
            
            # Get findings/conditions recorded on this date
            try:
                findings = frappe.db.sql("""
                    SELECT 
                        tooth_number,
                        condition_name as finding,
                        severity,
                        notes,
                        status
                    FROM `tabTooth Condition`
                    WHERE patient = %s AND DATE(recorded_date) = %s
                    ORDER BY tooth_number
                """, (patient_id, entry.date), as_dict=True)
                entry['findings'] = findings
            except Exception:
                entry['findings'] = []
            
            # Get payments made on this date
            try:
                payments = frappe.db.sql("""
                    SELECT 
                        payment_amount,
                        payment_method,
                        reference_number,
                        notes
                    FROM `tabDental Payment Entry`
                    WHERE patient = %s AND posting_date = %s AND docstatus = 1
                """, (patient_id, entry.date), as_dict=True)
                entry['payments'] = payments
            except Exception:
                entry['payments'] = []
            
            # Calculate total procedures and findings for quick summary
            entry['procedure_count'] = len(entry.get('procedures', []))
            entry['finding_count'] = len(entry.get('findings', []))
            entry['payment_total'] = sum(p.get('payment_amount', 0) for p in entry.get('payments', []))
            
            # Generate a narrative summary
            entry['narrative_summary'] = generate_visit_narrative(entry)
        
        return {
            "success": True,
            "data": {
                "notebook_entries": notebook_entries,
                "total_entries": len(notebook_entries)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Notebook Summary Error: {frappe.get_traceback()}", "Notebook Summary Error")
        return {
            "success": False,
            "error": str(e)
        }

def generate_visit_narrative(entry):
    """Generate a narrative summary for a visit entry"""
    narrative_parts = []
    
    # Visit type and complaint
    if entry.get('chief_complaint'):
        narrative_parts.append(f"Patient presented with: {entry.chief_complaint}")
    
    # Procedures performed
    if entry.get('procedures'):
        procedure_list = []
        for proc in entry['procedures']:
            tooth_text = f"tooth {proc['tooth_number']}" if proc.get('tooth_number') else "multiple teeth"
            procedure_list.append(f"{proc['procedure_name']} on {tooth_text}")
        if procedure_list:
            narrative_parts.append(f"Procedures performed: {', '.join(procedure_list)}")
    
    # Findings
    if entry.get('findings'):
        finding_list = []
        for finding in entry['findings']:
            tooth_text = f"tooth {finding['tooth_number']}" if finding.get('tooth_number') else "multiple teeth"
            severity_text = f" ({finding['severity']})" if finding.get('severity') else ""
            finding_list.append(f"{finding['finding']} on {tooth_text}{severity_text}")
        if finding_list:
            narrative_parts.append(f"Findings: {', '.join(finding_list)}")
    
    # Treatment plan
    if entry.get('treatment_plan'):
        narrative_parts.append(f"Treatment plan: {entry.treatment_plan}")
    
    # Payment information
    if entry.get('payment_total') and entry['payment_total'] > 0:
        payment_methods = [p['payment_method'] for p in entry.get('payments', []) if p.get('payment_method')]
        payment_text = f"Payment received: ${entry['payment_total']:.2f}"
        if payment_methods:
            payment_text += f" ({', '.join(set(payment_methods))})"
        narrative_parts.append(payment_text)
    
    # Notes
    if entry.get('notes'):
        narrative_parts.append(f"Notes: {entry.notes}")
    
    return ". ".join(narrative_parts) + "." if narrative_parts else "Visit completed."
