// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Chart', {
	refresh: function(frm) {
		// Clear any existing dashboard sections first
		frm.dashboard.clear_headline();
		
		// Show master chart header
		if (!frm.is_new()) {
			// Add master chart indicator
			if (frm.doc.chart_type === 'Master Chart') {
				frm.dashboard.set_headline(`
					<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
						<h4 style="margin: 0 0 5px 0;">🦷 Master Dental Chart - ${frm.doc.patient_name}</h4>
						<p style="margin: 0; opacity: 0.9;">Lifetime dental record • Last updated: ${frappe.datetime.str_to_user(frm.doc.modified)}</p>
						<div style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">
							<strong>📋 Current Dentition: ${frm.doc.dentition_type || 'Permanent'}</strong>
							<span style="margin-left: 15px; opacity: 0.8;">${get_dentition_description(frm.doc.dentition_type)}</span>
						</div>
					</div>
				`);
			}
			
			// Clear any existing chart sections
			$('.dental-chart-container').remove();
			
			// Create interactive dental chart
			create_interactive_dental_chart(frm);
			
			// Add visit management buttons
			frm.add_custom_button(__('Record Visit'), function() {
				record_new_visit(frm);
			}, __('Actions'));
			
			frm.add_custom_button(__('View History'), function() {
				show_dental_history(frm);
			}, __('Actions'));
			
			frm.add_custom_button(__('Print Chart'), function() {
				frm.print_doc();
			}, __('Actions'));
		}
		
		// Show dentition type info
		if (frm.doc.dentition_type) {
			frm.set_df_property('dentition_type', 'description', get_dentition_description(frm.doc.dentition_type));
			update_dentition_info_display(frm);
		}
	},
	
	// Handle dentition type change - refresh chart immediately
	dentition_type: function(frm) {
		// Update description when dentition type changes
		frm.set_df_property('dentition_type', 'description', get_dentition_description(frm.doc.dentition_type));
		update_dentition_info_display(frm);
		
		if (!frm.is_new()) {
			// Show loading indicator
			frappe.show_alert({
				message: __('Updating dental chart...'),
				indicator: 'blue'
			});
			
			// Clear existing conditions and procedures if dentition type changes
			if (frm.doc.tooth_conditions && frm.doc.tooth_conditions.length > 0) {
				frappe.confirm(
					__('Changing dentition type will clear existing conditions and procedures. Continue?'),
					function() {
						frm.clear_table('tooth_conditions');
						frm.clear_table('tooth_procedures');
						frm.refresh_fields();
						
						// Save and refresh chart immediately
						frm.save().then(() => {
							refresh_dental_chart(frm);
							frappe.show_alert({
								message: __('Dental chart updated for ' + frm.doc.dentition_type + ' teeth'),
								indicator: 'green'
							});
						});
					},
					function() {
						// Revert to previous value
						frm.reload_doc();
					}
				);
			} else {
				// Save and refresh chart immediately if no existing data
				frm.save().then(() => {
					refresh_dental_chart(frm);
					frappe.show_alert({
						message: __('Dental chart updated for ' + frm.doc.dentition_type + ' teeth'),
						indicator: 'green'
					});
				});
			}
		}
	}
});

function get_dentition_description(dentition_type) {
	const descriptions = {
		'Permanent': 'Adult teeth: 32 teeth using FDI numbering (11-48)',
		'Primary': 'Baby teeth: 20 teeth using Palmer notation (UR-A, UL-B, etc.)',
		'Mixed': 'Both permanent and primary teeth (for transitional cases)'
	};
	return descriptions[dentition_type] || '';
}

function create_interactive_dental_chart(frm) {
	// Store form reference globally for multi-selection functions
	window.current_frm = frm;
	
	// Get chart data first
	frappe.call({
		method: 'dentcharts.dentcharts.doctype.dental_chart.dental_chart.get_chart_data',
		args: {
			chart_name: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				let chart_data = r.message;
				let chart_html = build_interactive_chart_html(frm, chart_data);
				
				// Clear any existing chart sections before adding new one
				$('.dental-chart-container').remove();
				
				// Add chart directly to the form's layout container instead of dashboard
				let form_layout = frm.page.main.find('.frappe-control[data-fieldname="tooth_conditions_section"]').parent();
				if (form_layout.length) {
					form_layout.before(chart_html);
				} else {
					// Fallback to dashboard if section not found
					frm.dashboard.add_section(chart_html, __('Interactive Dental Chart'));
				}
				
				// Attach click handlers after DOM is ready
				setTimeout(() => {
					attach_tooth_click_handlers(frm);
				}, 200);
			}
		}
	});
}

// Global variable to track selected teeth
window.selected_teeth = [];

function build_interactive_chart_html(frm, chart_data) {
	let html = `
		<div class="dental-chart-container" style="background: white; padding: 20px; border: 1px solid #d1d8dd; border-radius: 6px; margin: 10px 0;">
			<div style="text-align: center; margin-bottom: 20px;">
				<div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
					<h4 style="margin: 0 0 8px 0;">${chart_data.patient} - Dental Chart</h4>
					<div style="display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap;">
						<div style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 4px;">
							<strong>🦷 ${chart_data.dentition_type} Dentition</strong>
						</div>
						<div style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 4px; font-size: 14px;">
							${get_dentition_description(chart_data.dentition_type)}
						</div>
					</div>
				</div>
				<div style="margin-bottom: 15px;">
					<p style="color: #6c757d; margin: 5px 0;">🖱️ Click teeth to select • Hold Ctrl/Cmd for multiple selection</p>
					<div id="selection-info" style="background: #e3f2fd; padding: 8px; border-radius: 4px; margin: 10px 0; min-height: 20px;">
						<span style="color: #1565c0; font-weight: bold;">No teeth selected</span>
					</div>
					<div id="multi-actions" style="display: none; margin: 10px 0;">
						<button class="btn btn-sm btn-primary" onclick="window.add_condition_to_selected()" style="margin: 2px;">Add Condition to Selected</button>
						<button class="btn btn-sm btn-success" onclick="window.add_procedure_to_selected()" style="margin: 2px;">Add Procedure to Selected</button>
						<button class="btn btn-sm btn-secondary" onclick="window.clear_selection()" style="margin: 2px;">Clear Selection</button>
					</div>
				</div>
			</div>
	`;

	if (chart_data.dentition_type === 'Primary' || chart_data.dentition_type === 'Mixed') {
		html += build_primary_teeth_chart(frm, chart_data);
	}
	
	if (chart_data.dentition_type === 'Permanent' || chart_data.dentition_type === 'Mixed') {
		html += build_permanent_teeth_chart(frm, chart_data);
	}

	html += `
			<div style="margin-top: 20px; text-align: center;">
				<div style="display: inline-block; text-align: left;">
					<p style="margin: 5px 0;"><span style="display: inline-block; width: 20px; height: 15px; background: #f8f9fa; border: 1px solid #ccc; margin-right: 8px;"></span> Healthy</p>
					<p style="margin: 5px 0;"><span style="display: inline-block; width: 20px; height: 15px; background: #fff3cd; border: 1px solid #ccc; margin-right: 8px;"></span> Has Condition</p>
					<p style="margin: 5px 0;"><span style="display: inline-block; width: 20px; height: 15px; background: #d1ecf1; border: 1px solid #ccc; margin-right: 8px;"></span> In Treatment</p>
					<p style="margin: 5px 0;"><span style="display: inline-block; width: 20px; height: 15px; background: #d4edda; border: 1px solid #ccc; margin-right: 8px;"></span> Treated</p>
				</div>
			</div>
		</div>
	`;

	return html;
}

