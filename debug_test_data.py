#!/usr/bin/env python3
"""
Debug script for test data generation issues
Run with: python debug_test_data.py
"""

import sys
import subprocess

def run_bench_command(site_name, command, description):
    """Run a bench command and return the result"""
    full_command = f"bench --site {site_name} execute {command}"
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"Command: {full_command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
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

def main():
    """Debug test data generation"""
    print("🐛 DEBUG: Test Data Generation")
    print("=" * 60)
    
    # Get site name
    site_name = input("Enter your site name (e.g., dev.localhost): ").strip()
    if not site_name:
        print("❌ Site name is required!")
        sys.exit(1)
    
    print(f"🎯 Debugging site: {site_name}")
    
    # Test individual components
    tests = [
        ("frappe.db.get_all('DocType', filters={'name': ['like', 'Dental%']}, pluck='name')", 
         "Check Available Dental DocTypes"),
        
        ("frappe.db.exists('DocType', 'Tooth Master')", 
         "Check Tooth Master DocType Exists"),
        
        ("frappe.db.exists('DocType', 'Dental Condition Master')", 
         "Check Dental Condition Master DocType Exists"),
        
        ("frappe.db.exists('DocType', 'Dental Procedure Master')", 
         "Check Dental Procedure Master DocType Exists"),
        
        ("dentcharts.dentcharts.test_data_generator.generate_master_data", 
         "Test Master Data Generation"),
        
        ("dentcharts.dentcharts.test_data_generator.generate_sample_data_for_testing", 
         "Test Sample Data Generation"),
    ]
    
    for command, description in tests:
        if input(f"\nRun: {description}? (y/n): ").lower() == 'y':
            run_bench_command(site_name, command, description)
    
    print("\n🎉 Debug session completed!")

if __name__ == "__main__":
    main() 