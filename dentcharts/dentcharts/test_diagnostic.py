# Diagnostic script for test data generation
import frappe

@frappe.whitelist()
def diagnose_import_issue():
    """Diagnose the import issue with create_standard_teeth"""
    try:
        print("🔍 Starting diagnostic...")
        
        # Check if DocType exists
        tooth_master_exists = frappe.db.exists("DocType", "Tooth Master")
        print(f"✅ Tooth Master DocType exists: {tooth_master_exists}")
        
        if not tooth_master_exists:
            return {"error": "Tooth Master DocType does not exist"}
        
        # Try to import the module
        print("🔍 Attempting to import ToothMaster class...")
        from dentcharts.dentcharts.doctype.tooth_master.tooth_master import ToothMaster
        print("✅ Import successful")
        
        # Check if the method exists
        has_method = hasattr(ToothMaster, 'create_standard_teeth')
        print(f"✅ create_standard_teeth method exists: {has_method}")
        
        if not has_method:
            return {"error": "create_standard_teeth method not found"}
        
        # Check if teeth already exist
        existing_teeth = frappe.db.count("Tooth Master", {"universal_number": 11})
        print(f"✅ Existing teeth with universal_number 11: {existing_teeth}")
        
        if existing_teeth > 0:
            return {"message": "Teeth already exist, skipping creation"}
        
        # Try to call the method
        print("🔍 Attempting to call create_standard_teeth...")
        result = ToothMaster.create_standard_teeth()
        print(f"✅ Method call successful: {result}")
        
        return {
            "success": True,
            "message": "Diagnostic completed successfully",
            "result": result
        }
        
    except ImportError as e:
        error_msg = f"Import Error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"General Error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

@frappe.whitelist()
def test_simple_master_data():
    """Test creating simple master data without complex imports"""
    try:
        frappe.db.begin()
        
        print("🧪 Testing simple master data creation...")
        
        # Test creating a simple dental condition
        if frappe.db.exists("DocType", "Dental Condition Master"):
            if not frappe.db.exists("Dental Condition Master", "Test Caries"):
                condition = frappe.get_doc({
                    "doctype": "Dental Condition Master",
                    "condition_name": "Test Caries",
                    "category": "Caries",
                    "severity": "Medium",
                    "color": "#FF6B6B",
                    "is_emergency": 0,
                    "description": "Test dental condition"
                })
                condition.insert()
                print("✅ Created test dental condition")
        
        # Test creating a simple dental procedure
        if frappe.db.exists("DocType", "Dental Procedure Master"):
            if not frappe.db.exists("Dental Procedure Master", "Test Cleaning"):
                procedure = frappe.get_doc({
                    "doctype": "Dental Procedure Master",
                    "procedure_name": "Test Cleaning",
                    "procedure_category": "Preventive",
                    "estimated_cost": 100,
                    "estimated_duration": 30,
                    "description": "Test dental procedure"
                })
                procedure.insert()
                print("✅ Created test dental procedure")
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Simple master data created successfully"
        }
        
    except Exception as e:
        frappe.db.rollback()
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

@frappe.whitelist()
def check_doctype_status():
    """Check the status of all dental DocTypes"""
    try:
        dental_doctypes = [
            "Dental Clinic", "Dental Practitioner", "Dental Patient",
            "Dental Chart", "Dental Appointment", "Treatment Plan",
            "Invoice", "Tooth Master", "Dental Condition Master", 
            "Dental Procedure Master", "Healthcare Practitioner", "Patient"
        ]
        
        status = {}
        for doctype in dental_doctypes:
            exists = frappe.db.exists("DocType", doctype)
            if exists:
                count = frappe.db.count(doctype)
                status[doctype] = {"exists": True, "count": count}
            else:
                status[doctype] = {"exists": False, "count": 0}
        
        return {
            "success": True,
            "doctype_status": status
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        } 