# Test Data Cleanup Utility for Dental ERP System
import frappe
from frappe.utils import getdate, add_days
from datetime import datetime, timedelta
import json

@frappe.whitelist()
def cleanup_all_test_data():
    """Complete cleanup of all test data"""
    try:
        frappe.db.begin()
        
        # Get cleanup summary before deletion
        summary = get_test_data_summary()
        
        # Clean up test data
        clear_test_records()
        clear_test_files()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "All test data cleaned up successfully",
            "deleted_summary": summary
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Test Data Cleanup Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def cleanup_test_data_by_date(days_old=7):
    """Clean up test data older than specified days"""
    try:
        frappe.db.begin()
        
        cutoff_date = add_days(getdate(), -int(days_old))
        
        # Get records to be deleted
        summary = get_test_data_summary_by_date(cutoff_date)
        
        # Delete old test records
        clear_test_records_by_date(cutoff_date)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Test data older than {days_old} days cleaned up",
            "cutoff_date": str(cutoff_date),
            "deleted_summary": summary
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Date-based Test Data Cleanup Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def cleanup_test_data_selective(doctypes_to_clean=None):
    """Clean up test data for specific DocTypes only"""
    try:
        frappe.db.begin()
        
        if not doctypes_to_clean:
            doctypes_to_clean = [
                "Payment Entry", "Invoice", "Invoice Item",
                "Treatment Plan Item", "Treatment Plan",
                "Appointment Procedure", "Dental Appointment"
            ]
        
        # Get summary before deletion
        summary = {}
        for doctype in doctypes_to_clean:
            if frappe.db.exists("DocType", doctype):
                count = frappe.db.count(doctype, {"name": ["like", "TEST-%"]})
                if count > 0:
                    summary[doctype] = count
        
        # Clean up selected DocTypes
        for doctype in doctypes_to_clean:
            clear_test_records_for_doctype(doctype)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Selective test data cleanup completed",
            "doctypes_cleaned": doctypes_to_clean,
            "deleted_summary": summary
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Selective Test Data Cleanup Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def clear_test_records():
    """Clear all test records with TEST- prefix"""
    test_doctypes = [
        # Transaction documents (delete first due to dependencies)
        "Payment Entry",
        "Invoice Item", 
        "Invoice",
        "Appointment Procedure",
        "Treatment Plan Item",
        "Treatment Plan",
        "Dental Appointment",
        "Tooth Procedure",
        "Tooth Condition",
        "Dental Chart",
        
        # Master documents (delete after transactions)
        "Dental Patient",
        "Dental Practitioner", 
        "Dental Clinic",
        
        # Healthcare module cleanup (if needed)
        "Patient Appointment",
        "Healthcare Practitioner"
    ]
    
    deleted_count = {}
    
    for doctype in test_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                # Count before deletion
                count = frappe.db.count(doctype, {"name": ["like", "TEST-%"]})
                
                if count > 0:
                    # Delete records
                    frappe.db.delete(doctype, {"name": ["like", "TEST-%"]})
                    deleted_count[doctype] = count
                    print(f"✅ Deleted {count} test records from {doctype}")
                    
        except Exception as e:
            print(f"⚠️  Error deleting from {doctype}: {str(e)}")
            continue
    
    return deleted_count

def clear_test_records_by_date(cutoff_date):
    """Clear test records older than cutoff date"""
    test_doctypes = [
        "Payment Entry", "Invoice", "Invoice Item",
        "Treatment Plan Item", "Treatment Plan",
        "Appointment Procedure", "Dental Appointment",
        "Tooth Procedure", "Tooth Condition", "Dental Chart",
        "Dental Patient", "Dental Practitioner", "Dental Clinic"
    ]
    
    deleted_count = {}
    
    for doctype in test_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                # Get records matching criteria
                records = frappe.db.get_all(
                    doctype,
                    filters={
                        "name": ["like", "TEST-%"],
                        "creation": ["<", cutoff_date]
                    },
                    pluck="name"
                )
                
                if records:
                    for record in records:
                        frappe.delete_doc(doctype, record, ignore_permissions=True)
                    
                    deleted_count[doctype] = len(records)
                    print(f"✅ Deleted {len(records)} old test records from {doctype}")
                    
        except Exception as e:
            print(f"⚠️  Error deleting old records from {doctype}: {str(e)}")
            continue
    
    return deleted_count

def clear_test_records_for_doctype(doctype):
    """Clear test records for a specific DocType"""
    try:
        if frappe.db.exists("DocType", doctype):
            count = frappe.db.count(doctype, {"name": ["like", "TEST-%"]})
            
            if count > 0:
                frappe.db.delete(doctype, {"name": ["like", "TEST-%"]})
                print(f"✅ Deleted {count} test records from {doctype}")
                return count
                
    except Exception as e:
        print(f"⚠️  Error deleting from {doctype}: {str(e)}")
        
    return 0

