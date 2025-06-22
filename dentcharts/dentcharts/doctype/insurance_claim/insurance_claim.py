import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

class InsuranceClaim(Document):
    def validate(self):
        """Validate insurance claim data"""
        self.validate_claim_details()
        self.calculate_patient_responsibility()
        self.set_default_values()
    
    def validate_claim_details(self):
        """Validate claim details"""
        if not self.claim_amount or self.claim_amount <= 0:
            frappe.throw("Claim amount must be greater than 0")
        
        if self.approved_amount and self.approved_amount > self.claim_amount:
            frappe.throw("Approved amount cannot exceed claim amount")
        
        if self.paid_amount and self.approved_amount and self.paid_amount > self.approved_amount:
            frappe.throw("Paid amount cannot exceed approved amount")
    
    def calculate_patient_responsibility(self):
        """Calculate patient responsibility amount"""
        approved_amount = self.approved_amount or 0
        deductible = self.deductible_amount or 0
        copay = self.copay_amount or 0
        
        if approved_amount > 0:
            unapproved_amount = max(0, self.claim_amount - approved_amount)
            self.patient_responsibility = flt(unapproved_amount + deductible + copay)
        else:
            self.patient_responsibility = flt(self.claim_amount)
    
    def set_default_values(self):
        """Set default values for new claims"""
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.claim_date:
            self.claim_date = today()
    
    def approve_claim(self, approved_amount, approval_notes=None):
        """Approve the insurance claim"""
        if self.claim_status not in ["Submitted", "Under Review"]:
            frappe.throw("Can only approve submitted or under review claims")
        
        if approved_amount > self.claim_amount:
            frappe.throw("Approved amount cannot exceed claim amount")
        
        self.approved_amount = approved_amount
        self.claim_status = "Approved" if approved_amount == self.claim_amount else "Partially Approved"
        self.response_date = today()
        
        if approval_notes:
            self.add_comment("Comment", f"Claim approved for ${approved_amount}. Notes: {approval_notes}")
        
        self.calculate_patient_responsibility()
        self.save()
    
    def deny_claim(self, denial_reason):
        """Deny the insurance claim"""
        if self.claim_status not in ["Submitted", "Under Review"]:
            frappe.throw("Can only deny submitted or under review claims")
        
        self.claim_status = "Denied"
        self.denial_reason = denial_reason
        self.response_date = today()
        self.approved_amount = 0
        self.patient_responsibility = self.claim_amount
        
        self.add_comment("Comment", f"Claim denied. Reason: {denial_reason}")
        self.save()
    
    def record_payment(self, payment_amount, payment_date=None):
        """Record insurance payment for this claim"""
        if not payment_date:
            payment_date = today()
        
        if payment_amount > (self.approved_amount or 0):
            frappe.throw("Payment amount cannot exceed approved amount")
        
        self.paid_amount = flt(self.paid_amount or 0) + flt(payment_amount)
        self.payment_date = payment_date
        
        if self.paid_amount >= (self.approved_amount or 0):
            self.claim_status = "Paid"
        
        self.save() 