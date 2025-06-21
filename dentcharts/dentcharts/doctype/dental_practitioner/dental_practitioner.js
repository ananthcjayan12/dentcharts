// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Practitioner', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			frm.add_custom_button(__('View Healthcare Practitioner'), function() {
				frappe.set_route('Form', 'Healthcare Practitioner', frm.doc.healthcare_practitioner);
			});
			
			frm.add_custom_button(__('View Schedule'), function() {
				frappe.set_route('List', 'Practitioner Schedule', {
					practitioner: frm.doc.healthcare_practitioner
				});
			});
			
			// Add appointments button
			frm.add_custom_button(__('Appointments'), function() {
				frappe.set_route('List', 'Patient Appointment', {
					practitioner: frm.doc.healthcare_practitioner
				});
			});
		}
	},
	
	healthcare_practitioner: function(frm) {
		// Fetch practitioner name when healthcare practitioner is selected
		if (frm.doc.healthcare_practitioner) {
			frappe.db.get_value('Healthcare Practitioner', frm.doc.healthcare_practitioner, 'practitioner_name')
				.then(r => {
					if (r.message) {
						frm.set_value('practitioner_name', r.message.practitioner_name);
					}
				});
		}
	},
	
	specialization: function(frm) {
		// Set default consultation fee based on specialization
		if (frm.doc.specialization && !frm.doc.consultation_fee) {
			const default_fees = {
				"General Dentistry": 100,
				"Orthodontics": 150,
				"Endodontics": 200,
				"Periodontics": 175,
				"Oral Surgery": 250,
				"Prosthodontics": 200,
				"Pediatric Dentistry": 120
			};
			
			const fee = default_fees[frm.doc.specialization] || 100;
			frm.set_value('consultation_fee', fee);
		}
	},
	
	dental_license_number: function(frm) {
		// Validate license number format (basic validation)
		if (frm.doc.dental_license_number && frm.doc.dental_license_number.length < 5) {
			frappe.msgprint(__('Dental License Number should be at least 5 characters long'));
		}
	}
}); 