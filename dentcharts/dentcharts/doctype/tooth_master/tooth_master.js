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
		// This mirrors the Python logic for setting computed fields
		if (frm.doc.dentition_type === "Permanent" && frm.doc.universal_number) {
			let num = frm.doc.universal_number;
			
			if (num >= 1 && num <= 16) {
				frm.set_value('arch', 'Upper');
				if (num >= 1 && num <= 8) {
					frm.set_value('quadrant', 'Upper Right');
					frm.set_value('position_in_quadrant', 9 - num);
				} else {
					frm.set_value('quadrant', 'Upper Left');
					frm.set_value('position_in_quadrant', num - 8);
				}
			} else if (num >= 17 && num <= 32) {
				frm.set_value('arch', 'Lower');
				if (num >= 17 && num <= 24) {
					frm.set_value('quadrant', 'Lower Left');
					frm.set_value('position_in_quadrant', num - 16);
				} else {
					frm.set_value('quadrant', 'Lower Right');
					frm.set_value('position_in_quadrant', 33 - num);
				}
			}
		}
	}
}); 