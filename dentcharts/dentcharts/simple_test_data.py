# Simplified Test Data Generator
import frappe
from frappe.utils import getdate, add_days, nowtime
import random

@frappe.whitelist()
def generate_basic_test_data():
    """Generate basic test data without complex dependencies"""
    try:
        frappe.db.begin()
        
        print("🧪 Starting basic test data generation...")
        
        # Clear existing test data first
        clear_basic_test_data()
        
        # Generate basic master data
        generate_basic_masters()
        
        # Generate one test clinic
        generate_test_clinic()
        
        # Generate one test practitioner
        generate_test_practitioner()
        
        # Generate a few test patients
        generate_test_patients()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Basic test data generated successfully",
            "summary": get_basic_summary()
        }
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def clear_basic_test_data():
    """Clear basic test data"""
    print("🧹 Clearing existing test data...")
    
    test_doctypes = [
        "Dental Patient", "Dental Practitioner", "Dental Clinic"
    ]
    
    for doctype in test_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                test_records = frappe.db.get_all(doctype, filters={"name": ["like", "TEST-%"]}, pluck="name")
                for record in test_records:
                    frappe.delete_doc(doctype, record, ignore_permissions=True)
                print(f"✅ Cleared {len(test_records)} records from {doctype}")
        except Exception as e:
            print(f"⚠️  Could not clear {doctype}: {str(e)}")

def generate_basic_masters():
    """Generate basic master data"""
    print("📋 Generating basic master data...")
    
    # Create some basic dental conditions if DocType exists
    try:
        if frappe.db.exists("DocType", "Dental Condition Master"):
            basic_conditions = [
                {"condition_name": "Caries", "category": "Caries", "severity": "Medium", "color": "#FF6B6B"},
                {"condition_name": "Gingivitis", "category": "Periodontal", "severity": "Low", "color": "#FFA726"},
                {"condition_name": "Abscess", "category": "Endodontic", "severity": "Critical", "color": "#D32F2F"}
            ]
            
            for condition in basic_conditions:
                if not frappe.db.exists("Dental Condition Master", condition["condition_name"]):
                    doc = frappe.get_doc({
                        "doctype": "Dental Condition Master",
                        **condition,
                        "description": f"Basic test condition: {condition['condition_name']}"
                    })
                    doc.insert()
            print("✅ Created basic dental conditions")
    except Exception as e:
        print(f"⚠️  Could not create dental conditions: {str(e)}")
    
    # Create some basic dental procedures if DocType exists
    try:
        if frappe.db.exists("DocType", "Dental Procedure Master"):
            basic_procedures = [
                {"procedure_name": "Cleaning", "procedure_category": "Preventive", "estimated_cost": 120},
                {"procedure_name": "Filling", "procedure_category": "Restorative", "estimated_cost": 180},
                {"procedure_name": "Extraction", "procedure_category": "Surgical", "estimated_cost": 200}
            ]
            
            for procedure in basic_procedures:
                if not frappe.db.exists("Dental Procedure Master", procedure["procedure_name"]):
                    doc = frappe.get_doc({
                        "doctype": "Dental Procedure Master",
                        **procedure,
                        "estimated_duration": 30,
                        "description": f"Basic {procedure['procedure_name'].lower()} procedure"
                    })
                    doc.insert()
            print("✅ Created basic dental procedures")
    except Exception as e:
        print(f"⚠️  Could not create dental procedures: {str(e)}")

def generate_test_clinic():
    """Generate one test clinic"""
    print("🏥 Generating test clinic...")
    
    try:
        if not frappe.db.exists("Dental Clinic", {"clinic_code": "TEST-MAIN"}):
            clinic = frappe.get_doc({
                "doctype": "Dental Clinic",
                "clinic_name": "TEST-Main Dental Clinic",
                "clinic_code": "TEST-MAIN",
                "address": "123 Test Street, Test City",
                "phone": "+1-555-0100",
                "email": "test@maindental.com",
                "license_number": "TEST-LIC-MAIN",
                "established_date": getdate(),
                "status": "Active",
                "default_currency": "USD"
            })
            clinic.insert()
            print(f"✅ Created clinic: {clinic.name}")
    except Exception as e:
        print(f"⚠️  Could not create clinic: {str(e)}")

