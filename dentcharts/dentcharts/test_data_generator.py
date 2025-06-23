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
        
        # Generate tooth procedures for treatment success metrics
        generate_tooth_procedures()
        
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
        "Tooth Procedure", "Appointment Procedure", "Dental Appointment",
        "Tooth Condition", "Dental Chart",
        "Dental Patient", "Dental Practitioner", "Dental Clinic",
        "Patient", "Healthcare Practitioner"  # Add base doctypes
    ]
    
    for doctype in test_doctypes:
        try:
            # Delete records that start with TEST-
            if frappe.db.exists("DocType", doctype):
                test_records = frappe.get_all(doctype, 
                    filters=[["name", "like", "TEST-%"]], 
                    pluck="name")
                
                for record in test_records:
                    try:
                        frappe.delete_doc(doctype, record, force=True)
                    except:
                        pass
                        
                # Also delete by other test patterns
                if doctype in ["Patient", "Healthcare Practitioner"]:
                    test_records = frappe.get_all(doctype, 
                        filters=[["first_name", "like", "Test%"]], 
                        pluck="name")
                    
                    for record in test_records:
                        try:
                            frappe.delete_doc(doctype, record, force=True)
                        except:
                            pass
                            
        except Exception as e:
            print(f"⚠️  Error clearing {doctype}: {str(e)}")
            pass  # Continue with other doctypes

