# Test Data Generator for Dental ERP System
import frappe
from frappe.utils import getdate, add_days, add_months, nowtime, random_string
import random
from datetime import datetime, timedelta

@frappe.whitelist()
def generate_all_test_data():
    """Generate comprehensive test data for all components"""
    try:
        frappe.db.begin()
        
        # Clear existing test data
        clear_test_data()
        
        # Generate master data first
        generate_master_data()
        
        # Generate core entities
        generate_clinics()
        generate_practitioners()
        generate_patients()
        
        # Generate dental charts and conditions
        generate_dental_charts()
        
        # Generate appointments and procedures
        generate_appointments()
        
        # Generate treatment plans
        generate_treatment_plans()
        
        # Generate invoices and payments
        generate_invoices_and_payments()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Test data generated successfully",
            "data": get_test_data_summary()
        }
        
    except Exception as e:
        frappe.db.rollback()
        # Use shorter title for error logging to avoid length issues
        try:
            frappe.log_error(str(e), "Test Data Generation Failed")
        except:
            # If logging fails, just print the error
            print(f"❌ Test Data Generation Error: {str(e)}")
        
        return {
            "success": False,
            "error": str(e)
        }

def clear_test_data():
    """Clear existing test data"""
    test_doctypes = [
        "Payment Entry", "Invoice", "Invoice Item",
        "Treatment Plan Item", "Treatment Plan",
        "Appointment Procedure", "Dental Appointment",
        "Tooth Procedure", "Tooth Condition", "Dental Chart",
        "Dental Patient", "Dental Practitioner", "Dental Clinic"
    ]
    
    for doctype in test_doctypes:
        try:
            frappe.db.delete(doctype, {"name": ["like", "TEST-%"]})
        except:
            pass  # DocType might not exist yet