function build_primary_teeth_chart(frm, chart_data) {
	let html = '<div style="margin-bottom: 30px;"><h5 style="text-align: center; color: #495057;">Primary Teeth (Baby Teeth)</h5>';
	
	// Upper jaw
	html += '<div style="text-align: center; margin: 20px 0;"><p style="margin: 5px 0; font-weight: bold;">Upper Jaw</p>';
	html += '<div style="display: flex; justify-content: center; margin: 10px 0;">';
	
	// Upper Right (E,D,C,B,A)
	['UR-E', 'UR-D', 'UR-C', 'UR-B', 'UR-A'].forEach(tooth => {
		html += create_tooth_element(tooth, chart_data.teeth[tooth] || {status: 'healthy', conditions: [], procedures: [], type: 'primary'});
	});
	
	html += '<div style="width: 20px;"></div>'; // Space between sides
	
	// Upper Left (A,B,C,D,E)
	['UL-A', 'UL-B', 'UL-C', 'UL-D', 'UL-E'].forEach(tooth => {
		html += create_tooth_element(tooth, chart_data.teeth[tooth] || {status: 'healthy', conditions: [], procedures: [], type: 'primary'});
	});
	
	html += '</div></div>';
	
	// Lower jaw
	html += '<div style="text-align: center; margin: 20px 0;"><p style="margin: 5px 0; font-weight: bold;">Lower Jaw</p>';
	html += '<div style="display: flex; justify-content: center; margin: 10px 0;">';
	
	// Lower Right (E,D,C,B,A)
	['LR-E', 'LR-D', 'LR-C', 'LR-B', 'LR-A'].forEach(tooth => {
		html += create_tooth_element(tooth, chart_data.teeth[tooth] || {status: 'healthy', conditions: [], procedures: [], type: 'primary'});
	});
	
	html += '<div style="width: 20px;"></div>'; // Space between sides
	
	// Lower Left (A,B,C,D,E)
	['LL-A', 'LL-B', 'LL-C', 'LL-D', 'LL-E'].forEach(tooth => {
		html += create_tooth_element(tooth, chart_data.teeth[tooth] || {status: 'healthy', conditions: [], procedures: [], type: 'primary'});
	});
	
	html += '</div></div></div>';
	
	return html;
}

function build_permanent_teeth_chart(frm, chart_data) {
	let html = '<div><h5 style="text-align: center; color: #495057;">Permanent Teeth (Adult Teeth)</h5>';
	
	// Upper jaw
	html += '<div style="text-align: center; margin: 20px 0;"><p style="margin: 5px 0; font-weight: bold;">Upper Jaw</p>';
	html += '<div style="display: flex; justify-content: center; margin: 10px 0;">';
	
	// Upper Right (18,17,16,15,14,13,12,11)
	for(let i = 18; i >= 11; i--) {
		html += create_tooth_element(i.toString(), chart_data.teeth[i.toString()] || {status: 'healthy', conditions: [], procedures: [], type: 'permanent'});
	}
	
	html += '<div style="width: 20px;"></div>'; // Space between sides
	
	// Upper Left (21,22,23,24,25,26,27,28)
	for(let i = 21; i <= 28; i++) {
		html += create_tooth_element(i.toString(), chart_data.teeth[i.toString()] || {status: 'healthy', conditions: [], procedures: [], type: 'permanent'});
	}
	
	html += '</div></div>';
	
	// Lower jaw
	html += '<div style="text-align: center; margin: 20px 0;"><p style="margin: 5px 0; font-weight: bold;">Lower Jaw</p>';
	html += '<div style="display: flex; justify-content: center; margin: 10px 0;">';
	
	// Lower Right (48,47,46,45,44,43,42,41)
	for(let i = 48; i >= 41; i--) {
		html += create_tooth_element(i.toString(), chart_data.teeth[i.toString()] || {status: 'healthy', conditions: [], procedures: [], type: 'permanent'});
	}
	
	html += '<div style="width: 20px;"></div>'; // Space between sides
	
	// Lower Left (31,32,33,34,35,36,37,38)
	for(let i = 31; i <= 38; i++) {
		html += create_tooth_element(i.toString(), chart_data.teeth[i.toString()] || {status: 'healthy', conditions: [], procedures: [], type: 'permanent'});
	}
	
	html += '</div></div></div>';
	
	return html;
}

function create_tooth_element(tooth_number, tooth_data) {
	let status_color = get_tooth_status_color(tooth_data.status);
	let has_conditions = tooth_data.conditions && tooth_data.conditions.length > 0;
	let has_procedures = tooth_data.procedures && tooth_data.procedures.length > 0;
	
	return `
		<div class="tooth-element" data-tooth="${tooth_number}" 
			 style="display: inline-block; margin: 2px; padding: 8px 6px; min-width: 35px; 
					background-color: ${status_color}; border: 2px solid #495057; 
					border-radius: 4px; text-align: center; cursor: pointer; 
					transition: all 0.2s ease; font-size: 11px; font-weight: bold;
					position: relative; user-select: none;"
			 onmouseover="this.style.transform='scale(1.1)'; this.style.zIndex='10';"
			 onmouseout="this.style.transform='scale(1)'; this.style.zIndex='1';"
			 title="Click to select tooth ${tooth_number} • Ctrl+Click for multiple selection">
			<div>${tooth_number}</div>
			${has_conditions ? '<div style="color: #dc3545; font-size: 10px;">🦷</div>' : ''}
			${has_procedures ? '<div style="color: #007bff; font-size: 10px;">🔧</div>' : ''}
		</div>
	`;
}

