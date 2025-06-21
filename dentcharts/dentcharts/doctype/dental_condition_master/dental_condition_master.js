// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Condition Master', {
	refresh: function(frm) {
		// Add button to create all standard conditions (for System Manager only)
		if (frappe.user.has_role('System Manager') && frm.doc.__islocal) {
			frm.add_custom_button(__('Create All Standard Conditions'), function() {
				frappe.confirm(
					__('This will create all standard dental conditions. Continue?'),
					function() {
						frappe.call({
							method: 'dentcharts.dentcharts.doctype.dental_condition_master.dental_condition_master.DentalConditionMaster.create_standard_conditions',
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
		
		// Color preview in form
		if (frm.doc.color_code && !frm.doc.__islocal) {
			frm.set_df_property('color_code', 'description', 
				`<div style="width: 30px; height: 20px; background-color: ${frm.doc.color_code}; border: 1px solid #ccc; margin-top: 5px;"></div>`);
		}
		
		// Show condition in chart preview
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Preview in Chart'), function() {
				let preview_html = `
					<div style="display: inline-block; padding: 10px; margin: 5px; 
								background-color: ${frm.doc.color_code || '#f8f9fa'}; 
								border: 2px solid #dee2e6; border-radius: 5px; text-align: center;">
						<div style="font-weight: bold; font-size: 16px;">${frm.doc.symbol || '?'}</div>
						<div style="font-size: 12px; margin-top: 5px;">${frm.doc.condition_name}</div>
					</div>
				`;
				frappe.msgprint({
					title: __('Chart Preview'),
					message: preview_html,
					primary_action: {
						action() {
							frappe.msgprint(__('Full dental chart visualization will be available in Phase 3B'));
						}
					}
				});
			});
		}
	},
	
	category: function(frm) {
		// Auto-set symbol based on category
		if (frm.doc.category && !frm.doc.symbol) {
			frm.trigger('set_default_symbol');
		}
	},
	
	severity: function(frm) {
		// Auto-set color based on severity
		if (frm.doc.severity && !frm.doc.color_code) {
			frm.trigger('set_default_color');
		}
		
		// Auto-set emergency flag for critical conditions
		if (frm.doc.severity === 'Critical') {
			frm.set_value('is_emergency', 1);
		}
	},
	
	set_default_symbol: function(frm) {
		let symbol_map = {
			"Caries": "C",
			"Periodontal": "P",
			"Endodontic": "E",
			"Prosthodontic": "Pr",
			"Orthodontic": "O",
			"Oral Surgery": "S",
			"Cosmetic": "Co",
			"Prevention": "Pv",
			"Emergency": "!",
			"Other": "?"
		};
		
		if (symbol_map[frm.doc.category]) {
			frm.set_value('symbol', symbol_map[frm.doc.category]);
		}
	},
	
	set_default_color: function(frm) {
		let color_map = {
			"Low": "#28a745",      // Green
			"Medium": "#ffc107",   // Yellow
			"High": "#fd7e14",     // Orange
			"Critical": "#dc3545"  // Red
		};
		
		if (color_map[frm.doc.severity]) {
			frm.set_value('color_code', color_map[frm.doc.severity]);
		}
	},
	
	is_emergency: function(frm) {
		// Auto-set severity to Critical for emergency conditions
		if (frm.doc.is_emergency && frm.doc.severity !== 'Critical') {
			frappe.confirm(
				__('Emergency conditions are typically Critical severity. Update severity?'),
				function() {
					frm.set_value('severity', 'Critical');
				}
			);
		}
	},
	
	color_code: function(frm) {
		// Update color preview
		if (frm.doc.color_code) {
			frm.set_df_property('color_code', 'description', 
				`<div style="width: 30px; height: 20px; background-color: ${frm.doc.color_code}; border: 1px solid #ccc; margin-top: 5px;"></div>`);
		}
	}
}); 