def generate_master_data():
    """Generate master data if not exists"""
    
    # Generate Tooth Masters (if not exists)
    try:
        if frappe.db.exists("DocType", "Tooth Master") and not frappe.db.exists("Tooth Master", {"universal_number": 11}):
            # Import the class and call the static method
            from dentcharts.dentcharts.doctype.tooth_master.tooth_master import ToothMaster
            result = ToothMaster.create_standard_teeth()
            print(f"✅ Tooth Master: {result}")
        else:
            print("⚠️  Tooth Master: DocType not found or teeth already exist")
    except ImportError as e:
        print(f"⚠️  Tooth Master creation skipped - Import error: {str(e)}")
    except Exception as e:
        print(f"⚠️  Tooth Master creation skipped - Error: {str(e)}")
    
    # Generate Dental Condition Masters
    try:
        if frappe.db.exists("DocType", "Dental Condition Master"):
            conditions = [
                {"condition_name": "Caries", "category": "Caries", "severity": "Medium", "color": "#FF6B6B", "is_emergency": 0},
                {"condition_name": "Pulpitis", "category": "Endodontic", "severity": "High", "color": "#FF4757", "is_emergency": 1},
                {"condition_name": "Gingivitis", "category": "Periodontal", "severity": "Low", "color": "#FFA726", "is_emergency": 0},
                {"condition_name": "Periodontitis", "category": "Periodontal", "severity": "High", "color": "#FF5722", "is_emergency": 0},
                {"condition_name": "Abscess", "category": "Endodontic", "severity": "Critical", "color": "#D32F2F", "is_emergency": 1},
                {"condition_name": "Fracture", "category": "Trauma", "severity": "High", "color": "#7B1FA2", "is_emergency": 1},
                {"condition_name": "Wear", "category": "Attrition", "severity": "Low", "color": "#795548", "is_emergency": 0},
                {"condition_name": "Staining", "category": "Cosmetic", "severity": "Low", "color": "#607D8B", "is_emergency": 0}
            ]
            
            created_conditions = 0
            for condition in conditions:
                if not frappe.db.exists("Dental Condition Master", condition["condition_name"]):
                    doc = frappe.get_doc({
                        "doctype": "Dental Condition Master",
                        "condition_name": condition["condition_name"],
                        "category": condition["category"],
                        "severity": condition["severity"],
                        "color": condition["color"],
                        "is_emergency": condition["is_emergency"],
                        "description": f"Test condition: {condition['condition_name']}"
                    })
                    doc.insert()
                    created_conditions += 1
            
            print(f"✅ Dental Conditions: Created {created_conditions} conditions")
        else:
            print("⚠️  Dental Condition Master: DocType not found")
    except Exception as e:
        print(f"⚠️  Dental Condition Master creation skipped: {str(e)}")
    
    # Generate Dental Procedure Masters
    try:
        if frappe.db.exists("DocType", "Dental Procedure Master"):
            procedures = [
                {"procedure_name": "Cleaning", "category": "Preventive", "estimated_cost": 120, "estimated_duration": 30},
                {"procedure_name": "Filling", "category": "Restorative", "estimated_cost": 180, "estimated_duration": 45},
                {"procedure_name": "Crown", "category": "Restorative", "estimated_cost": 800, "estimated_duration": 90},
                {"procedure_name": "Root Canal", "category": "Endodontic", "estimated_cost": 1200, "estimated_duration": 120},
                {"procedure_name": "Extraction", "category": "Surgical", "estimated_cost": 200, "estimated_duration": 30},
                {"procedure_name": "Bridge", "category": "Prosthodontic", "estimated_cost": 2400, "estimated_duration": 180},
                {"procedure_name": "Implant", "category": "Surgical", "estimated_cost": 3500, "estimated_duration": 120},
                {"procedure_name": "Whitening", "category": "Cosmetic", "estimated_cost": 400, "estimated_duration": 60},
                {"procedure_name": "Scaling", "category": "Periodontal", "estimated_cost": 150, "estimated_duration": 45},
                {"procedure_name": "Fluoride Treatment", "category": "Preventive", "estimated_cost": 50, "estimated_duration": 15}
            ]
            
            created_procedures = 0
            for procedure in procedures:
                if not frappe.db.exists("Dental Procedure Master", procedure["procedure_name"]):
                    doc = frappe.get_doc({
                        "doctype": "Dental Procedure Master",
                        "procedure_name": procedure["procedure_name"],
                        "procedure_category": procedure["category"],
                        "estimated_cost": procedure["estimated_cost"],
                        "estimated_duration": procedure["estimated_duration"],
                        "description": f"Standard {procedure['procedure_name'].lower()} procedure",
                        "insurance_covered": 1 if procedure["category"] in ["Preventive", "Restorative"] else 0
                    })
                    doc.insert()
                    created_procedures += 1
            
            print(f"✅ Dental Procedures: Created {created_procedures} procedures")
        else:
            print("⚠️  Dental Procedure Master: DocType not found")
    except Exception as e:
        print(f"⚠️  Dental Procedure Master creation skipped: {str(e)}")

def generate_clinics():
    """Generate test dental clinics"""
    clinics = [
        {
            "clinic_name": "TEST-Bright Smile Dental Center",
            "clinic_code": "TEST-BSDC",
            "address": "123 Main Street, Downtown",
            "phone": "+1-555-0101",
            "email": "info@brightsmile.test",
            "license_number": "TEST-LIC-001",
            "established_date": "2020-01-15"
        },
        {
            "clinic_name": "TEST-Family Dental Care",
            "clinic_code": "TEST-FDC",
            "address": "456 Oak Avenue, Suburbia",
            "phone": "+1-555-0202",
            "email": "contact@familydental.test",
            "license_number": "TEST-LIC-002",
            "established_date": "2018-06-20"
        }
    ]
    
    for clinic_data in clinics:
        doc = frappe.get_doc({
            "doctype": "Dental Clinic",
            **clinic_data,
            "status": "Active",
            "default_currency": "USD"
        })
        doc.insert()