function attach_tooth_click_handlers(frm) {
	$(document).off('click', '.tooth-element');
	$(document).on('click', '.tooth-element', function(e) {
		let tooth_number = $(this).data('tooth');
		
		// Handle multi-selection with Ctrl/Cmd key
		if (e.ctrlKey || e.metaKey) {
			toggle_tooth_selection(tooth_number, $(this));
		} else {
			// Single selection - if no teeth selected, show dialog
			// If teeth are selected, clear selection and select this one
			if (window.selected_teeth.length === 0) {
				show_enhanced_tooth_dialog(frm, tooth_number);
			} else {
				clear_selection();
				toggle_tooth_selection(tooth_number, $(this));
			}
		}
		
		e.preventDefault();
		e.stopPropagation();
	});
}

function toggle_tooth_selection(tooth_number, element) {
	let index = window.selected_teeth.indexOf(tooth_number);
	
	if (index > -1) {
		// Deselect tooth
		window.selected_teeth.splice(index, 1);
		element.css({
			'box-shadow': 'none',
			'border-color': '#495057'
		});
	} else {
		// Select tooth
		window.selected_teeth.push(tooth_number);
		element.css({
			'box-shadow': '0 0 0 3px rgba(0, 123, 255, 0.5)',
			'border-color': '#007bff'
		});
	}
	
	update_selection_info();
}

function update_selection_info() {
	let info_div = $('#selection-info');
	let actions_div = $('#multi-actions');
	
	if (window.selected_teeth.length === 0) {
		info_div.html('<span style="color: #1565c0; font-weight: bold;">No teeth selected</span>');
		actions_div.hide();
	} else if (window.selected_teeth.length === 1) {
		info_div.html(`<span style="color: #1565c0; font-weight: bold;">Selected: Tooth ${window.selected_teeth[0]}</span>`);
		actions_div.show();
	} else {
		info_div.html(`<span style="color: #1565c0; font-weight: bold;">Selected: ${window.selected_teeth.length} teeth (${window.selected_teeth.join(', ')})</span>`);
		actions_div.show();
	}
}

window.clear_selection = function() {
	window.selected_teeth = [];
	$('.tooth-element').css({
		'box-shadow': 'none',
		'border-color': '#495057'
	});
	update_selection_info();
}

function show_enhanced_tooth_dialog(frm, tooth_number) {
	// Refresh form to ensure we have latest data
	frm.refresh_fields();
	
	// Get existing conditions and procedures for this tooth
	let existing_conditions = (frm.doc.tooth_conditions || []).filter(c => {
		// Handle both direct match and string conversion
		return String(c.tooth_number) === String(tooth_number);
	});
	
	let existing_procedures = (frm.doc.tooth_procedures || []).filter(p => {
		// Handle both direct match and string conversion
		return String(p.tooth_number) === String(tooth_number);
	});
	
	// Create enhanced dialog with inline editing
	let dialog_fields = [
		{
			fieldtype: 'HTML',
			options: `
				<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
					<h4 style="margin: 0; text-align: center;">🦷 Tooth ${tooth_number} - Complete Management</h4>
				</div>
			`
		}
	];

	// Add existing conditions section with inline editing
	if (existing_conditions.length > 0) {
		dialog_fields.push({
			fieldtype: 'Section Break',
			label: '🦷 Current Conditions'
		});

		existing_conditions.forEach((condition, index) => {
			dialog_fields.push({
				fieldtype: 'Column Break',
				label: `Condition ${index + 1}`
			});
			dialog_fields.push({
				fieldtype: 'Link',
				fieldname: `condition_code_${index}`,
				label: 'Condition',
				options: 'Dental Condition Master',
				default: condition.condition_code,
				onchange: function() {
					// Update the condition in the form
					frm.doc.tooth_conditions[frm.doc.tooth_conditions.findIndex(c => c.name === condition.name)].condition_code = this.value;
					frm.refresh_field('tooth_conditions');
				}
			});
			dialog_fields.push({
				fieldtype: 'Select',
				fieldname: `condition_surface_${index}`,
				label: 'Surface',
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial',
				default: condition.surface
			});
			dialog_fields.push({
				fieldtype: 'Select',
				fieldname: `condition_severity_${index}`,
				label: 'Severity',
				options: '\nMild\nModerate\nSevere',
				default: condition.severity
			});
			dialog_fields.push({
				fieldtype: 'Small Text',
				fieldname: `condition_notes_${index}`,
				label: 'Notes',
				default: condition.notes
			});
			dialog_fields.push({
				fieldtype: 'HTML',
				options: `<button class="btn btn-sm btn-danger" onclick="window.remove_condition('${condition.name}')">Remove Condition</button>`
			});
		});
	}

	// Add existing procedures section with inline editing
	if (existing_procedures.length > 0) {
		dialog_fields.push({
			fieldtype: 'Section Break',
			label: '🔧 Current Procedures'
		});

		existing_procedures.forEach((procedure, index) => {
			dialog_fields.push({
				fieldtype: 'Column Break',
				label: `Procedure ${index + 1}`
			});
			dialog_fields.push({
				fieldtype: 'Link',
				fieldname: `procedure_code_${index}`,
				label: 'Procedure',
				options: 'Dental Procedure Master',
				default: procedure.procedure_code
			});
			dialog_fields.push({
				fieldtype: 'Select',
				fieldname: `procedure_surface_${index}`,
				label: 'Surface',
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial',
				default: procedure.surface
			});
			dialog_fields.push({
				fieldtype: 'Select',
				fieldname: `procedure_status_${index}`,
				label: 'Status',
				options: 'Planned\nIn Progress\nCompleted\nCancelled',
				default: procedure.status,
				change: function() {
					// Update status and dates based on selection
					if (this.value === 'Completed' && !procedure.completed_date) {
						// Auto-set completion date
						frappe.db.set_value('Tooth Procedure', procedure.name, 'completed_date', frappe.datetime.nowdate());
					}
				}
			});
			dialog_fields.push({
				fieldtype: 'Small Text',
				fieldname: `procedure_notes_${index}`,
				label: 'Notes',
				default: procedure.notes
			});
			dialog_fields.push({
				fieldtype: 'HTML',
				options: `<button class="btn btn-sm btn-danger" onclick="window.remove_procedure('${procedure.name}')">Remove Procedure</button>`
			});
		});
	}

	// Add new condition/procedure sections
	dialog_fields.push({
		fieldtype: 'Section Break',
		label: '➕ Add New'
	});
	
	dialog_fields.push({
		fieldtype: 'HTML',
		options: `
			<div style="display: flex; gap: 10px; justify-content: center; margin: 15px 0;">
				<button class="btn btn-primary" onclick="window.add_new_condition_inline()">Add New Condition</button>
				<button class="btn btn-success" onclick="window.add_new_procedure_inline()">Add New Procedure</button>
			</div>
		`
	});

	let d = new frappe.ui.Dialog({
		title: __('Tooth Management - ') + tooth_number,
		fields: dialog_fields,
		size: 'large',
		primary_action_label: __('Save Changes'),
		primary_action: function(values) {
			save_tooth_changes(frm, tooth_number, existing_conditions, existing_procedures, values);
			d.hide();
		}
	});

	// Store references for inline functions
	window.current_tooth_dialog = d;
	window.current_frm = frm;
	window.current_tooth = tooth_number;

	d.show();
}

