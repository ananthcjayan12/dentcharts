// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Clinic', {
	refresh: function(frm) {
		// Add custom buttons or form logic here
		if (frm.doc.website && !frm.doc.website.startsWith('http')) {
			frm.doc.website = 'https://' + frm.doc.website;
		}
	},
	
	email: function(frm) {
		// Email validation on change
		if (frm.doc.email && !frm.doc.email.includes('@')) {
			frappe.msgprint(__('Please enter a valid email address'));
		}
	}
}); 