def generate_practitioners():
    """Generate test dental practitioners"""
    
    # First create Healthcare Practitioners
    practitioners = [
        {
            "practitioner_name": "Dr. Sarah Johnson",
            "specialization": "General Dentistry",
            "license": "TEST-DDS-001",
            "consultation_fee": 200
        },
        {
            "practitioner_name": "Dr. Michael Chen",
            "specialization": "Orthodontics",
            "license": "TEST-DDS-002",
            "consultation_fee": 300
        },
        {
            "practitioner_name": "Dr. Emily Rodriguez",
            "specialization": "Oral Surgery",
            "license": "TEST-DDS-003",
            "consultation_fee": 400
        },
        {
            "practitioner_name": "Dr. David Wilson",
            "specialization": "Periodontics",
            "license": "TEST-DDS-004",
            "consultation_fee": 350
        }
    ]
    
    clinic = frappe.get_doc("Dental Clinic", {"clinic_code": "TEST-BSDC"})
    
    for prac_data in practitioners:
        # Create Healthcare Practitioner
        healthcare_prac = frappe.get_doc({
            "doctype": "Healthcare Practitioner",
            "first_name": prac_data["practitioner_name"].split()[1],
            "last_name": prac_data["practitioner_name"].split()[2],
            "practitioner_name": prac_data["practitioner_name"],
            "mobile": f"+1-555-{random.randint(1000, 9999)}",
            "email": f"{prac_data['practitioner_name'].lower().replace(' ', '.').replace('dr.', '')}@test.com"
        })
        healthcare_prac.insert()
        
        # Create Dental Practitioner
        dental_prac = frappe.get_doc({
            "doctype": "Dental Practitioner",
            "practitioner_name": prac_data["practitioner_name"],
            "healthcare_practitioner": healthcare_prac.name,
            "dental_license_number": prac_data["license"],
            "specialization": prac_data["specialization"],
            "years_of_experience": random.randint(5, 20),
            "consultation_fee": prac_data["consultation_fee"],
            "clinic": clinic.name
        })
        dental_prac.insert()

def generate_patients():
    """Generate test patients"""
    
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "James", "Maria", 
                   "William", "Jennifer", "Richard", "Patricia", "Charles", "Linda", "Christopher", "Barbara",
                   "Daniel", "Elizabeth", "Matthew", "Jessica", "Anthony", "Susan", "Mark", "Karen"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
                  "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
                  "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris"]
    
    for i in range(50):  # Generate 50 test patients
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Create Healthcare Patient first
        birth_date = getdate() - timedelta(days=random.randint(18*365, 80*365))
        
        healthcare_patient = frappe.get_doc({
            "doctype": "Patient",
            "first_name": first_name,
            "last_name": last_name,
            "patient_name": f"{first_name} {last_name}",
            "gender": random.choice(["Male", "Female"]),
            "dob": birth_date,
            "mobile": f"+1-555-{random.randint(1000, 9999)}",
            "email": f"{first_name.lower()}.{last_name.lower()}@test.com"
        })
        healthcare_patient.insert()
        
        # Create Dental Patient
        dental_patient = frappe.get_doc({
            "doctype": "Dental Patient",
            "patient_name": f"{first_name} {last_name}",
            "healthcare_patient": healthcare_patient.name,
            "dental_history": random.choice([
                "Regular checkups, no major issues",
                "Previous fillings, good oral hygiene",
                "History of gum disease, improved with treatment",
                "Orthodontic treatment completed",
                "Previous root canal treatment"
            ]),
            "dental_allergies": random.choice(["None", "Latex", "Penicillin", "Local anesthetics", ""]),
            "emergency_contact": f"Emergency Contact {i+1}",
            "emergency_phone": f"+1-555-{random.randint(5000, 9999)}",
            "preferred_dentist": random.choice(frappe.get_all("Dental Practitioner", pluck="name"))
        })
        dental_patient.insert()

