// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tooth Master', {
	refresh: function(frm) {
		// Add button to create all standard teeth (for System Manager only)
		if (frappe.user.has_role('System Manager') && frm.doc.__islocal) {
			frm.add_custom_button(__('Create All Standard Teeth'), function() {
				frappe.confirm(
					__('This will create all 32 permanent teeth. Continue?'),
					function() {
						frappe.call({
							method: 'dentcharts.dentcharts.doctype.tooth_master.tooth_master.ToothMaster.create_standard_teeth',
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
		
		// Show tooth chart position info
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('View in Chart'), function() {
				frappe.msgprint(__('Tooth chart visualization will be available in Phase 3B'));
			});
		}
	},
	
	universal_number: function(frm) {
		// Auto-set computed fields when universal number changes
		if (frm.doc.universal_number && frm.doc.dentition_type === "Permanent") {
			frm.trigger('set_computed_fields');
		}
	},
	
	dentition_type: function(frm) {
		// Update validation when dentition type changes
		if (frm.doc.universal_number) {
			frm.trigger('set_computed_fields');
		}
	},
	
	tooth_type: function(frm) {
		// Set default surfaces based on tooth type
		if (frm.doc.tooth_type && !frm.doc.surfaces) {
			let surfaces;
			if (['Incisor', 'Canine'].includes(frm.doc.tooth_type)) {
				surfaces = ["Incisal", "Mesial", "Distal", "Facial", "Lingual"];
			} else {
				surfaces = ["Occlusal", "Mesial", "Distal", "Buccal", "Lingual"];
			}
			frm.set_value('surfaces', JSON.stringify(surfaces));
		}
	},
	
	set_computed_fields: function(frm) {
		// This mirrors the Python logic for FDI numbering system
		if (frm.doc.dentition_type === "Permanent" && frm.doc.universal_number) {
			let num = frm.doc.universal_number;
			
			// FDI notation: First digit = quadrant, Second digit = position
			let quadrant_digit = Math.floor(num / 10);
			let position_digit = num % 10;
			
			if (quadrant_digit === 1) {  // Upper Right (11-18)
				frm.set_value('arch', 'Upper');
				frm.set_value('quadrant', 'Upper Right');
				frm.set_value('position_in_quadrant', position_digit);
			} else if (quadrant_digit === 2) {  // Upper Left (21-28)
				frm.set_value('arch', 'Upper');
				frm.set_value('quadrant', 'Upper Left');
				frm.set_value('position_in_quadrant', position_digit);
			} else if (quadrant_digit === 3) {  // Lower Left (31-38)
				frm.set_value('arch', 'Lower');
				frm.set_value('quadrant', 'Lower Left');
				frm.set_value('position_in_quadrant', position_digit);
			} else if (quadrant_digit === 4) {  // Lower Right (41-48)
				frm.set_value('arch', 'Lower');
				frm.set_value('quadrant', 'Lower Right');
				frm.set_value('position_in_quadrant', position_digit);
			}
		}
	}
}); 