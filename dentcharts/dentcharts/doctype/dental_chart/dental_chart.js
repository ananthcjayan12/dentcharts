// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Chart', {
	refresh: function(frm) {
		// Add custom buttons for chart actions
		if (!frm.is_new()) {
			frm.add_custom_button(__('Add Condition'), function() {
				frm.add_tooth_condition();
			});
			
			frm.add_custom_button(__('Add Procedure'), function() {
				frm.add_tooth_procedure();
			});
			
			frm.add_custom_button(__('View Chart Data'), function() {
				frm.show_chart_visualization();
			});
		}
		
		// Show dentition type info
		if (frm.doc.dentition_type) {
			frm.set_df_property('dentition_type', 'description', frm.get_dentition_description());
		}
	},
	
	dentition_type: function(frm) {
		// Update description when dentition type changes
		frm.set_df_property('dentition_type', 'description', frm.get_dentition_description());
		
		// Clear existing conditions and procedures if dentition type changes
		if (!frm.is_new() && frm.doc.tooth_conditions.length > 0) {
			frappe.confirm(
				__('Changing dentition type will clear existing conditions and procedures. Continue?'),
				function() {
					frm.clear_table('tooth_conditions');
					frm.clear_table('tooth_procedures');
					frm.refresh_fields();
				},
				function() {
					// Revert to previous value
					frm.reload_doc();
				}
			);
		}
	},
	
	get_dentition_description: function(frm) {
		const descriptions = {
			'Permanent': 'Adult teeth: 32 teeth using FDI numbering (11-48)',
			'Primary': 'Baby teeth: 20 teeth using Palmer notation (UR-A, UL-B, etc.)',
			'Mixed': 'Both permanent and primary teeth (for transitional cases)'
		};
		return descriptions[frm.doc.dentition_type] || '';
	},
	
	add_tooth_condition: function(frm) {
		// Get available teeth based on dentition type
		frappe.call({
			method: 'dentcharts.dentcharts.doctype.dental_chart.dental_chart.get_available_teeth_for_chart',
			args: {
				dentition_type: frm.doc.dentition_type
			},
			callback: function(r) {
				if (r.message) {
					let d = new frappe.ui.Dialog({
						title: __('Add Tooth Condition'),
						fields: [
							{
								fieldtype: 'Select',
								fieldname: 'tooth_number',
								label: __('Tooth Number'),
								options: r.message.join('\n'),
								reqd: 1
							},
							{
								fieldtype: 'Link',
								fieldname: 'condition_code',
								label: __('Condition'),
								options: 'Dental Condition Master',
								reqd: 1
							},
							{
								fieldtype: 'Select',
								fieldname: 'surface',
								label: __('Surface'),
								options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial',
								default: 'Whole Tooth'
							},
							{
								fieldtype: 'Small Text',
								fieldname: 'notes',
								label: __('Notes')
							}
						],
						primary_action_label: __('Add Condition'),
						primary_action: function(values) {
							let condition_row = frm.add_child('tooth_conditions');
							condition_row.tooth_number = values.tooth_number;
							condition_row.condition_code = values.condition_code;
							condition_row.surface = values.surface;
							condition_row.notes = values.notes;
							condition_row.date_identified = frappe.datetime.nowdate();
							condition_row.identified_by = frappe.session.user;
							
							frm.refresh_field('tooth_conditions');
							d.hide();
						}
					});
					d.show();
				}
			}
		});
	},
	
	add_tooth_procedure: function(frm) {
		// Get available teeth based on dentition type
		frappe.call({
			method: 'dentcharts.dentcharts.doctype.dental_chart.dental_chart.get_available_teeth_for_chart',
			args: {
				dentition_type: frm.doc.dentition_type
			},
			callback: function(r) {
				if (r.message) {
					let d = new frappe.ui.Dialog({
						title: __('Add Tooth Procedure'),
						fields: [
							{
								fieldtype: 'Select',
								fieldname: 'tooth_number',
								label: __('Tooth Number'),
								options: r.message.join('\n'),
								reqd: 1
							},
							{
								fieldtype: 'Link',
								fieldname: 'procedure_code',
								label: __('Procedure'),
								options: 'Dental Procedure Master',
								reqd: 1
							},
							{
								fieldtype: 'Select',
								fieldname: 'surface',
								label: __('Surface'),
								options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial',
								default: 'Whole Tooth'
							},
							{
								fieldtype: 'Select',
								fieldname: 'status',
								label: __('Status'),
								options: 'Planned\nIn Progress\nCompleted\nCancelled',
								default: 'Planned'
							},
							{
								fieldtype: 'Small Text',
								fieldname: 'notes',
								label: __('Notes')
							}
						],
						primary_action_label: __('Add Procedure'),
						primary_action: function(values) {
							let procedure_row = frm.add_child('tooth_procedures');
							procedure_row.tooth_number = values.tooth_number;
							procedure_row.procedure_code = values.procedure_code;
							procedure_row.surface = values.surface;
							procedure_row.status = values.status;
							procedure_row.notes = values.notes;
							procedure_row.planned_date = frappe.datetime.nowdate();
							procedure_row.planned_by = frappe.session.user;
							
							frm.refresh_field('tooth_procedures');
							d.hide();
						}
					});
					d.show();
				}
			}
		});
	},
	
	show_chart_visualization: function(frm) {
		frappe.call({
			method: 'dentcharts.dentcharts.doctype.dental_chart.dental_chart.get_chart_data',
			args: {
				chart_name: frm.doc.name
			},
			callback: function(r) {
				if (r.message) {
					let chart_data = r.message;
					let html = frm.build_chart_html(chart_data);
					
					frappe.msgprint({
						title: __('Dental Chart Visualization'),
						message: html,
						wide: true
					});
				}
			}
		});
	},
	
	build_chart_html: function(frm, chart_data) {
		let html = `<div style="text-align: center; padding: 20px;">
			<h3>${chart_data.patient} - ${chart_data.dentition_type} Dentition</h3>
			<p><strong>Chart Date:</strong> ${chart_data.chart_date}</p>
			<p><strong>Dentist:</strong> ${chart_data.dentist}</p>
			<br>
		`;
		
		// Group teeth by type
		let permanent_teeth = [];
		let primary_teeth = [];
		
		for (let [tooth_number, tooth_data] of Object.entries(chart_data.teeth)) {
			if (tooth_data.type === 'permanent') {
				permanent_teeth.push({number: tooth_number, data: tooth_data});
			} else {
				primary_teeth.push({number: tooth_number, data: tooth_data});
			}
		}
		
		// Show permanent teeth
		if (permanent_teeth.length > 0) {
			html += '<h4>Permanent Teeth</h4><div style="display: flex; flex-wrap: wrap; justify-content: center;">';
			permanent_teeth.forEach(tooth => {
				let status_color = frm.get_tooth_status_color(tooth.data.status);
				html += `
					<div style="display: inline-block; margin: 2px; padding: 5px; 
								background-color: ${status_color}; border: 1px solid #ccc; 
								border-radius: 3px; min-width: 40px; text-align: center;">
						<strong>${tooth.number}</strong>
						${tooth.data.conditions.length > 0 ? '<br>🦷' : ''}
						${tooth.data.procedures.length > 0 ? '<br>🔧' : ''}
					</div>
				`;
			});
			html += '</div><br>';
		}
		
		// Show primary teeth
		if (primary_teeth.length > 0) {
			html += '<h4>Primary Teeth</h4><div style="display: flex; flex-wrap: wrap; justify-content: center;">';
			primary_teeth.forEach(tooth => {
				let status_color = frm.get_tooth_status_color(tooth.data.status);
				html += `
					<div style="display: inline-block; margin: 2px; padding: 5px; 
								background-color: ${status_color}; border: 1px solid #ccc; 
								border-radius: 3px; min-width: 50px; text-align: center;">
						<strong>${tooth.number}</strong>
						${tooth.data.conditions.length > 0 ? '<br>🦷' : ''}
						${tooth.data.procedures.length > 0 ? '<br>🔧' : ''}
					</div>
				`;
			});
			html += '</div>';
		}
		
		html += `
			<br><br>
			<div style="text-align: left; display: inline-block;">
				<p><strong>Legend:</strong></p>
				<p>🦷 = Has Conditions</p>
				<p>🔧 = Has Procedures</p>
				<p style="background-color: #f8f9fa; padding: 2px;">⬜ = Healthy</p>
				<p style="background-color: #fff3cd; padding: 2px;">🟨 = Has Condition</p>
				<p style="background-color: #d1ecf1; padding: 2px;">🟦 = In Treatment</p>
				<p style="background-color: #d4edda; padding: 2px;">🟩 = Treated</p>
			</div>
		</div>`;
		
		return html;
	},
	
	get_tooth_status_color: function(frm, status) {
		const colors = {
			'healthy': '#f8f9fa',
			'has_condition': '#fff3cd',
			'in_treatment': '#d1ecf1',
			'treated': '#d4edda'
		};
		return colors[status] || '#f8f9fa';
	}
}); 