def generate_dental_charts():
    """Generate dental charts and conditions"""
    patients = frappe.get_all("Dental Patient", pluck="name")
    practitioners = frappe.get_all("Dental Practitioner", pluck="name")
    conditions = frappe.get_all("Dental Condition Master", pluck="name")
    
    for patient in patients[:30]:  # Generate charts for first 30 patients
        # Create Dental Chart
        chart = frappe.get_doc({
            "doctype": "Dental Chart",
            "patient": patient,
            "chart_date": getdate() - timedelta(days=random.randint(1, 365)),
            "practitioner": random.choice(practitioners),
            "status": "Active",
            "notes": f"Initial dental chart for {patient}"
        })
        chart.insert()
        
        # Add some tooth conditions (randomly)
        teeth = frappe.get_all("Tooth Master", pluck="name")
        for _ in range(random.randint(1, 5)):  # 1-5 conditions per patient
            tooth_condition = frappe.get_doc({
                "doctype": "Tooth Condition",
                "dental_chart": chart.name,
                "patient": patient,
                "tooth": random.choice(teeth),
                "condition": random.choice(conditions),
                "identified_date": chart.chart_date,
                "severity": random.choice(["Low", "Medium", "High"]),
                "notes": "Test condition identified during examination"
            })
            tooth_condition.insert()

def generate_appointments():
    """Generate dental appointments"""
    patients = frappe.get_all("Dental Patient", pluck="name")
    practitioners = frappe.get_all("Dental Practitioner", pluck="name")
    procedures = frappe.get_all("Dental Procedure Master", pluck="name")
    
    # Generate appointments for the last 6 months and next 2 months
    start_date = getdate() - timedelta(days=180)
    end_date = getdate() + timedelta(days=60)
    
    appointment_count = 0
    current_date = start_date
    
    while current_date <= end_date and appointment_count < 200:
        # Skip weekends
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            # Generate 8-12 appointments per day
            daily_appointments = random.randint(8, 12)
            
            for _ in range(daily_appointments):
                appointment_time = f"{random.randint(8, 17):02d}:{random.choice(['00', '30']):02d}:00"
                
                # Determine status based on date
                if current_date < getdate():
                    status = random.choice(["Completed", "Completed", "Completed", "Cancelled"])
                elif current_date == getdate():
                    status = random.choice(["Scheduled", "Checked In", "In Progress", "Completed"])
                else:
                    status = "Scheduled"
                
                appointment = frappe.get_doc({
                    "doctype": "Dental Appointment",
                    "patient": random.choice(patients),
                    "practitioner": random.choice(practitioners),
                    "appointment_date": current_date,
                    "appointment_time": appointment_time,
                    "status": status,
                    "appointment_type": random.choice(["Routine Checkup", "Follow-up", "Emergency", "Consultation"]),
                    "duration": random.choice([30, 45, 60, 90]),
                    "notes": f"Test appointment for {current_date}"
                })
                appointment.insert()
                
                # Add appointment procedures
                num_procedures = random.randint(1, 3)
                for _ in range(num_procedures):
                    procedure = frappe.get_doc({
                        "doctype": "Appointment Procedure",
                        "appointment": appointment.name,
                        "procedure": random.choice(procedures),
                        "estimated_duration": random.choice([15, 30, 45, 60]),
                        "estimated_cost": random.randint(100, 500),
                        "status": "Planned" if status == "Scheduled" else "Completed"
                    })
                    procedure.insert()
                
                appointment_count += 1
        
        current_date += timedelta(days=1)

