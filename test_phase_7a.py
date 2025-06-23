#!/usr/bin/env python3
"""
Phase 7A Testing Helper Script
Automates common testing tasks for the dental ERP system
"""

import subprocess
import sys
import json
import requests
from datetime import datetime

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ FAILED: {description}")
            if result.stderr:
                print(f"Error:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_dashboard_endpoints(site_url):
    """Test dashboard API endpoints"""
    print(f"\n{'='*60}")
    print("🌐 Testing Dashboard Endpoints")
    print(f"{'='*60}")
    
    endpoints = [
        "get_executive_dashboard_data",
        "get_clinical_dashboard_data", 
        "get_financial_dashboard_data",
        "get_operational_dashboard_data"
    ]
    
    for endpoint in endpoints:
        url = f"{site_url}/api/method/dentcharts.dentcharts.dashboard_utils.{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}: SUCCESS")
                data = response.json()
                if 'message' in data:
                    print(f"   Data keys: {list(data['message'].keys())}")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")

def main():
    """Main testing function"""
    print("🧪 PHASE 7A: COMPONENT TESTING HELPER")
    print("=" * 60)
    
    # Get site name from user
    site_name = input("Enter your site name (e.g., dental.localhost): ").strip()
    if not site_name:
        print("❌ Site name is required!")
        sys.exit(1)
    
    # Get site URL for API testing
    site_url = f"http://{site_name}"
    if not site_url.startswith('http'):
        site_url = f"http://{site_url}"
    
    print(f"🎯 Testing site: {site_name}")
    print(f"🌐 API URL: {site_url}")
    
    # Test categories
    tests = {
        "1": "Generate Test Data",
        "2": "Run DocType Tests", 
        "3": "Test Dashboard APIs",
        "4": "Generate Reports",
        "5": "Check System Status",
        "6": "Run All Tests",
        "7": "Cleanup Test Data",
        "0": "Exit"
    }
    
    while True:
        print(f"\n{'='*60}")
        print("📋 SELECT TEST CATEGORY:")
        print(f"{'='*60}")
        for key, value in tests.items():
            print(f"{key}. {value}")
        
        choice = input("\nEnter your choice (0-7): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
            
        elif choice == "1":
            # Generate test data
            commands = [
                (f"bench --site {site_name} execute dentcharts.dentcharts.test_data_generator.generate_sample_data_for_testing", 
                 "Generate Sample Test Data"),
                (f"bench --site {site_name} execute dentcharts.dentcharts.test_data_generator.generate_all_test_data", 
                 "Generate Complete Test Data (Optional - takes longer)")
            ]
            
            for cmd, desc in commands:
                if input(f"\nRun: {desc}? (y/n): ").lower() == 'y':
                    run_command(cmd, desc)
                    
        elif choice == "2":
            # Run DocType tests
            doctypes = [
                "dental_clinic",
                "dental_patient", 
                "dental_practitioner",
                "dental_chart",
                "dental_appointment",
                "treatment_plan",
                "invoice"
            ]
            
            print("\n📋 Available DocType Tests:")
            for i, doctype in enumerate(doctypes, 1):
                print(f"{i}. {doctype.replace('_', ' ').title()}")
            
            selection = input("\nEnter DocType number (or 'all' for all tests): ").strip()
            
            if selection.lower() == 'all':
                for doctype in doctypes:
                    cmd = f"bench --site {site_name} run-tests --app dentcharts --module dentcharts.dentcharts.doctype.{doctype}.test_{doctype}"
                    run_command(cmd, f"Test {doctype.replace('_', ' ').title()}")
            else:
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(doctypes):
                        doctype = doctypes[idx]
                        cmd = f"bench --site {site_name} run-tests --app dentcharts --module dentcharts.dentcharts.doctype.{doctype}.test_{doctype}"
                        run_command(cmd, f"Test {doctype.replace('_', ' ').title()}")
                    else:
                        print("❌ Invalid selection!")
                except ValueError:
                    print("❌ Invalid input!")
                    
        elif choice == "3":
            # Test dashboard APIs
            test_dashboard_endpoints(site_url)
            
        elif choice == "4":
            # Generate reports
            reports = [
                ("dentcharts.dentcharts.report.patient_demographics.patient_demographics.execute", 
                 "Patient Demographics Report"),
                ("dentcharts.dentcharts.report.revenue_analysis.revenue_analysis.execute", 
                 "Revenue Analysis Report"),
                ("dentcharts.dentcharts.report.treatment_success_metrics.treatment_success_metrics.execute", 
                 "Treatment Success Metrics Report")
            ]
            
            for report_path, desc in reports:
                if input(f"\nGenerate: {desc}? (y/n): ").lower() == 'y':
                    cmd = f"bench --site {site_name} execute {report_path}"
                    run_command(cmd, f"Generate {desc}")
                    
        elif choice == "5":
            # Check system status
            commands = [
                (f"bench --site {site_name} migrate", "Run Database Migrations"),
                (f"bench --site {site_name} build", "Build Assets"),
                (f"bench --site {site_name} doctor", "System Health Check"),
                (f"bench --site {site_name} logs", "Check Recent Logs")
            ]
            
            for cmd, desc in commands:
                if input(f"\nRun: {desc}? (y/n): ").lower() == 'y':
                    run_command(cmd, desc)
                    
        elif choice == "6":
            # Run all tests
            print("🚀 Running comprehensive test suite...")
            
            # Generate test data
            run_command(f"bench --site {site_name} execute dentcharts.dentcharts.test_data_generator.generate_sample_data_for_testing", 
                       "Generate Test Data")
            
            # Test key DocTypes
            key_doctypes = ["dental_patient", "dental_appointment", "invoice"]
            for doctype in key_doctypes:
                cmd = f"bench --site {site_name} run-tests --app dentcharts --module dentcharts.dentcharts.doctype.{doctype}.test_{doctype}"
                run_command(cmd, f"Test {doctype.replace('_', ' ').title()}")
            
            # Test dashboards
            test_dashboard_endpoints(site_url)
            
            # System health check
            run_command(f"bench --site {site_name} doctor", "System Health Check")
            
            print("\n🎉 Comprehensive testing completed!")
            
        elif choice == "7":
            # Cleanup test data
            cleanup_options = {
                "1": "Complete Cleanup (All test data)",
                "2": "Cleanup by Date (Older than X days)",
                "3": "Selective Cleanup (Choose DocTypes)",
                "4": "Check Test Data Status",
                "5": "Validate Cleanup Safety",
                "0": "Back to Main Menu"
            }
            
            while True:
                print(f"\n{'='*60}")
                print("🧹 TEST DATA CLEANUP OPTIONS:")
                print(f"{'='*60}")
                for key, value in cleanup_options.items():
                    print(f"{key}. {value}")
                
                cleanup_choice = input("\nEnter cleanup option (0-5): ").strip()
                
                if cleanup_choice == "0":
                    break
                elif cleanup_choice == "1":
                    # Complete cleanup
                    if input("\n⚠️  This will DELETE ALL test data! Continue? (type 'YES' to confirm): ").strip() == "YES":
                        cmd = f"bench --site {site_name} execute dentcharts.dentcharts.test_data_cleanup.cleanup_all_test_data"
                        run_command(cmd, "Complete Test Data Cleanup")
                    else:
                        print("❌ Cleanup cancelled")
                        
                elif cleanup_choice == "2":
                    # Cleanup by date
                    days = input("Enter number of days (delete data older than X days): ").strip()
                    try:
                        days = int(days)
                        cmd = f"bench --site {site_name} execute dentcharts.dentcharts.test_data_cleanup.cleanup_test_data_by_date --args {days}"
                        run_command(cmd, f"Cleanup Test Data Older Than {days} Days")
                    except ValueError:
                        print("❌ Invalid number of days")
                        
                elif cleanup_choice == "3":
                    # Selective cleanup
                    print("\n📋 Available DocTypes for cleanup:")
                    doctypes = [
                        "Invoice", "Payment Entry", "Dental Appointment",
                        "Treatment Plan", "Dental Chart", "Dental Patient"
                    ]
                    for i, dt in enumerate(doctypes, 1):
                        print(f"{i}. {dt}")
                    
                    selection = input("\nEnter DocType numbers (comma-separated) or 'all': ").strip()
                    if selection.lower() == 'all':
                        selected_doctypes = doctypes
                    else:
                        try:
                            indices = [int(x.strip()) - 1 for x in selection.split(',')]
                            selected_doctypes = [doctypes[i] for i in indices if 0 <= i < len(doctypes)]
                        except:
                            print("❌ Invalid selection")
                            continue
                    
                    if selected_doctypes:
                        doctypes_str = "[" + ",".join([f'"{dt}"' for dt in selected_doctypes]) + "]"
                        cmd = f"bench --site {site_name} execute dentcharts.dentcharts.test_data_cleanup.cleanup_test_data_selective --args '{doctypes_str}'"
                        run_command(cmd, f"Selective Cleanup: {', '.join(selected_doctypes)}")
                        
                elif cleanup_choice == "4":
                    # Check status
                    cmd = f"bench --site {site_name} execute dentcharts.dentcharts.test_data_cleanup.get_current_test_data_status"
                    run_command(cmd, "Check Test Data Status")
                    
                elif cleanup_choice == "5":
                    # Validate safety
                    cmd = f"bench --site {site_name} execute dentcharts.dentcharts.test_data_cleanup.validate_cleanup_safety"
                    run_command(cmd, "Validate Cleanup Safety")
                    
                else:
                    print("❌ Invalid choice! Please enter 0-5.")
            
        else:
            print("❌ Invalid choice! Please select 0-7.")

if __name__ == "__main__":
    main() 