function add_tooth_condition_for_tooth(frm, selected_tooth) {
	let d = new frappe.ui.Dialog({
		title: __('Add Condition to Tooth ') + selected_tooth,
		fields: [
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
			condition_row.tooth_number = selected_tooth;
			condition_row.condition_code = values.condition_code;
			condition_row.surface = values.surface;
			condition_row.notes = values.notes;
			condition_row.date_identified = frappe.datetime.nowdate();
			condition_row.identified_by = frappe.session.user;
			
			frm.refresh_field('tooth_conditions');
			frm.save();
			d.hide();
			
			// Refresh the interactive chart
			setTimeout(() => {
				create_interactive_dental_chart(frm);
			}, 500);
		}
	});
	d.show();
}

function add_tooth_procedure_for_tooth(frm, selected_tooth) {
	let d = new frappe.ui.Dialog({
		title: __('Add Procedure to Tooth ') + selected_tooth,
		fields: [
			{
				fieldtype: 'Link',
				fieldname: 'procedure_code',
				label: __('Procedure'),
				options: 'Dental Procedure Master',
				reqd: 1,
				change: function() {
					let procedure_code = d.get_value('procedure_code');
					if (procedure_code) {
						// Fetch procedure details and update cost fields
						frappe.call({
							method: 'frappe.client.get',
							args: {
								doctype: 'Dental Procedure Master',
								name: procedure_code
							},
							callback: function(r) {
								if (r.message) {
									let procedure = r.message;
									// Update cost fields with prefilled values
									d.set_value('standard_fee', procedure.standard_fee || 0);
									d.set_value('actual_fee', procedure.standard_fee || 0);
									d.set_value('duration_minutes', procedure.duration_minutes || 0);
									
									// Update cost info display
									update_cost_info_display(d, procedure);
								}
							}
						});
					}
				}
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
				options: 'Planned\nScheduled\nIn Progress\nCompleted\nCancelled',
				default: 'Planned'
			},
			{
				fieldtype: 'Section Break',
				label: __('Cost Information')
			},
			{
				fieldtype: 'HTML',
				fieldname: 'cost_info',
				label: __('Cost Details')
			},
			{
				fieldtype: 'Currency',
				fieldname: 'standard_fee',
				label: __('Standard Fee'),
				read_only: 1,
				description: __('This is the standard fee from procedure master')
			},
			{
				fieldtype: 'Currency',
				fieldname: 'actual_fee',
				label: __('Actual Fee (Editable)'),
				description: __('You can modify this amount as needed')
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'insurance_covered',
				label: __('Insurance Covered'),
				default: 0
			},
			{
				fieldtype: 'Currency',
				fieldname: 'patient_portion',
				label: __('Patient Portion'),
				read_only: 1,
				description: __('Calculated as: Actual Fee - Insurance Covered')
			},
			{
				fieldtype: 'Section Break',
				label: __('Additional Details')
			},
			{
				fieldtype: 'Int',
				fieldname: 'duration_minutes',
				label: __('Duration (Minutes)'),
				read_only: 1
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: __('Procedure Notes')
			}
		],
		primary_action_label: __('Add Procedure'),
		primary_action: function(values) {
			let procedure_row = frm.add_child('tooth_procedures');
			procedure_row.tooth_number = selected_tooth;
			procedure_row.procedure_code = values.procedure_code;
			procedure_row.surface = values.surface;
			procedure_row.status = values.status;
			procedure_row.notes = values.notes;
			procedure_row.planned_date = frappe.datetime.nowdate();
			procedure_row.planned_by = frappe.session.user;
			
			// Add cost information
			procedure_row.standard_fee = values.standard_fee || 0;
			procedure_row.actual_fee = values.actual_fee || 0;
			procedure_row.insurance_covered = values.insurance_covered || 0;
			procedure_row.patient_portion = (values.actual_fee || 0) - (values.insurance_covered || 0);
			procedure_row.duration_minutes = values.duration_minutes || 0;
			
			frm.refresh_field('tooth_procedures');
			frm.save();
			d.hide();
			
			// Show success message with cost summary
			frappe.show_alert({
				message: __(`Procedure added: ${values.procedure_code} - Fee: ${format_currency(values.actual_fee || 0)}`),
				indicator: 'green'
			});
			
			// Refresh the interactive chart
			setTimeout(() => {
				create_interactive_dental_chart(frm);
			}, 500);
		}
	});
	
	// Add change handler for insurance and actual fee to calculate patient portion
	d.fields_dict.actual_fee.$input.on('change', function() {
		calculate_patient_portion(d);
	});
	
	d.fields_dict.insurance_covered.$input.on('change', function() {
		calculate_patient_portion(d);
	});
	
	d.show();
}

