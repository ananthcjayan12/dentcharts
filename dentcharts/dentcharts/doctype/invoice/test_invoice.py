import unittest
import frappe
from frappe.utils import today, add_days, flt
from dentcharts.dentcharts.doctype.invoice.invoice import Invoice

class TestInvoice(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		# Create test patient if not exists
		if not frappe.db.exists("Patient", "TEST-PATIENT-001"):
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": "Test Patient",
				"name": "TEST-PATIENT-001",
				"sex": "Male",
				"blood_group": "O+"
			})
			patient.insert()
		
		# Create test practitioner if not exists
		if not frappe.db.exists("Healthcare Practitioner", "TEST-PRACTITIONER-001"):
			practitioner = frappe.get_doc({
				"doctype": "Healthcare Practitioner",
				"practitioner_name": "Dr. Test Dentist",
				"name": "TEST-PRACTITIONER-001",
				"department": "Dentistry"
			})
			practitioner.insert()
		
		# Create test procedure if not exists
		if not frappe.db.exists("Dental Procedure Master", "TEST-PROC-001"):
			procedure = frappe.get_doc({
				"doctype": "Dental Procedure Master",
				"procedure_code": "TEST-PROC-001",
				"procedure_name": "Test Cleaning",
				"category": "Preventive",
				"standard_fee": 100.00
			})
			procedure.insert()
	
	def test_invoice_creation(self):
		"""Test basic invoice creation"""
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": today(),
			"invoice_items": [{
				"procedure_code": "TEST-PROC-001",
				"quantity": 1,
				"amount": 100.00
			}]
		})
		
		invoice.insert()
		
		# Test calculations
		self.assertEqual(invoice.subtotal, 100.00)
		self.assertEqual(invoice.total_amount, 100.00)
		self.assertEqual(invoice.outstanding_amount, 100.00)
		self.assertEqual(invoice.payment_status, "Unpaid")
	
	def test_due_date_calculation(self):
		"""Test automatic due date calculation"""
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": today(),
			"payment_terms": "Net 30",
			"invoice_items": [{
				"procedure_code": "TEST-PROC-001",
				"quantity": 1,
				"amount": 100.00
			}]
		})
		
		invoice.insert()
		
		expected_due_date = add_days(today(), 30)
		self.assertEqual(str(invoice.due_date), str(expected_due_date))
	
	def test_insurance_calculation(self):
		"""Test insurance amount calculation"""
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": today(),
			"insurance_coverage_percentage": 80,
			"invoice_items": [{
				"procedure_code": "TEST-PROC-001",
				"quantity": 1,
				"amount": 100.00
			}]
		})
		
		invoice.insert()
		
		self.assertEqual(invoice.insurance_amount, 80.00)
		self.assertEqual(invoice.patient_portion, 20.00)
	
	def test_payment_recording(self):
		"""Test payment recording functionality"""
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": today(),
			"invoice_items": [{
				"procedure_code": "TEST-PROC-001",
				"quantity": 1,
				"amount": 100.00
			}]
		})
		
		invoice.insert()
		invoice.submit()
		
		# Record partial payment
		payment_entry_name = invoice.record_payment(50.00, "Cash")
		invoice.reload()
		
		self.assertEqual(invoice.paid_amount, 50.00)
		self.assertEqual(invoice.outstanding_amount, 50.00)
		self.assertEqual(invoice.payment_status, "Partially Paid")
		
		# Record remaining payment
		invoice.record_payment(50.00, "Cash")
		invoice.reload()
		
		self.assertEqual(invoice.paid_amount, 100.00)
		self.assertEqual(invoice.outstanding_amount, 0.00)
		self.assertEqual(invoice.payment_status, "Paid")
	
	def test_multiple_items_calculation(self):
		"""Test calculation with multiple invoice items"""
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": today(),
			"invoice_items": [
				{
					"procedure_code": "TEST-PROC-001",
					"quantity": 2,
					"amount": 100.00
				},
				{
					"procedure_code": "TEST-PROC-001",
					"quantity": 1,
					"amount": 150.00
				}
			]
		})
		
		invoice.insert()
		
		# 2 * 100 + 1 * 150 = 350
		self.assertEqual(invoice.subtotal, 350.00)
		self.assertEqual(invoice.total_amount, 350.00)
	
	def test_validation_errors(self):
		"""Test validation errors"""
		# Test empty invoice items
		with self.assertRaises(frappe.ValidationError):
			invoice = frappe.get_doc({
				"doctype": "Invoice",
				"patient": "TEST-PATIENT-001",
				"practitioner": "TEST-PRACTITIONER-001",
				"invoice_date": today(),
				"invoice_items": []
			})
			invoice.insert()
		
		# Test invalid due date
		with self.assertRaises(frappe.ValidationError):
			invoice = frappe.get_doc({
				"doctype": "Invoice",
				"patient": "TEST-PATIENT-001",
				"practitioner": "TEST-PRACTITIONER-001",
				"invoice_date": today(),
				"due_date": add_days(today(), -1),  # Due date before invoice date
				"invoice_items": [{
					"procedure_code": "TEST-PROC-001",
					"quantity": 1,
					"amount": 100.00
				}]
			})
			invoice.insert()
	
	def test_late_fee_calculation(self):
		"""Test late fee calculation for overdue invoices"""
		# Create overdue invoice
		past_date = add_days(today(), -45)
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": past_date,
			"due_date": add_days(past_date, 30),
			"late_fee_applicable": 1,
			"invoice_items": [{
				"procedure_code": "TEST-PROC-001",
				"quantity": 1,
				"amount": 100.00
			}]
		})
		
		invoice.insert()
		
		# Should calculate late fee for overdue invoice
		self.assertEqual(invoice.invoice_status, "Overdue")
		self.assertGreater(invoice.late_fee_amount, 0)
	
	def test_static_methods(self):
		"""Test static utility methods"""
		# Create test invoice
		invoice = frappe.get_doc({
			"doctype": "Invoice",
			"patient": "TEST-PATIENT-001",
			"practitioner": "TEST-PRACTITIONER-001",
			"invoice_date": today(),
			"invoice_items": [{
				"procedure_code": "TEST-PROC-001",
				"quantity": 1,
				"amount": 100.00
			}]
		})
		invoice.insert()
		
		# Test get_outstanding_invoices_for_patient
		outstanding_invoices = Invoice.get_outstanding_invoices_for_patient("TEST-PATIENT-001")
		self.assertGreater(len(outstanding_invoices), 0)
		
		# Test get_overdue_invoices (should be empty for new invoice)
		overdue_invoices = Invoice.get_overdue_invoices()
		# This might be empty or contain other test data
		self.assertIsInstance(overdue_invoices, list)
	
	def tearDown(self):
		"""Clean up test data"""
		# Delete test invoices
		frappe.db.sql("DELETE FROM `tabInvoice` WHERE patient = 'TEST-PATIENT-001'")
		frappe.db.sql("DELETE FROM `tabPayment Entry` WHERE patient = 'TEST-PATIENT-001'")
		frappe.db.commit()

if __name__ == '__main__':
	unittest.main() 