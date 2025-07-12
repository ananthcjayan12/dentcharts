// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Patient', {
	refresh: function(frm) {
		// Add custom buttons or actions here if needed
	},
	
	validate: function(frm) {
		// Additional client-side validation
		if (frm.doc.date_of_registration) {
			let today = new Date();
			let registration_date = new Date(frm.doc.date_of_registration);
			if (registration_date > today) {
				frappe.msgprint(__('Date of Registration cannot be in the future'));
				return false;
			}
		}
		
		if (frm.doc.source && frm.doc.source.trim() === '') {
			frappe.msgprint(__('Source cannot be empty if provided'));
			return false;
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
	},
	
	date_of_registration: function(frm) {
		// Validate date of registration
		if (frm.doc.date_of_registration) {
			let today = new Date();
			let registration_date = new Date(frm.doc.date_of_registration);
			if (registration_date > today) {
				frappe.msgprint(__('Date of Registration cannot be in the future'));
				frm.set_value('date_of_registration', '');
			}
		}
	},
	
	source: function(frm) {
		// Validate source field is not empty
		if (frm.doc.source && frm.doc.source.trim() === '') {
			frappe.msgprint(__('Source cannot be empty if provided'));
			frm.set_value('source', '');
		}
	},
	
	chief_complaint: function(frm) {
		// Auto-save chief complaint to linked dental chart if available
		if (frm.doc.chief_complaint && frm.doc.healthcare_patient) {
			// This will be handled server-side when the chart is created
		}
	}
}); 