// Multi-selection functions - Attach to window for global access
window.add_condition_to_selected = function() {
	if (window.selected_teeth.length === 0) {
		frappe.msgprint('Please select teeth first');
		return;
	}
	
	let d = new frappe.ui.Dialog({
		title: __(`Add Condition to ${window.selected_teeth.length} Selected Teeth`),
		fields: [
			{
				fieldtype: 'HTML',
				options: `<p><strong>Selected Teeth:</strong> ${window.selected_teeth.join(', ')}</p>`
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
				fieldtype: 'Select',
				fieldname: 'severity',
				label: __('Severity'),
				options: '\nMild\nModerate\nSevere'
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: __('Notes')
			}
		],
		primary_action_label: __('Add to All Selected'),
		primary_action: function(values) {
			let frm = window.current_frm;
			
			window.selected_teeth.forEach(tooth_number => {
				let condition_row = frm.add_child('tooth_conditions');
				condition_row.tooth_number = tooth_number;
				condition_row.condition_code = values.condition_code;
				condition_row.surface = values.surface;
				condition_row.severity = values.severity;
				condition_row.notes = values.notes;
				condition_row.date_identified = frappe.datetime.nowdate();
				condition_row.identified_by = frappe.session.user;
			});
			
			frm.refresh_field('tooth_conditions');
			frm.save();
			d.hide();
			clear_selection();
			
			// Refresh the chart
			setTimeout(() => {
				create_interactive_dental_chart(frm);
			}, 500);
			
			frappe.show_alert({
				message: __(`Condition added to ${window.selected_teeth.length} teeth successfully`),
				indicator: 'green'
			});
		}
	});
	d.show();
}

window.add_procedure_to_selected = function() {
	if (window.selected_teeth.length === 0) {
		frappe.msgprint('Please select teeth first');
		return;
	}
	
	let d = new frappe.ui.Dialog({
		title: __(`Add Procedure to ${window.selected_teeth.length} Selected Teeth`),
		fields: [
			{
				fieldtype: 'HTML',
				options: `<p><strong>Selected Teeth:</strong> ${window.selected_teeth.join(', ')}</p>`
			},
			{
				fieldtype: 'Link',
				fieldname: 'procedure_code',
				label: __('Procedure'),
				options: 'Dental Procedure Master',
				reqd: 1,
				change: function() {
					let procedure_code = d.get_value('procedure_code');
					if (procedure_code) {
						// Fetch procedure details and update cost fields
						frappe.call({
							method: 'frappe.client.get',
							args: {
								doctype: 'Dental Procedure Master',
								name: procedure_code
							},
							callback: function(r) {
								if (r.message) {
									let procedure = r.message;
									// Update cost fields with prefilled values
									d.set_value('standard_fee', procedure.standard_fee || 0);
									d.set_value('actual_fee', procedure.standard_fee || 0);
									d.set_value('duration_minutes', procedure.duration_minutes || 0);
									
									// Update cost info display for multiple teeth
									update_multi_cost_info_display(d, procedure, window.selected_teeth.length);
								}
							}
						});
					}
				}
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
				options: 'Planned\nScheduled\nIn Progress\nCompleted\nCancelled',
				default: 'Planned'
			},
			{
				fieldtype: 'Section Break',
				label: __('Cost Information (Per Tooth)')
			},
			{
				fieldtype: 'HTML',
				fieldname: 'cost_info',
				label: __('Cost Summary')
			},
			{
				fieldtype: 'Currency',
				fieldname: 'standard_fee',
				label: __('Standard Fee (Per Tooth)'),
				read_only: 1,
				description: __('Standard fee from procedure master')
			},
			{
				fieldtype: 'Currency',
				fieldname: 'actual_fee',
				label: __('Actual Fee (Per Tooth)'),
				description: __('You can modify this amount as needed')
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'insurance_covered',
				label: __('Insurance Covered (Per Tooth)'),
				default: 0
			},
			{
				fieldtype: 'Currency',
				fieldname: 'patient_portion',
				label: __('Patient Portion (Per Tooth)'),
				read_only: 1
			},
			{
				fieldtype: 'Section Break',
				label: __('Additional Details')
			},
			{
				fieldtype: 'Int',
				fieldname: 'duration_minutes',
				label: __('Duration (Minutes per tooth)'),
				read_only: 1
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: __('Procedure Notes')
			}
		],
		primary_action_label: __('Add to All Selected'),
		primary_action: function(values) {
			let frm = window.current_frm;
			let total_cost = (values.actual_fee || 0) * window.selected_teeth.length;
			
			window.selected_teeth.forEach(tooth_number => {
				let procedure_row = frm.add_child('tooth_procedures');
				procedure_row.tooth_number = tooth_number;
				procedure_row.procedure_code = values.procedure_code;
				procedure_row.surface = values.surface;
				procedure_row.status = values.status;
				procedure_row.notes = values.notes;
				procedure_row.planned_date = frappe.datetime.nowdate();
				procedure_row.planned_by = frappe.session.user;
				
				// Add cost information
				procedure_row.standard_fee = values.standard_fee || 0;
				procedure_row.actual_fee = values.actual_fee || 0;
				procedure_row.insurance_covered = values.insurance_covered || 0;
				procedure_row.patient_portion = (values.actual_fee || 0) - (values.insurance_covered || 0);
				procedure_row.duration_minutes = values.duration_minutes || 0;
			});
			
			frm.refresh_field('tooth_procedures');
			frm.save();
			d.hide();
			clear_selection();
			
			// Refresh the chart
			setTimeout(() => {
				create_interactive_dental_chart(frm);
			}, 500);
			
			frappe.show_alert({
				message: __(`Procedure added to ${window.selected_teeth.length} teeth - Total Cost: ${format_currency(total_cost)}`),
				indicator: 'green'
			});
		}
	});
	
	// Add change handler for insurance and actual fee to calculate patient portion
	d.fields_dict.actual_fee.$input.on('change', function() {
		calculate_patient_portion(d);
		update_multi_cost_summary(d, window.selected_teeth.length);
	});
	
	d.fields_dict.insurance_covered.$input.on('change', function() {
		calculate_patient_portion(d);
		update_multi_cost_summary(d, window.selected_teeth.length);
	});
	
	d.show();
}