def generate_master_data():
    """Generate master data if not exists"""
    
    # Generate Tooth Masters (if not exists)
    try:
        if frappe.db.exists("DocType", "Tooth Master"):
            existing_teeth = frappe.db.count("Tooth Master")
            if existing_teeth < 32:
                # Import the class and call the static method
                from dentcharts.dentcharts.doctype.tooth_master.tooth_master import ToothMaster
                result = ToothMaster.create_standard_teeth()
                print(f"✅ Tooth Master: {result}")
            else:
                print(f"⚠️  Tooth Master: {existing_teeth} teeth already exist")
        else:
            print("⚠️  Tooth Master: DocType not found")
    except ImportError as e:
        print(f"⚠️  Tooth Master creation skipped - Import error: {str(e)}")
    except Exception as e:
        print(f"⚠️  Tooth Master creation skipped - Error: {str(e)}")
    
    # Generate Dental Condition Masters
    try:
        if frappe.db.exists("DocType", "Dental Condition Master"):
            conditions = [
                {"condition_code": "TEST-CAR001", "condition_name": "Test Caries", "category": "Caries", "severity": "Medium", "color_code": "#FF6B6B", "is_emergency": 0},
                {"condition_code": "TEST-END001", "condition_name": "Test Pulpitis", "category": "Endodontic", "severity": "High", "color_code": "#FF4757", "is_emergency": 1},
                {"condition_code": "TEST-PER001", "condition_name": "Test Gingivitis", "category": "Periodontal", "severity": "Low", "color_code": "#FFA726", "is_emergency": 0},
                {"condition_code": "TEST-PER002", "condition_name": "Test Periodontitis", "category": "Periodontal", "severity": "High", "color_code": "#FF5722", "is_emergency": 0},
                {"condition_code": "TEST-END002", "condition_name": "Test Abscess", "category": "Endodontic", "severity": "Critical", "color_code": "#D32F2F", "is_emergency": 1},
                {"condition_code": "TEST-TRA001", "condition_name": "Test Fracture", "category": "Other", "severity": "High", "color_code": "#7B1FA2", "is_emergency": 1},
                {"condition_code": "TEST-OTH001", "condition_name": "Test Wear", "category": "Other", "severity": "Low", "color_code": "#795548", "is_emergency": 0},
                {"condition_code": "TEST-COS001", "condition_name": "Test Staining", "category": "Cosmetic", "severity": "Low", "color_code": "#607D8B", "is_emergency": 0}
            ]
            
            created_conditions = 0
            for condition in conditions:
                if not frappe.db.exists("Dental Condition Master", condition["condition_code"]):
                    try:
                        doc = frappe.get_doc({
                            "doctype": "Dental Condition Master",
                            "condition_code": condition["condition_code"],
                            "condition_name": condition["condition_name"],
                            "category": condition["category"],
                            "severity": condition["severity"],
                            "color_code": condition["color_code"],
                            "is_emergency": condition["is_emergency"],
                            "description": f"Test condition: {condition['condition_name']}"
                        })
                        doc.insert()
                        created_conditions += 1
                    except Exception as e:
                        print(f"⚠️  Error creating condition {condition['condition_code']}: {str(e)}")
            
            print(f"✅ Dental Conditions: Created {created_conditions} conditions")
        else:
            print("⚠️  Dental Condition Master: DocType not found")
    except Exception as e:
        print(f"⚠️  Dental Condition Master creation skipped: {str(e)}")
    
    # Generate Dental Procedure Masters
    try:
        if frappe.db.exists("DocType", "Dental Procedure Master"):
            procedures = [
                {"procedure_code": "TEST-PRE001", "procedure_name": "Test Cleaning", "category": "Preventive", "complexity": "Simple", "standard_fee": 120, "duration_minutes": 30},
                {"procedure_code": "TEST-RES001", "procedure_name": "Test Filling", "category": "Restorative", "complexity": "Simple", "standard_fee": 180, "duration_minutes": 45},
                {"procedure_code": "TEST-RES002", "procedure_name": "Test Crown", "category": "Restorative", "complexity": "Complex", "standard_fee": 800, "duration_minutes": 90},
                {"procedure_code": "TEST-END001", "procedure_name": "Test Root Canal", "category": "Endodontic", "complexity": "Advanced", "standard_fee": 1200, "duration_minutes": 120},
                {"procedure_code": "TEST-SUR001", "procedure_name": "Test Extraction", "category": "Oral Surgery", "complexity": "Moderate", "standard_fee": 200, "duration_minutes": 30},
                {"procedure_code": "TEST-PRO001", "procedure_name": "Test Bridge", "category": "Prosthodontic", "complexity": "Advanced", "standard_fee": 2400, "duration_minutes": 180},
                {"procedure_code": "TEST-SUR002", "procedure_name": "Test Implant", "category": "Oral Surgery", "complexity": "Advanced", "standard_fee": 3500, "duration_minutes": 120},
                {"procedure_code": "TEST-COS001", "procedure_name": "Test Whitening", "category": "Cosmetic", "complexity": "Simple", "standard_fee": 400, "duration_minutes": 60},
                {"procedure_code": "TEST-PER001", "procedure_name": "Test Scaling", "category": "Periodontal", "complexity": "Simple", "standard_fee": 150, "duration_minutes": 45},
                {"procedure_code": "TEST-PRE002", "procedure_name": "Test Fluoride Treatment", "category": "Preventive", "complexity": "Simple", "standard_fee": 50, "duration_minutes": 15}
            ]
            
            created_procedures = 0
            for procedure in procedures:
                if not frappe.db.exists("Dental Procedure Master", procedure["procedure_code"]):
                    try:
                        doc = frappe.get_doc({
                            "doctype": "Dental Procedure Master",
                            "procedure_code": procedure["procedure_code"],
                            "procedure_name": procedure["procedure_name"],
                            "category": procedure["category"],
                            "complexity": procedure["complexity"],
                            "standard_fee": procedure["standard_fee"],
                            "duration_minutes": procedure["duration_minutes"],
                            "description": f"Standard {procedure['procedure_name'].lower()} procedure"
                        })
                        doc.insert()
                        created_procedures += 1
                    except Exception as e:
                        print(f"⚠️  Error creating procedure {procedure['procedure_code']}: {str(e)}")
            
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
    """Generate test dental patients"""
    
    # Sample patient data with unique identifiers
    patients_data = [
        {"first_name": "John", "last_name": "Smith", "sex": "Male", "age_years": 35},
        {"first_name": "Sarah", "last_name": "Johnson", "sex": "Female", "age_years": 28},
        {"first_name": "Michael", "last_name": "Brown", "sex": "Male", "age_years": 42},
        {"first_name": "Emily", "last_name": "Davis", "sex": "Female", "age_years": 31},
        {"first_name": "David", "last_name": "Wilson", "sex": "Male", "age_years": 55},
        {"first_name": "Lisa", "last_name": "Miller", "sex": "Female", "age_years": 39},
        {"first_name": "Robert", "last_name": "Garcia", "sex": "Male", "age_years": 47},
        {"first_name": "Jennifer", "last_name": "Martinez", "sex": "Female", "age_years": 33},
        {"first_name": "William", "last_name": "Anderson", "sex": "Male", "age_years": 29},
        {"first_name": "Amanda", "last_name": "Taylor", "sex": "Female", "age_years": 36}
    ]
    
    created_patients = 0
    for i, patient_data in enumerate(patients_data):
        patient_name = f"TEST-{patient_data['first_name']} {patient_data['last_name']}"
        
        # Skip if patient already exists
        if frappe.db.exists("Patient", {"patient_name": patient_name}):
            continue
            
        try:
            # Create Healthcare Patient (base patient record)
            dob = getdate() - timedelta(days=patient_data['age_years'] * 365)
            
            healthcare_patient = frappe.get_doc({
                "doctype": "Patient",
                "first_name": patient_data['first_name'],
                "last_name": patient_data['last_name'],
                "patient_name": patient_name,
                "sex": patient_data['sex'],
                "dob": dob,
                "mobile": f"+1-555-{1000 + i:04d}",  # Unique mobile numbers
                "email": f"test.patient.{i+1}@testdental.com",  # Unique emails
                "customer_group": "Individual",
                "territory": "United States"
            })
            healthcare_patient.insert()
            
            # Create Dental Patient (extended patient record)
            dental_patient = frappe.get_doc({
                "doctype": "Dental Patient",
                "patient_name": patient_name,
                "healthcare_patient": healthcare_patient.name,
                "dental_history": f"Patient has regular dental checkups. Age: {patient_data['age_years']}",
                "emergency_contact": f"Emergency Contact for {patient_data['first_name']}",
                "emergency_phone": f"+1-555-{9000 + i:04d}",
                "insurance_provider": random.choice(["Delta Dental", "Blue Cross", "Aetna", "MetLife", "None"]),
                "preferred_appointment_time": random.choice(["Morning", "Afternoon", "Evening"])
            })
            dental_patient.insert()
            created_patients += 1
            
        except Exception as e:
            print(f"⚠️  Error creating patient {patient_name}: {str(e)}")
            continue
    
    print(f"✅ Patients: Created {created_patients} patients")

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