def clear_test_files():
    """Clear test files and attachments"""
    try:
        # Clear test file attachments
        test_files = frappe.db.get_all(
            "File",
            filters={"file_name": ["like", "TEST-%"]},
            pluck="name"
        )
        
        for file_name in test_files:
            frappe.delete_doc("File", file_name, ignore_permissions=True)
        
        print(f"✅ Deleted {len(test_files)} test files")
        return len(test_files)
        
    except Exception as e:
        print(f"⚠️  Error deleting test files: {str(e)}")
        return 0

def get_test_data_summary():
    """Get summary of all test data before cleanup"""
    test_doctypes = [
        "Dental Clinic", "Dental Practitioner", "Dental Patient",
        "Dental Chart", "Tooth Condition", "Tooth Procedure",
        "Dental Appointment", "Appointment Procedure",
        "Treatment Plan", "Treatment Plan Item",
        "Invoice", "Invoice Item", "Payment Entry"
    ]
    
    summary = {}
    total_records = 0
    
    for doctype in test_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                count = frappe.db.count(doctype, {"name": ["like", "TEST-%"]})
                if count > 0:
                    summary[doctype] = count
                    total_records += count
        except:
            continue
    
    # Add file count
    try:
        file_count = frappe.db.count("File", {"file_name": ["like", "TEST-%"]})
        if file_count > 0:
            summary["Files"] = file_count
            total_records += file_count
    except:
        pass
    
    summary["Total Records"] = total_records
    return summary

def get_test_data_summary_by_date(cutoff_date):
    """Get summary of test data older than cutoff date"""
    test_doctypes = [
        "Dental Clinic", "Dental Practitioner", "Dental Patient",
        "Dental Chart", "Dental Appointment", "Treatment Plan", "Invoice"
    ]
    
    summary = {}
    total_records = 0
    
    for doctype in test_doctypes:
        try:
            if frappe.db.exists("DocType", doctype):
                count = frappe.db.count(doctype, {
                    "name": ["like", "TEST-%"],
                    "creation": ["<", cutoff_date]
                })
                if count > 0:
                    summary[doctype] = count
                    total_records += count
        except:
            continue
    
    summary["Total Records"] = total_records
    summary["Cutoff Date"] = str(cutoff_date)
    return summary

@frappe.whitelist()
def get_current_test_data_status():
    """Get current status of test data without cleanup"""
    return {
        "success": True,
        "summary": get_test_data_summary(),
        "timestamp": str(datetime.now())
    }

@frappe.whitelist()
def validate_cleanup_safety():
    """Validate if cleanup is safe to perform"""
    try:
        # Check if we're in production
        if frappe.conf.get("developer_mode") != 1:
            return {
                "safe": False,
                "message": "Cleanup should only be run in development mode",
                "developer_mode": False
            }
        
        # Check if there are any non-test important records
        important_checks = {
            "Dental Patient": frappe.db.count("Dental Patient", {"name": ["not like", "TEST-%"]}),
            "Dental Appointment": frappe.db.count("Dental Appointment", {"name": ["not like", "TEST-%"]}),
            "Invoice": frappe.db.count("Invoice", {"name": ["not like", "TEST-%"]})
        }
        
        has_production_data = any(count > 0 for count in important_checks.values())
        
        return {
            "safe": True,
            "message": "Cleanup validation passed",
            "developer_mode": True,
            "has_production_data": has_production_data,
            "production_data_counts": important_checks,
            "test_data_summary": get_test_data_summary()
        }
        
    except Exception as e:
        return {
            "safe": False,
            "message": f"Validation error: {str(e)}",
            "error": str(e)
        }

# Console commands for manual cleanup
def cleanup_console_commands():
    """Print console commands for manual cleanup"""
    commands = [
        "# Manual cleanup commands (run from bench console):",
        "",
        "# 1. Complete cleanup",
        "frappe.get_doc('dentcharts.dentcharts.test_data_cleanup').cleanup_all_test_data()",
        "",
        "# 2. Cleanup by date (older than 7 days)",
        "frappe.get_doc('dentcharts.dentcharts.test_data_cleanup').cleanup_test_data_by_date(7)",
        "",
        "# 3. Selective cleanup (transactions only)",
        "frappe.get_doc('dentcharts.dentcharts.test_data_cleanup').cleanup_test_data_selective(['Invoice', 'Payment Entry'])",
        "",
        "# 4. Check current test data status",
        "frappe.get_doc('dentcharts.dentcharts.test_data_cleanup').get_current_test_data_status()",
        "",
        "# 5. Validate cleanup safety",
        "frappe.get_doc('dentcharts.dentcharts.test_data_cleanup').validate_cleanup_safety()"
    ]
    
    return "\n".join(commands) 