function save_tooth_changes(frm, tooth_number, existing_conditions, existing_procedures, values) {
	// Update existing conditions
	existing_conditions.forEach((condition, index) => {
		let condition_doc = frm.doc.tooth_conditions.find(c => c.name === condition.name);
		if (condition_doc) {
			condition_doc.condition_code = values[`condition_code_${index}`] || condition_doc.condition_code;
			condition_doc.surface = values[`condition_surface_${index}`] || condition_doc.surface;
			condition_doc.severity = values[`condition_severity_${index}`] || condition_doc.severity;
			condition_doc.notes = values[`condition_notes_${index}`] || condition_doc.notes;
		}
	});
	
	// Update existing procedures
	existing_procedures.forEach((procedure, index) => {
		let procedure_doc = frm.doc.tooth_procedures.find(p => p.name === procedure.name);
		if (procedure_doc) {
			procedure_doc.procedure_code = values[`procedure_code_${index}`] || procedure_doc.procedure_code;
			procedure_doc.surface = values[`procedure_surface_${index}`] || procedure_doc.surface;
			procedure_doc.status = values[`procedure_status_${index}`] || procedure_doc.status;
			procedure_doc.notes = values[`procedure_notes_${index}`] || procedure_doc.notes;
			
			// Auto-set completion date if status changed to completed
			if (values[`procedure_status_${index}`] === 'Completed' && !procedure_doc.completed_date) {
				procedure_doc.completed_date = frappe.datetime.nowdate();
			}
		}
	});
	
	frm.refresh_field('tooth_conditions');
	frm.refresh_field('tooth_procedures');
	frm.save();
	
	// Refresh the chart
	setTimeout(() => {
		create_interactive_dental_chart(frm);
	}, 500);
	
	frappe.show_alert({
		message: __('Tooth changes saved successfully'),
		indicator: 'green'
	});
}

// Inline add functions (simplified for better UX) - Attach to window for global access
window.add_new_condition_inline = function() {
	add_tooth_condition_for_tooth(window.current_frm, window.current_tooth);
	window.current_tooth_dialog.hide();
}

window.add_new_procedure_inline = function() {
	add_tooth_procedure_for_tooth(window.current_frm, window.current_tooth);
	window.current_tooth_dialog.hide();
}

// Remove functions for inline editing
window.remove_condition = function(condition_name) {
	frappe.confirm(
		'Are you sure you want to remove this condition?',
		function() {
			// Find and remove the condition
			let frm = window.current_frm;
			let condition_index = frm.doc.tooth_conditions.findIndex(c => c.name === condition_name);
			if (condition_index > -1) {
				frm.doc.tooth_conditions.splice(condition_index, 1);
				frm.refresh_field('tooth_conditions');
				frm.save();
				
				// Close dialog and refresh chart
				window.current_tooth_dialog.hide();
				setTimeout(() => {
					create_interactive_dental_chart(frm);
				}, 500);
				
				frappe.show_alert({
					message: __('Condition removed successfully'),
					indicator: 'green'
				});
			}
		}
	);
}

window.remove_procedure = function(procedure_name) {
	frappe.confirm(
		'Are you sure you want to remove this procedure?',
		function() {
			// Find and remove the procedure
			let frm = window.current_frm;
			let procedure_index = frm.doc.tooth_procedures.findIndex(p => p.name === procedure_name);
			if (procedure_index > -1) {
				frm.doc.tooth_procedures.splice(procedure_index, 1);
				frm.refresh_field('tooth_procedures');
				frm.save();
				
				// Close dialog and refresh chart
				window.current_tooth_dialog.hide();
				setTimeout(() => {
					create_interactive_dental_chart(frm);
				}, 500);
				
				frappe.show_alert({
					message: __('Procedure removed successfully'),
					indicator: 'green'
				});
			}
		}
	);
}

function show_tooth_details(frm, tooth_number, conditions, procedures) {
	let details_html = `
		<div style="padding: 10px;">
			<h4>Tooth ${tooth_number} - Detailed Information</h4>
	`;
	
	if (conditions.length > 0) {
		details_html += '<h5 style="color: #dc3545; margin-top: 20px;">🦷 Conditions</h5>';
		conditions.forEach(condition => {
			details_html += `
				<div style="border: 1px solid #fff3cd; background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px;">
					<strong>${condition.condition_code}</strong> - ${condition.surface}<br>
					<small>Identified: ${condition.date_identified} by ${condition.identified_by}</small>
					${condition.notes ? `<br><em>${condition.notes}</em>` : ''}
				</div>
			`;
		});
	}
	
	if (procedures.length > 0) {
		details_html += '<h5 style="color: #007bff; margin-top: 20px;">🔧 Procedures</h5>';
		procedures.forEach(procedure => {
			let status_color = procedure.status === 'Completed' ? '#d4edda' : 
							  procedure.status === 'In Progress' ? '#d1ecf1' : '#f8f9fa';
			details_html += `
				<div style="border: 1px solid ${status_color}; background: ${status_color}; padding: 10px; margin: 5px 0; border-radius: 3px;">
					<strong>${procedure.procedure_code}</strong> - ${procedure.surface} 
					<span style="float: right; font-weight: bold;">${procedure.status}</span><br>
					<small>Planned: ${procedure.planned_date} by ${procedure.planned_by}</small>
					${procedure.notes ? `<br><em>${procedure.notes}</em>` : ''}
				</div>
			`;
		});
	}
	
	details_html += '</div>';
	
	frappe.msgprint({
		title: __('Tooth Details'),
		message: details_html,
		wide: true
	});
}

function add_tooth_condition(frm) {
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
}

function add_tooth_procedure(frm) {
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
}

function show_chart_visualization(frm) {
	frappe.call({
		method: 'dentcharts.dentcharts.doctype.dental_chart.dental_chart.get_chart_data',
		args: {
			chart_name: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				let chart_data = r.message;
				let html = build_chart_html(chart_data);
				
				frappe.msgprint({
					title: __('Dental Chart Visualization'),
					message: html,
					wide: true
				});
			}
		}
	});
}

function build_chart_html(chart_data) {
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
			let status_color = get_tooth_status_color(tooth.data.status);
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
			let status_color = get_tooth_status_color(tooth.data.status);
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
}

function get_tooth_status_color(status) {
	const colors = {
		'healthy': '#f8f9fa',
		'has_condition': '#fff3cd',
		'in_treatment': '#d1ecf1',
		'treated': '#d4edda'
	};
	return colors[status] || '#f8f9fa';
}

