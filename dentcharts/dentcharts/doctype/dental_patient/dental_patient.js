// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Patient', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			frm.add_custom_button(__('View Healthcare Patient'), function() {
				frappe.set_route('Form', 'Patient', frm.doc.healthcare_patient);
			});
			
			frm.add_custom_button(__('Create Appointment'), function() {
				frappe.new_doc('Patient Appointment', {
					patient: frm.doc.healthcare_patient,
					patient_name: frm.doc.patient_name
				});
			});
			
			// Add dental chart button (will be implemented in Phase 3)
			frm.add_custom_button(__('Dental Chart'), function() {
				frappe.msgprint(__('Dental Chart functionality will be available in Phase 3'));
			});
		}
	},
	
	healthcare_patient: function(frm) {
		// Fetch patient name when healthcare patient is selected
		if (frm.doc.healthcare_patient) {
			frappe.db.get_value('Patient', frm.doc.healthcare_patient, 'patient_name')
				.then(r => {
					if (r.message) {
						frm.set_value('patient_name', r.message.patient_name);
					}
				});
		}
	},
	
	emergency_phone: function(frm) {
		// Validate emergency phone number
		if (frm.doc.emergency_phone && frm.doc.emergency_phone.length < 10) {
			frappe.msgprint(__('Please enter a valid emergency phone number'));
		}
	}
}); 