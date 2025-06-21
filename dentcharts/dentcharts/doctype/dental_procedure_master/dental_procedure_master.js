// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Procedure Master', {
	refresh: function(frm) {
		// Add button to create all standard procedures (for System Manager only)
		if (frappe.user.has_role('System Manager') && frm.doc.__islocal) {
			frm.add_custom_button(__('Create All Standard Procedures'), function() {
				frappe.confirm(
					__('This will create all standard dental procedures. Continue?'),
					function() {
						frappe.call({
							method: 'dentcharts.dentcharts.doctype.dental_procedure_master.dental_procedure_master.DentalProcedureMaster.create_standard_procedures',
							callback: function(r) {
								if (r.message) {
									frappe.msgprint(r.message);
									frm.reload_doc();
								}
							}
						});
					}
				);
			});
		}
		
		// Calculate estimated cost with insurance
		if (frm.doc.standard_fee && frm.doc.insurance_coverage && !frm.doc.__islocal) {
			let patient_cost = frm.doc.standard_fee * (1 - (frm.doc.insurance_coverage / 100));
			frm.add_custom_button(__('Cost Calculator'), function() {
				frappe.msgprint({
					title: __('Cost Breakdown'),
					message: `
						<table class="table table-bordered">
							<tr><td><strong>Standard Fee:</strong></td><td>${format_currency(frm.doc.standard_fee, frm.doc.currency)}</td></tr>
							<tr><td><strong>Insurance Coverage:</strong></td><td>${frm.doc.insurance_coverage}%</td></tr>
							<tr><td><strong>Patient Cost:</strong></td><td>${format_currency(patient_cost, frm.doc.currency)}</td></tr>
							<tr><td><strong>Duration:</strong></td><td>${frm.doc.duration_minutes} minutes</td></tr>
						</table>
					`
				});
			});
		}
	},
	
	complexity: function(frm) {
		// Auto-suggest duration based on complexity
		if (frm.doc.complexity && !frm.doc.duration_minutes) {
			let duration_map = {
				"Simple": 30,
				"Moderate": 60,
				"Complex": 90,
				"Advanced": 120
			};
			
			if (duration_map[frm.doc.complexity]) {
				frm.set_value('duration_minutes', duration_map[frm.doc.complexity]);
			}
		}
		
		// Auto-suggest anesthesia based on complexity
		if (frm.doc.complexity && !frm.doc.anesthesia_required) {
			let anesthesia_map = {
				"Simple": "None",
				"Moderate": "Local",
				"Complex": "Local",
				"Advanced": "IV Sedation"
			};
			
			if (anesthesia_map[frm.doc.complexity]) {
				frm.set_value('anesthesia_required', anesthesia_map[frm.doc.complexity]);
			}
		}
	},
	
	category: function(frm) {
		// Auto-set follow-up requirements based on category
		if (frm.doc.category) {
			let follow_up_categories = ['Restorative', 'Endodontic', 'Oral Surgery', 'Periodontal', 'Emergency'];
			
			if (follow_up_categories.includes(frm.doc.category) && !frm.doc.follow_up_required) {
				frm.set_value('follow_up_required', 1);
				
				// Set default follow-up days
				let follow_up_days_map = {
					'Restorative': 14,
					'Endodontic': 7,
					'Oral Surgery': 7,
					'Periodontal': 14,
					'Emergency': 3
				};
				
				if (follow_up_days_map[frm.doc.category]) {
					frm.set_value('follow_up_days', follow_up_days_map[frm.doc.category]);
				}
			}
		}
	},
	
	follow_up_required: function(frm) {
		// Clear follow-up days if not required
		if (!frm.doc.follow_up_required) {
			frm.set_value('follow_up_days', null);
		}
	},
	
	standard_fee: function(frm) {
		// Auto-set currency if not specified
		if (frm.doc.standard_fee && !frm.doc.currency) {
			frappe.call({
				method: 'frappe.defaults.get_user_default',
				args: {key: 'currency'},
				callback: function(r) {
					if (r.message) {
						frm.set_value('currency', r.message);
					} else {
						frm.set_value('currency', 'USD');
					}
				}
			});
		}
	},
	
	duration_minutes: function(frm) {
		// Validate duration
		if (frm.doc.duration_minutes > 480) {
			frappe.msgprint(__('Duration exceeds 8 hours. Please verify this is correct.'));
		}
	}
}); 