function record_new_visit(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Record New Visit'),
		fields: [
			{
				fieldtype: 'HTML',
				options: `<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
					<h5 style="margin: 0 0 10px 0;">📅 New Visit Entry</h5>
					<p style="margin: 0;">Record today's visit details. This will be added to the patient's master dental chart.</p>
				</div>`
			},
			{
				fieldtype: 'Date',
				fieldname: 'visit_date',
				label: __('Visit Date'),
				default: frappe.datetime.nowdate(),
				reqd: 1
			},
			{
				fieldtype: 'Link',
				fieldname: 'dentist',
				label: __('Examining Dentist'),
				options: 'Healthcare Practitioner',
				default: frm.doc.dentist,
				reqd: 1
			},
			{
				fieldtype: 'Select',
				fieldname: 'visit_type',
				label: __('Visit Type'),
				options: 'Regular Checkup\nEmergency\nFollow-up\nConsultation\nTreatment\nCleaning',
				default: 'Regular Checkup',
				reqd: 1
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'chief_complaint',
				label: __('Chief Complaint')
			},
			{
				fieldtype: 'Text',
				fieldname: 'visit_notes',
				label: __('Visit Notes')
			}
		],
		primary_action_label: __('Start Recording'),
		primary_action: function(values) {
			// Update chart with visit information
			frm.set_value('chart_date', values.visit_date);
			frm.set_value('dentist', values.dentist);
			
			// Add visit notes to existing notes
			let current_notes = frm.doc.notes || '';
			let visit_entry = `\n\n--- VISIT: ${values.visit_date} (${values.visit_type}) ---\n`;
			visit_entry += `Dentist: ${values.dentist}\n`;
			if (values.chief_complaint) {
				visit_entry += `Chief Complaint: ${values.chief_complaint}\n`;
			}
			if (values.visit_notes) {
				visit_entry += `Notes: ${values.visit_notes}\n`;
			}
			visit_entry += `--- End of Visit ---\n`;
			
			frm.set_value('notes', current_notes + visit_entry);
			frm.save();
			
			d.hide();
			frappe.show_alert({
				message: __('Visit recorded successfully. Now click on teeth to add conditions/procedures.'),
				indicator: 'green'
			});
		}
	});
	d.show();
}

function show_dental_history(frm) {
	// Create a comprehensive history view
	let conditions_by_date = {};
	let procedures_by_date = {};
	
	// Group conditions by date
	(frm.doc.tooth_conditions || []).forEach(condition => {
		let date = condition.date_identified || 'Unknown Date';
		if (!conditions_by_date[date]) conditions_by_date[date] = [];
		conditions_by_date[date].push(condition);
	});
	
	// Group procedures by date
	(frm.doc.tooth_procedures || []).forEach(procedure => {
		let date = procedure.planned_date || 'Unknown Date';
		if (!procedures_by_date[date]) procedures_by_date[date] = [];
		procedures_by_date[date].push(procedure);
	});
	
	// Get all unique dates and sort them
	let all_dates = [...new Set([...Object.keys(conditions_by_date), ...Object.keys(procedures_by_date)])];
	all_dates.sort((a, b) => new Date(b) - new Date(a)); // Most recent first
	
	let history_html = `
		<div style="padding: 20px;">
			<h3>🦷 Complete Dental History - ${frm.doc.patient_name}</h3>
			<p style="color: #6c757d; margin-bottom: 20px;">Master Chart Created: ${frappe.datetime.str_to_user(frm.doc.creation)}</p>
	`;
	
	if (all_dates.length === 0) {
		history_html += '<p style="text-align: center; color: #6c757d; font-style: italic;">No dental procedures or conditions recorded yet.</p>';
	} else {
		all_dates.forEach(date => {
			if (date !== 'Unknown Date') {
				history_html += `
					<div style="border-left: 4px solid #007bff; padding-left: 15px; margin-bottom: 20px;">
						<h5 style="color: #495057; margin-bottom: 10px;">📅 ${frappe.datetime.str_to_user(date)}</h5>
				`;
				
				// Show conditions for this date
				if (conditions_by_date[date]) {
					history_html += '<div style="margin-bottom: 10px;"><strong>🦷 Conditions Identified:</strong><ul style="margin: 5px 0 0 20px;">';
					conditions_by_date[date].forEach(condition => {
						history_html += `
							<li style="margin: 2px 0;">
								<strong>Tooth ${condition.tooth_number}:</strong> ${condition.condition_code} (${condition.surface})
								${condition.severity ? ` - ${condition.severity}` : ''}
								${condition.notes ? `<br><small style="color: #6c757d;">${condition.notes}</small>` : ''}
							</li>
						`;
					});
					history_html += '</ul></div>';
				}
				
				// Show procedures for this date
				if (procedures_by_date[date]) {
					history_html += '<div style="margin-bottom: 10px;"><strong>🔧 Procedures:</strong><ul style="margin: 5px 0 0 20px;">';
					procedures_by_date[date].forEach(procedure => {
						let status_color = procedure.status === 'Completed' ? '#28a745' : 
										  procedure.status === 'In Progress' ? '#007bff' : '#6c757d';
						history_html += `
							<li style="margin: 2px 0;">
								<strong>Tooth ${procedure.tooth_number}:</strong> ${procedure.procedure_code} (${procedure.surface})
								<span style="color: ${status_color}; font-weight: bold;"> - ${procedure.status}</span>
								${procedure.notes ? `<br><small style="color: #6c757d;">${procedure.notes}</small>` : ''}
							</li>
						`;
					});
					history_html += '</ul></div>';
				}
				
				history_html += '</div>';
			}
		});
	}
	
	// Add summary statistics
	let total_conditions = (frm.doc.tooth_conditions || []).length;
	let total_procedures = (frm.doc.tooth_procedures || []).length;
	let completed_procedures = (frm.doc.tooth_procedures || []).filter(p => p.status === 'Completed').length;
	let pending_procedures = total_procedures - completed_procedures;
	
	history_html += `
		<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
			<h5>📊 Summary Statistics</h5>
			<div style="display: flex; gap: 20px; flex-wrap: wrap;">
				<div><strong>Total Conditions:</strong> ${total_conditions}</div>
				<div><strong>Total Procedures:</strong> ${total_procedures}</div>
				<div><strong>Completed:</strong> ${completed_procedures}</div>
				<div><strong>Pending:</strong> ${pending_procedures}</div>
			</div>
		</div>
	</div>`;
	
	frappe.msgprint({
		title: __('Dental History'),
		message: history_html,
		wide: true
	});
}