def generate_treatment_plans():
    """Generate treatment plans"""
    patients = frappe.get_all("Dental Patient", pluck="name")
    practitioners = frappe.get_all("Dental Practitioner", pluck="name")
    procedures = frappe.get_all("Dental Procedure Master", pluck="name")
    
    for patient in patients[:20]:  # Generate treatment plans for first 20 patients
        plan = frappe.get_doc({
            "doctype": "Treatment Plan",
            "patient": patient,
            "practitioner": random.choice(practitioners),
            "plan_date": getdate() - timedelta(days=random.randint(1, 180)),
            "status": random.choice(["Draft", "Approved", "In Progress", "Completed"]),
            "total_estimated_cost": 0,
            "description": f"Comprehensive treatment plan for {patient}",
            "is_emergency": random.choice([0, 0, 0, 1])  # 25% emergency plans
        })
        plan.insert()
        
        # Add treatment plan items
        total_cost = 0
        num_items = random.randint(2, 6)
        
        for sequence in range(1, num_items + 1):
            procedure_master = frappe.get_doc("Dental Procedure Master", random.choice(procedures))
            estimated_cost = procedure_master.estimated_cost * random.uniform(0.8, 1.2)  # Vary cost slightly
            
            plan_item = frappe.get_doc({
                "doctype": "Treatment Plan Item",
                "treatment_plan": plan.name,
                "procedure": procedure_master.name,
                "sequence": sequence,
                "estimated_cost": estimated_cost,
                "estimated_duration": procedure_master.estimated_duration,
                "status": random.choice(["Planned", "Scheduled", "Completed"]),
                "notes": f"Treatment item {sequence} for plan"
            })
            plan_item.insert()
            total_cost += estimated_cost
        
        # Update plan total
        plan.total_estimated_cost = total_cost
        plan.save()

def generate_invoices_and_payments():
    """Generate invoices and payments"""
    completed_appointments = frappe.get_all(
        "Dental Appointment", 
        filters={"status": "Completed"},
        pluck="name"
    )
    
    for appointment_name in completed_appointments[:100]:  # Generate invoices for first 100 completed appointments
        appointment = frappe.get_doc("Dental Appointment", appointment_name)
        
        # Create Invoice
        invoice = frappe.get_doc({
            "doctype": "Invoice",
            "patient": appointment.patient,
            "practitioner": appointment.practitioner,
            "posting_date": appointment.appointment_date,
            "due_date": appointment.appointment_date + timedelta(days=30),
            "appointment": appointment.name,
            "status": "Submitted",
            "currency": "USD"
        })
        
        # Add invoice items from appointment procedures
        appointment_procedures = frappe.get_all(
            "Appointment Procedure",
            filters={"appointment": appointment.name},
            fields=["procedure", "estimated_cost"]
        )
        
        total = 0
        for proc in appointment_procedures:
            procedure_master = frappe.get_doc("Dental Procedure Master", proc.procedure)
            
            invoice_item = frappe.get_doc({
                "doctype": "Invoice Item",
                "parent": invoice.name,
                "parenttype": "Invoice",
                "parentfield": "items",
                "item_name": procedure_master.procedure_name,
                "description": f"{procedure_master.procedure_name} - {procedure_master.description}",
                "quantity": 1,
                "rate": proc.estimated_cost,
                "amount": proc.estimated_cost
            })
            invoice.append("items", invoice_item)
            total += proc.estimated_cost
        
        invoice.total = total
        invoice.grand_total = total
        invoice.outstanding_amount = total
        invoice.insert()
        
        # Create payment (80% of invoices get paid)
        if random.random() < 0.8:
            payment_amount = total
            if random.random() < 0.2:  # 20% partial payments
                payment_amount = total * random.uniform(0.3, 0.8)
            
            payment = frappe.get_doc({
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": appointment.patient,
                "posting_date": appointment.appointment_date + timedelta(days=random.randint(0, 15)),
                "paid_amount": payment_amount,
                "received_amount": payment_amount,
                "mode_of_payment": random.choice(["Cash", "Credit Card", "Check", "Insurance", "Bank Transfer"]),
                "reference_no": f"PAY-{random.randint(10000, 99999)}",
                "reference_date": appointment.appointment_date,
                "invoice": invoice.name
            })
            payment.insert()
            
            # Update invoice outstanding
            invoice.outstanding_amount = total - payment_amount
            invoice.save()