def generate_test_practitioner():
    """Generate one test practitioner"""
    print("👨‍⚕️ Generating test practitioner...")
    
    try:
        # First create Healthcare Practitioner if it doesn't exist
        healthcare_prac_name = "Dr. Test Dentist"
        if not frappe.db.exists("Healthcare Practitioner", {"practitioner_name": healthcare_prac_name}):
            healthcare_prac = frappe.get_doc({
                "doctype": "Healthcare Practitioner",
                "first_name": "Test",
                "last_name": "Dentist",
                "practitioner_name": healthcare_prac_name,
                "mobile": "+1-555-0001",
                "email": "test.dentist@test.com"
            })
            healthcare_prac.insert()
            print(f"✅ Created healthcare practitioner: {healthcare_prac.name}")
        
        # Then create Dental Practitioner
        if not frappe.db.exists("Dental Practitioner", {"practitioner_name": healthcare_prac_name}):
            dental_prac = frappe.get_doc({
                "doctype": "Dental Practitioner",
                "practitioner_name": healthcare_prac_name,
                "healthcare_practitioner": healthcare_prac_name,
                "dental_license_number": "TEST-DDS-MAIN",
                "specialization": "General Dentistry",
                "years_of_experience": 10,
                "consultation_fee": 200
            })
            dental_prac.insert()
            print(f"✅ Created dental practitioner: {dental_prac.name}")
            
    except Exception as e:
        print(f"⚠️  Could not create practitioner: {str(e)}")

def generate_test_patients():
    """Generate a few test patients"""
    print("👥 Generating test patients...")
    
    patient_data = [
        {"first": "John", "last": "Doe", "gender": "Male", "age": 30},
        {"first": "Jane", "last": "Smith", "gender": "Female", "age": 25},
        {"first": "Bob", "last": "Johnson", "gender": "Male", "age": 45}
    ]
    
    for i, data in enumerate(patient_data):
        try:
            patient_name = f"{data['first']} {data['last']}"
            
            # Create Healthcare Patient first
            if not frappe.db.exists("Patient", {"patient_name": patient_name}):
                healthcare_patient = frappe.get_doc({
                    "doctype": "Patient",
                    "first_name": data["first"],
                    "last_name": data["last"],
                    "patient_name": patient_name,
                    "gender": data["gender"],
                    "dob": add_days(getdate(), -data["age"]*365),
                    "mobile": f"+1-555-000{i+2}",
                    "email": f"{data['first'].lower()}.{data['last'].lower()}@test.com"
                })
                healthcare_patient.insert()
                print(f"✅ Created healthcare patient: {healthcare_patient.name}")
            
            # Create Dental Patient
            if not frappe.db.exists("Dental Patient", {"patient_name": patient_name}):
                dental_patient = frappe.get_doc({
                    "doctype": "Dental Patient",
                    "patient_name": patient_name,
                    "healthcare_patient": patient_name,
                    "dental_history": f"Test patient {data['first']} - No significant dental history",
                    "emergency_contact": f"Emergency Contact for {data['first']}",
                    "emergency_phone": f"+1-555-900{i+1}"
                })
                dental_patient.insert()
                print(f"✅ Created dental patient: {dental_patient.name}")
                
        except Exception as e:
            print(f"⚠️  Could not create patient {data['first']} {data['last']}: {str(e)}")

def get_basic_summary():
    """Get summary of basic test data"""
    summary = {}
    
    basic_doctypes = ["Dental Clinic", "Dental Practitioner", "Dental Patient", "Patient", "Healthcare Practitioner"]
    
    for doctype in basic_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                count = frappe.db.count(doctype, {"name": ["like", "TEST-%"]})
                if count > 0:
                    summary[doctype] = count
        except:
            continue
    
    return summary

@frappe.whitelist()
def check_doctype_status():
    """Check which DocTypes are available"""
    try:
        dental_doctypes = [
            "Dental Clinic", "Dental Practitioner", "Dental Patient",
            "Dental Chart", "Dental Appointment", "Treatment Plan",
            "Invoice", "Tooth Master", "Dental Condition Master", "Dental Procedure Master"
        ]
        
        status = {}
        for doctype in dental_doctypes:
            status[doctype] = frappe.db.exists("DocType", doctype) or False
        
        return {
            "success": True,
            "doctype_status": status
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def cleanup_basic_test_data():
    """Clean up basic test data"""
    try:
        frappe.db.begin()
        clear_basic_test_data()
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Basic test data cleaned up successfully"
        }
        
    except Exception as e:
        frappe.db.rollback()
        return {
            "success": False,
            "error": str(e)
        } 