function refresh_dental_chart(frm) {
	// Clear existing chart completely
	$('.dental-chart-container').remove();
	
	// Update dashboard header with new dentition type
	frm.dashboard.clear_headline();
	if (frm.doc.chart_type === 'Master Chart') {
		frm.dashboard.set_headline(`
			<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
				<h4 style="margin: 0 0 5px 0;">🦷 Master Dental Chart - ${frm.doc.patient_name}</h4>
				<p style="margin: 0; opacity: 0.9;">Lifetime dental record • Last updated: ${frappe.datetime.str_to_user(frm.doc.modified)}</p>
				<div style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">
					<strong>📋 Current Dentition: ${frm.doc.dentition_type || 'Permanent'}</strong>
					<span style="margin-left: 15px; opacity: 0.8;">${get_dentition_description(frm.doc.dentition_type)}</span>
				</div>
			</div>
		`);
	}
	
	// Create new chart
	create_interactive_dental_chart(frm);
}

function update_dentition_info_display(frm) {
	if (!frm.doc.dentition_type) return;
	
	let html = '';
	let icon = '';
	let color = '';
	let description = '';
	
	switch(frm.doc.dentition_type) {
		case 'Permanent':
			icon = '🦷';
			color = '#007bff';
			description = 'Adult teeth (32 teeth) • FDI numbering system (11-48)';
			break;
		case 'Primary':
			icon = '👶';
			color = '#28a745';
			description = 'Baby teeth (20 teeth) • Palmer notation (UR-A, UL-B, etc.)';
			break;
		case 'Mixed':
			icon = '🔄';
			color = '#fd7e14';
			description = 'Both permanent and primary teeth • Transitional dentition';
			break;
	}
	
	html = `
		<div style="background: linear-gradient(135deg, ${color}, ${adjustColor(color, -20)}); 
					color: white; padding: 12px; border-radius: 6px; margin: 8px 0; 
					box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
			<div style="display: flex; align-items: center; gap: 10px;">
				<span style="font-size: 24px;">${icon}</span>
				<div style="flex: 1;">
					<strong style="font-size: 16px;">${frm.doc.dentition_type} Dentition Selected</strong>
					<div style="font-size: 13px; opacity: 0.9; margin-top: 3px;">${description}</div>
				</div>
				<div style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; font-size: 12px;">
					Chart Type: ${frm.doc.chart_type || 'Master Chart'}
				</div>
			</div>
		</div>
	`;
	
	frm.get_field('dentition_info').html(html);
}

function adjustColor(color, amount) {
	const usePound = color[0] === "#";
	const col = usePound ? color.slice(1) : color;
	const num = parseInt(col, 16);
	let r = (num >> 16) + amount;
	let g = (num >> 8 & 0x00FF) + amount;
	let b = (num & 0x0000FF) + amount;
	r = r > 255 ? 255 : r < 0 ? 0 : r;
	g = g > 255 ? 255 : g < 0 ? 0 : g;
	b = b > 255 ? 255 : b < 0 ? 0 : b;
	return (usePound ? "#" : "") + String("000000" + (r << 16 | g << 8 | b).toString(16)).slice(-6);
}

// Cost calculation and display helper functions
function calculate_patient_portion(dialog) {
	let actual_fee = dialog.get_value('actual_fee') || 0;
	let insurance_covered = dialog.get_value('insurance_covered') || 0;
	let patient_portion = actual_fee - insurance_covered;
	dialog.set_value('patient_portion', patient_portion);
}

function update_cost_info_display(dialog, procedure) {
	let html = `
		<div style="background: linear-gradient(135deg, #17a2b8, #138496); color: white; padding: 12px; border-radius: 6px; margin: 8px 0;">
			<div style="display: flex; align-items: center; gap: 10px;">
				<span style="font-size: 20px;">💰</span>
				<div style="flex: 1;">
					<strong style="font-size: 14px;">${procedure.procedure_name}</strong>
					<div style="font-size: 12px; opacity: 0.9; margin-top: 2px;">
						Standard Fee: ${format_currency(procedure.standard_fee || 0)} • 
						Duration: ${procedure.duration_minutes || 0} mins
					</div>
				</div>
			</div>
		</div>
	`;
	
	let cost_field = dialog.get_field('cost_info');
	if (cost_field) {
		cost_field.$wrapper.html(html);
	}
}

function update_multi_cost_info_display(dialog, procedure, teeth_count) {
	let standard_fee = procedure.standard_fee || 0;
	let total_standard = standard_fee * teeth_count;
	
	let html = `
		<div style="background: linear-gradient(135deg, #fd7e14, #e55a00); color: white; padding: 12px; border-radius: 6px; margin: 8px 0;">
			<div style="display: flex; align-items: center; gap: 10px;">
				<span style="font-size: 20px;">💰</span>
				<div style="flex: 1;">
					<strong style="font-size: 14px;">${procedure.procedure_name}</strong>
					<div style="font-size: 12px; opacity: 0.9; margin-top: 2px;">
						${teeth_count} teeth × ${format_currency(standard_fee)} = ${format_currency(total_standard)} (Standard Total)
					</div>
					<div style="font-size: 12px; opacity: 0.9; margin-top: 2px;">
						Duration per tooth: ${procedure.duration_minutes || 0} mins
					</div>
				</div>
			</div>
		</div>
	`;
	
	let cost_field = dialog.get_field('cost_info');
	if (cost_field) {
		cost_field.$wrapper.html(html);
	}
}

function update_multi_cost_summary(dialog, teeth_count) {
	let actual_fee = dialog.get_value('actual_fee') || 0;
	let insurance_covered = dialog.get_value('insurance_covered') || 0;
	let patient_portion = actual_fee - insurance_covered;
	
	let total_actual = actual_fee * teeth_count;
	let total_insurance = insurance_covered * teeth_count;
	let total_patient = patient_portion * teeth_count;
	
	// Update the cost info display with totals
	let existing_html = dialog.get_field('cost_info').$wrapper.html();
	let summary_html = `
		${existing_html}
		<div style="background: rgba(0,0,0,0.1); padding: 8px; border-radius: 4px; margin-top: 8px;">
			<div style="font-size: 12px; opacity: 0.9;">
				<strong>Total Summary:</strong><br>
				Actual Total: ${format_currency(total_actual)} | 
				Insurance Total: ${format_currency(total_insurance)} | 
				Patient Total: ${format_currency(total_patient)}
			</div>
		</div>
	`;
	
	dialog.get_field('cost_info').$wrapper.html(summary_html);
} 