def get_test_data_summary():
    """Get summary of generated test data"""
    summary = {}
    
    doctypes = [
        "Dental Clinic", "Dental Practitioner", "Dental Patient",
        "Dental Chart", "Tooth Condition", "Dental Appointment",
        "Appointment Procedure", "Treatment Plan", "Treatment Plan Item",
        "Invoice", "Invoice Item", "Payment Entry"
    ]
    
    for doctype in doctypes:
        try:
            count = frappe.db.count(doctype)
            summary[doctype] = count
        except:
            summary[doctype] = 0
    
    return summary

@frappe.whitelist()
def generate_sample_data_for_testing():
    """Generate minimal sample data for quick testing"""
    try:
        frappe.db.begin()
        
        # Generate just essential data for testing
        generate_master_data()
        
        # Create one clinic
        if not frappe.db.exists("Dental Clinic", {"clinic_code": "TEST-MAIN"}):
            clinic = frappe.get_doc({
                "doctype": "Dental Clinic",
                "clinic_name": "TEST-Main Dental Clinic",
                "clinic_code": "TEST-MAIN",
                "address": "123 Test Street",
                "phone": "+1-555-0100",
                "email": "test@dental.com",
                "license_number": "TEST-LIC-MAIN",
                "established_date": getdate(),
                "status": "Active",
                "default_currency": "USD"
            })
            clinic.insert()
        
        # Create one practitioner
        if not frappe.db.exists("Healthcare Practitioner", {"practitioner_name": "Dr. Test Dentist"}):
            healthcare_prac = frappe.get_doc({
                "doctype": "Healthcare Practitioner",
                "first_name": "Test",
                "last_name": "Dentist",
                "practitioner_name": "Dr. Test Dentist",
                "mobile": "+1-555-0001",
                "email": "test.dentist@test.com"
            })
            healthcare_prac.insert()
            
            dental_prac = frappe.get_doc({
                "doctype": "Dental Practitioner",
                "practitioner_name": "Dr. Test Dentist",
                "healthcare_practitioner": healthcare_prac.name,
                "dental_license_number": "TEST-DDS-MAIN",
                "specialization": "General Dentistry",
                "years_of_experience": 10,
                "consultation_fee": 200
            })
            dental_prac.insert()
        
        # Create a few patients
        for i in range(5):
            patient_name = f"Test Patient {i+1}"
            if not frappe.db.exists("Patient", {"patient_name": patient_name}):
                healthcare_patient = frappe.get_doc({
                    "doctype": "Patient",
                    "first_name": "Test",
                    "last_name": f"Patient{i+1}",
                    "patient_name": patient_name,
                    "gender": "Male" if i % 2 == 0 else "Female",
                    "dob": getdate() - timedelta(days=(25 + i*5)*365),
                    "mobile": f"+1-555-000{i+2}",
                    "email": f"test.patient{i+1}@test.com"
                })
                healthcare_patient.insert()
                
                dental_patient = frappe.get_doc({
                    "doctype": "Dental Patient",
                    "patient_name": patient_name,
                    "healthcare_patient": healthcare_patient.name,
                    "dental_history": "Test patient dental history",
                    "emergency_contact": f"Emergency Contact {i+1}",
                    "emergency_phone": f"+1-555-900{i+1}"
                })
                dental_patient.insert()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Sample test data generated successfully"
        }
        
    except Exception as e:
        frappe.db.rollback()
        # Use shorter title for error logging to avoid length issues
        try:
            frappe.log_error(str(e), "Sample Data Error")
        except:
            # If logging fails, just print the error
            print(f"❌ Sample Data Generation Error: {str(e)}")
        
        return {
            "success": False,
            "error": str(e)
        } 