def generate_tooth_procedures():
    """Generate Tooth Procedure records for treatment success metrics"""
    try:
        patients = frappe.get_all("Dental Patient", pluck="name")
        practitioners = frappe.get_all("Healthcare Practitioner", pluck="name")
        procedures = frappe.get_all("Dental Procedure Master", pluck="name")
        teeth = frappe.get_all("Tooth Master", pluck="name")
        
        if not (patients and practitioners and procedures and teeth):
            print("⚠️  Tooth Procedures: Missing required master data")
            return
        
        # Generate procedures for the last 6 months
        start_date = getdate() - timedelta(days=180)
        end_date = getdate()
        
        procedure_count = 0
        for _ in range(300):  # Generate 300 tooth procedures
            procedure_master = frappe.get_doc("Dental Procedure Master", random.choice(procedures))
            
            # Random dates for procedures
            procedure_date = start_date + timedelta(days=random.randint(0, 180))
            
            # Determine status based on date
            if procedure_date < getdate() - timedelta(days=30):
                status = random.choice(["Completed", "Completed", "Completed", "Cancelled"])
            elif procedure_date < getdate():
                status = random.choice(["Completed", "In Progress"])
            else:
                status = "Planned"
            
            # Calculate dates
            planned_date = procedure_date
            completed_date = None
            if status == "Completed":
                # Completed 0-7 days after planned date
                completed_date = planned_date + timedelta(days=random.randint(0, 7))
            
            # Calculate fees
            standard_fee = procedure_master.standard_fee
            actual_fee = standard_fee * random.uniform(0.8, 1.2) if status == "Completed" else None
            
            # Add some complications (10% chance)
            notes = f"Procedure performed on {procedure_date.strftime('%Y-%m-%d')}"
            if random.random() < 0.1:
                notes += ". Minor complication noted during procedure."
            elif random.random() < 0.05:
                notes += ". Problem with healing, follow-up required."
            
            tooth_procedure = frappe.get_doc({
                "doctype": "Tooth Procedure",
                "tooth_number": random.choice(teeth),
                "procedure_code": procedure_master.name,
                "surface": random.choice(["Whole Tooth", "Occlusal", "Mesial", "Distal", "Buccal", "Lingual"]),
                "status": status,
                "planned_date": planned_date,
                "completed_date": completed_date,
                "planned_by": "Administrator",
                "performed_by": random.choice(practitioners) if status in ["Completed", "In Progress"] else None,
                "duration_minutes": procedure_master.duration_minutes,
                "standard_fee": standard_fee,
                "actual_fee": actual_fee,
                "insurance_covered": actual_fee * random.uniform(0.0, 0.8) if actual_fee else 0,
                "notes": notes,
                "follow_up_required": random.choice([0, 0, 0, 1])  # 25% need follow-up
            })
            
            # Set follow-up date if required
            if tooth_procedure.follow_up_required and completed_date:
                tooth_procedure.follow_up_date = completed_date + timedelta(days=random.randint(7, 30))
            
            tooth_procedure.insert()
            procedure_count += 1
        
        print(f"✅ Tooth Procedures: Created {procedure_count} procedures")
        
    except Exception as e:
        print(f"⚠️  Tooth Procedures creation failed: {str(e)}")

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
            estimated_cost = procedure_master.standard_fee * random.uniform(0.8, 1.2)  # Vary cost slightly
            
            plan_item = frappe.get_doc({
                "doctype": "Treatment Plan Item",
                "treatment_plan": plan.name,
                "procedure": procedure_master.name,
                "sequence": sequence,
                "estimated_cost": estimated_cost,
                "estimated_duration": procedure_master.duration_minutes,
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
        
        # Create Invoice with correct field names
        invoice = frappe.get_doc({
            "doctype": "Invoice",
            "patient": appointment.patient,
            "practitioner": appointment.practitioner,
            "invoice_date": appointment.appointment_date,  # Changed from posting_date
            "due_date": add_days(appointment.appointment_date, 30),  # Use add_days function
            "appointment_reference": appointment.name,  # Changed from appointment
            "invoice_status": "Sent",  # Changed from status
            "priority": "Normal"
        })
        
        # Add invoice items from appointment procedures
        appointment_procedures = frappe.get_all(
            "Appointment Procedure",
            filters={"appointment": appointment.name},
            fields=["procedure", "estimated_cost"]
        )
        
        subtotal = 0
        for proc in appointment_procedures:
            procedure_master = frappe.get_doc("Dental Procedure Master", proc.procedure)
            
            # Create invoice item as child table entry
            invoice.append("invoice_items", {
                "item_description": procedure_master.procedure_name,
                "procedure_code": procedure_master.procedure_code,
                "quantity": 1,
                "unit_price": proc.estimated_cost,
                "total_price": proc.estimated_cost
            })
            subtotal += proc.estimated_cost
        
        # Calculate totals with correct field names
        tax_amount = subtotal * 0.08  # 8% tax
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal + tax_amount  # Changed from grand_total
        invoice.outstanding_amount = subtotal + tax_amount
        invoice.patient_portion = subtotal + tax_amount
        
        invoice.insert()
        
        # Create payment (80% of invoices get paid)
        if random.random() < 0.8:
            payment_amount = invoice.total_amount
            if random.random() < 0.2:  # 20% partial payments
                payment_amount = invoice.total_amount * random.uniform(0.3, 0.8)
            
            payment = frappe.get_doc({
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": appointment.patient,
                "posting_date": add_days(appointment.appointment_date, random.randint(0, 15)),
                "paid_amount": payment_amount,
                "received_amount": payment_amount,
                "mode_of_payment": random.choice(["Cash", "Credit Card", "Check", "Insurance", "Bank Transfer"]),
                "reference_no": f"PAY-{random.randint(10000, 99999)}",
                "reference_date": appointment.appointment_date
            })
            payment.insert()
            
            # Update invoice outstanding
            invoice.outstanding_amount = invoice.total_amount - payment_amount
            invoice.payment_status = "Paid" if payment_amount >= invoice.total_amount else "Partially Paid"
            invoice.paid_amount = payment_amount
            invoice.save()

def get_test_data_summary():
    """Get summary of generated test data"""
    summary = {}
    
    doctypes = [
        "Dental Clinic", "Dental Practitioner", "Dental Patient",
        "Dental Chart", "Tooth Condition", "Tooth Procedure", "Dental Appointment",
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
                    "sex": "Male" if i % 2 == 0 else "Female",
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

@frappe.whitelist()
def generate_simple_test_data():
    """Generate minimal test data without user conflicts"""
    try:
        frappe.db.begin()
        
        print("🧪 Starting simple test data generation...")
        
        # 1. Generate master data
        generate_master_data()
        
        # 2. Create one clinic (if not exists)
        if not frappe.db.exists("Dental Clinic", {"clinic_code": "TEST-SIMPLE"}):
            clinic = frappe.get_doc({
                "doctype": "Dental Clinic",
                "clinic_name": "TEST-Simple Dental Clinic",
                "clinic_code": "TEST-SIMPLE",
                "address": "123 Test Street",
                "phone": "+1-555-0100",
                "email": "test@simpledental.com",
                "license_number": "TEST-LIC-SIMPLE",
                "established_date": getdate(),
                "status": "Active",
                "default_currency": "USD"
            })
            clinic.insert()
            print("✅ Created test clinic")
        
        # 3. Create one healthcare practitioner (if not exists)
        if not frappe.db.exists("Healthcare Practitioner", {"first_name": "Test", "last_name": "Dentist"}):
            healthcare_prac = frappe.get_doc({
                "doctype": "Healthcare Practitioner",
                "first_name": "Test",
                "last_name": "Dentist",
                "practitioner_name": "Dr. Test Dentist",
                "mobile": "+1-555-9999",
                "email": "test.dentist@simpledental.com"
            })
            healthcare_prac.insert()
            
            dental_prac = frappe.get_doc({
                "doctype": "Dental Practitioner",
                "practitioner_name": "Dr. Test Dentist",
                "healthcare_practitioner": healthcare_prac.name,
                "dental_license_number": "TEST-DDS-SIMPLE",
                "specialization": "General Dentistry",
                "years_of_experience": 10,
                "consultation_fee": 200
            })
            dental_prac.insert()
            print("✅ Created test practitioner")
        
        # 4. Generate some tooth procedures directly (for reports)
        procedures = frappe.get_all("Dental Procedure Master", 
                                  filters=[["procedure_code", "like", "TEST-%"]], 
                                  pluck="name")
        teeth = frappe.get_all("Tooth Master", pluck="name")
        practitioners = frappe.get_all("Healthcare Practitioner", pluck="name")
        
        if procedures and teeth and practitioners:
            procedure_count = 0
            for i in range(50):  # Generate 50 procedures
                procedure_master = frappe.get_doc("Dental Procedure Master", random.choice(procedures))
                
                # Random dates for procedures (last 3 months)
                procedure_date = getdate() - timedelta(days=random.randint(1, 90))
                status = random.choice(["Completed", "Completed", "In Progress", "Planned"])
                
                completed_date = None
                if status == "Completed":
                    completed_date = procedure_date + timedelta(days=random.randint(0, 3))
                
                # Calculate fees
                standard_fee = procedure_master.standard_fee
                actual_fee = standard_fee * random.uniform(0.9, 1.1) if status == "Completed" else None
                
                # Add complications occasionally
                notes = f"Test procedure performed on {procedure_date}"
                if random.random() < 0.1:
                    notes += ". Minor complication noted."
                
                tooth_procedure = frappe.get_doc({
                    "doctype": "Tooth Procedure",
                    "tooth_number": random.choice(teeth),
                    "procedure_code": procedure_master.name,
                    "surface": random.choice(["Whole Tooth", "Occlusal", "Mesial"]),
                    "status": status,
                    "planned_date": procedure_date,
                    "completed_date": completed_date,
                    "planned_by": "Administrator",
                    "performed_by": random.choice(practitioners) if status in ["Completed", "In Progress"] else None,
                    "duration_minutes": procedure_master.duration_minutes,
                    "standard_fee": standard_fee,
                    "actual_fee": actual_fee,
                    "notes": notes
                })
                tooth_procedure.insert()
                procedure_count += 1
            
            print(f"✅ Created {procedure_count} tooth procedures")
        
        # 5. Generate some invoices
        invoice_count = 0
        for i in range(20):  # Generate 20 invoices
            invoice_date = getdate() - timedelta(days=random.randint(1, 90))
            
            invoice = frappe.get_doc({
                "doctype": "Invoice",
                "patient": f"TEST-Patient-{i+1}",  # Simple patient reference
                "practitioner": practitioners[0] if practitioners else "Dr. Test Dentist",
                "invoice_date": invoice_date,
                "due_date": add_days(invoice_date, 30),
                "invoice_status": random.choice(["Sent", "Paid", "Partially Paid"]),
                "priority": "Normal"
            })
            
            # Add simple invoice items
            procedure = random.choice(procedures) if procedures else None
            if procedure:
                procedure_master = frappe.get_doc("Dental Procedure Master", procedure)
                
                invoice.append("invoice_items", {
                    "item_description": procedure_master.procedure_name,
                    "procedure_code": procedure_master.procedure_code,
                    "quantity": 1,
                    "unit_price": procedure_master.standard_fee,
                    "total_price": procedure_master.standard_fee
                })
                
                # Calculate totals
                subtotal = procedure_master.standard_fee
                tax_amount = subtotal * 0.08
                invoice.subtotal = subtotal
                invoice.tax_amount = tax_amount
                invoice.total_amount = subtotal + tax_amount
                invoice.outstanding_amount = subtotal + tax_amount
                
                invoice.insert()
                invoice_count += 1
        
        print(f"✅ Created {invoice_count} invoices")
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Simple test data generated successfully",
            "data": get_test_data_summary()
        }
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Simple Test Data Generation Error: {str(e)}")
        
        return {
            "success": False,
            "error": str(e)
        } 