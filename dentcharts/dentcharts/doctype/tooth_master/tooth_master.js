// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tooth Master', {
	refresh: function(frm) {
		// Add buttons to create standard teeth (for System Manager only)
		if (frappe.user.has_role('System Manager') && frm.doc.__islocal) {
			frm.add_custom_button(__('Create All Permanent Teeth'), function() {
				frappe.confirm(
					__('This will create all 32 permanent teeth with FDI numbering. Continue?'),
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
			
			frm.add_custom_button(__('Create All Primary Teeth'), function() {
				frappe.confirm(
					__('This will create all 20 primary teeth with FDI numbering. Continue?'),
					function() {
						frappe.call({
							method: 'dentcharts.dentcharts.doctype.tooth_master.tooth_master.ToothMaster.create_standard_primary_teeth',
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
				let chart_info = `
					<div style="text-align: center; padding: 20px;">
						<h3>Tooth ${frm.doc.tooth_number || frm.doc.universal_number} - ${frm.doc.tooth_name}</h3>
						<p><strong>Arch:</strong> ${frm.doc.arch}</p>
						<p><strong>Quadrant:</strong> ${frm.doc.quadrant}</p>
						<p><strong>Type:</strong> ${frm.doc.tooth_type}</p>
						<p><strong>Dentition:</strong> ${frm.doc.dentition_type}</p>
						<p><strong>Position in Quadrant:</strong> ${frm.doc.position_in_quadrant}</p>
						${frm.doc.surfaces ? `<p><strong>Surfaces:</strong> ${JSON.parse(frm.doc.surfaces).join(', ')}</p>` : ''}
					</div>
				`;
				
				frappe.msgprint({
					title: __('Tooth Chart Information'),
					message: chart_info,
					primary_action: {
						label: __('View Dental Charts'),
						action() {
							frappe.set_route('List', 'Dental Chart');
						}
					}
				});
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
		if (frm.doc.universal_number || frm.doc.tooth_number) {
			frm.trigger('set_computed_fields');
		}
	},
	
	tooth_number: function(frm) {
		// Auto-set computed fields when tooth number changes (for primary teeth)
		if (frm.doc.dentition_type === "Primary" && frm.doc.tooth_number) {
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
		// Handle both FDI (permanent) and Palmer (primary) notation systems
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
		} else if (frm.doc.dentition_type === "Primary" && frm.doc.tooth_number && frm.doc.tooth_number.includes('-')) {
			// Palmer notation for primary teeth: "UR-A", "UL-B", etc.
			let parts = frm.doc.tooth_number.split('-');
			if (parts.length === 2) {
				let quadrant_code = parts[0];
				let letter = parts[1];
				
				if (quadrant_code === "UR") {  // Upper Right
					frm.set_value('arch', 'Upper');
					frm.set_value('quadrant', 'Upper Right');
				} else if (quadrant_code === "UL") {  // Upper Left
					frm.set_value('arch', 'Upper');
					frm.set_value('quadrant', 'Upper Left');
				} else if (quadrant_code === "LL") {  // Lower Left
					frm.set_value('arch', 'Lower');
					frm.set_value('quadrant', 'Lower Left');
				} else if (quadrant_code === "LR") {  // Lower Right
					frm.set_value('arch', 'Lower');
					frm.set_value('quadrant', 'Lower Right');
				}
				
				// Position based on letter (A=1, B=2, C=3, D=4, E=5)
				if (letter && letter.length === 1 && letter >= 'A' && letter <= 'E') {
					frm.set_value('position_in_quadrant', letter.charCodeAt(0) - 'A'.charCodeAt(0) + 1);
				}
			}
		}
	}
}); 