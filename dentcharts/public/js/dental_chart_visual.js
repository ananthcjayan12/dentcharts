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
			
			frm.add_custom_button(__('Add Manual Activity'), function() {
				add_manual_activity(frm);
			}, __('Activity History'));
			
			frm.add_custom_button(__('Export Activity Log'), function() {
				export_activity_log(frm);
			}, __('Activity History'));
			
			frm.add_custom_button(__('Clear Old Activities'), function() {
				clear_old_activities(frm);
			}, __('Activity History'));
			
			frm.add_custom_button(__('Add General Procedure'), function() {
				add_general_procedure(frm);
			}, __('Add Treatments'));
			
			// Add Generate Invoice button if any procedures exist (planned/in-progress/completed)
			if ((frm.doc.tooth_procedures || []).length) {
				frm.add_custom_button(__('Generate Invoice'), function() {
					show_invoice_generation_dialog(frm);
				}, __('Actions'));
			}
		}
		
		// Show dentition type info
		if (frm.doc.dentition_type) {
			frm.set_df_property('dentition_type', 'description', get_dentition_description(frm.doc.dentition_type));
			update_dentition_info_display(frm);
		}
		
		// Update activity timeline
		if (!frm.is_new()) {
			update_activity_timeline(frm);
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
	},
	
	// Handle activity table changes
	chart_activities_add: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// Set default values for new manual activities
		row.activity_datetime = frappe.datetime.now();
		row.performed_by = frappe.session.user;
		row.activity_type = 'Chart Updated';
		frm.refresh_field('chart_activities');
	},
	
	chart_activities_on_form_rendered: function(frm, cdt, cdn) {
		// Add custom styling to activity rows
		let row = locals[cdt][cdn];
		let grid_row = frm.fields_dict.chart_activities.grid.get_row(cdn);
		
		if (grid_row && row.activity_type) {
			let color = get_activity_color(row.activity_type);
			grid_row.$wrapper.find('.grid-row').css({
				'border-left': `4px solid ${color}`,
				'background': `${color}08`,
				'border-radius': '4px',
				'margin': '2px 0'
			});
		}
	}
	, // add comma to separate new handlers
	// Client-side logging when adding a tooth condition
	tooth_conditions_add: function(frm, cdt, cdn) {
		let cond = locals[cdt][cdn];
		let act = frm.add_child('chart_activities');
		act.activity_type = 'Condition Added';
		act.activity_description = __('Added condition {0} to tooth {1}', [cond.condition_code, cond.tooth_number]);
		act.tooth_number = cond.tooth_number;
		act.condition_code = cond.condition_code;
		act.new_value = `${cond.condition_code} on ${cond.surface}`;
		act.activity_datetime = frappe.datetime.now();
		act.performed_by = frappe.session.user;
		frm.refresh_field('chart_activities');
		update_activity_timeline(frm);
	},
	// Client-side logging when adding a tooth procedure
	tooth_procedures_add: function(frm, cdt, cdn) {
		let proc = locals[cdt][cdn];
		let cost = proc.actual_fee || proc.standard_fee || 0;
		let act = frm.add_child('chart_activities');
		act.activity_type = 'Procedure Added';
		act.activity_description = __('Added procedure {0} to tooth {1}', [proc.procedure_code, proc.tooth_number]);
		act.tooth_number = proc.tooth_number;
		act.procedure_code = proc.procedure_code;
		act.new_value = `${proc.procedure_code} (${proc.status}) on ${proc.surface}`;
		act.cost_impact = cost;
		act.activity_datetime = frappe.datetime.now();
		act.performed_by = frappe.session.user;
		frm.refresh_field('chart_activities');
		update_activity_timeline(frm);
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
				// Render invoice cards section for this patient
				render_invoice_section(frm);
				// Render payment cards section for this patient
				render_payment_section(frm);
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
			</div>`;

	// Add general procedures section if any exist
	if (chart_data.general_procedures && chart_data.general_procedures.length > 0) {
		html += `
			<div style="margin-top: 20px; padding: 15px; background: linear-gradient(135deg, #e8f4fd, #d1ecf1); border-radius: 8px;">
				<h5 style="margin: 0 0 15px 0; color: #0c5460;">🔧 General Procedures</h5>
				<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;">`;
		
		chart_data.general_procedures.forEach((procedure, index) => {
			let status_color = procedure.status === 'Completed' ? '#28a745' : 
							  procedure.status === 'In Progress' ? '#17a2b8' : '#ffc107';
			html += `
				<div class="general-procedure-card" data-procedure-code="${procedure.code}" data-procedure-index="${index}" 
					 style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid ${status_color}; cursor: pointer; transition: all 0.2s ease;"
					 onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)';"
					 onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';"
					 onclick="show_general_procedure_dialog('${procedure.code}', ${index})"
					 title="Click to edit this general procedure">
					<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
						<strong style="color: #333;">${procedure.code}</strong>
						<span style="background: ${status_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
							${procedure.status}
						</span>
					</div>
					<div style="font-size: 13px; color: #666; margin-bottom: 5px;">
						<strong>Surface:</strong> ${procedure.surface}
					</div>
					<div style="font-size: 13px; color: #666; margin-bottom: 5px;">
						<strong>Date:</strong> ${frappe.datetime.str_to_user(procedure.date)}
					</div>
					${procedure.actual_fee ? `<div style="font-size: 13px; color: #28a745; font-weight: bold;">
						<strong>Fee:</strong> ${format_currency(procedure.actual_fee)}
					</div>` : ''}
					${procedure.notes ? `<div style="font-size: 12px; color: #666; margin-top: 8px; font-style: italic;">
						${procedure.notes}
					</div>` : ''}
					<div style="font-size: 11px; color: #999; margin-top: 8px; text-align: center;">
						🖱️ Click to edit
					</div>
				</div>
			`;
		});
		
		html += `
				</div>
			</div>`;
	}
	
	html += `
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
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
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
				fieldtype: 'Date',
				fieldname: `condition_date_${index}`,
				label: 'Date Identified',
				default: condition.date_identified
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
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
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
				fieldtype: 'Date',
				fieldname: `procedure_planned_date_${index}`,
				label: 'Planned Date',
				default: procedure.planned_date
			});
			dialog_fields.push({
				fieldtype: 'Date',
				fieldname: `procedure_status_date_${index}`,
				label: 'Status Change Date',
				default: procedure.completed_date || procedure.planned_date || frappe.datetime.get_today(),
				description: 'Date when this status change occurred'
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
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
				default: 'Whole Tooth'
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: __('Notes')
			},
			{
				fieldtype: 'Date',
				fieldname: 'date_identified',
				label: __('Date'),
				default: frappe.datetime.get_today(),
				reqd: 1
			}
		],
		primary_action_label: __('Add Condition'),
		primary_action: function(values) {
			let condition_row = frm.add_child('tooth_conditions');
			condition_row.tooth_number = selected_tooth;
			condition_row.tooth_name = selected_tooth;
			condition_row.condition_code = values.condition_code;
			condition_row.surface = values.surface;
			condition_row.notes = values.notes;
			condition_row.date_identified = values.date_identified;
			condition_row.identified_by = frappe.session.user;
			
			frm.refresh_field('tooth_conditions');
			// Immediately log this addition client-side
			let act_cond = frm.add_child('chart_activities');
			act_cond.activity_type = 'Condition Added';
			act_cond.activity_description = __('Added condition {0} to tooth {1}', [values.condition_code, selected_tooth]);
			act_cond.tooth_number = selected_tooth;
			act_cond.condition_code = values.condition_code;
			act_cond.new_value = `${values.condition_code} on ${values.surface}`;
			act_cond.activity_datetime = values.date_identified + ' 00:00:00';
			act_cond.performed_by = frappe.session.user;
			frm.refresh_field('chart_activities');
			update_activity_timeline(frm);
			
			// Save and reload to pick up server-appended activities, then refresh UI
			frm.save().then(() => {
				frm.reload_doc().then(() => {
					create_interactive_dental_chart(frm);
					update_activity_timeline(frm);
				});
			});

			d.hide();
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
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
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
			},
			{
				fieldtype: 'Date',
				fieldname: 'planned_date',
				label: __('Date'),
				default: frappe.datetime.get_today(),
				reqd: 1
			}
		],
		primary_action_label: __('Add Procedure'),
		primary_action: function(values) {
			let procedure_row = frm.add_child('tooth_procedures');
			procedure_row.tooth_number = selected_tooth;
			procedure_row.tooth_name = selected_tooth;
			procedure_row.procedure_code = values.procedure_code;
			procedure_row.surface = values.surface;
			procedure_row.status = values.status;
			procedure_row.notes = values.notes;
			procedure_row.planned_date = values.planned_date;
			procedure_row.planned_by = frappe.session.user;
			
			// Add cost information
			procedure_row.standard_fee = values.standard_fee || 0;
			procedure_row.actual_fee = values.actual_fee || 0;
			procedure_row.insurance_covered = values.insurance_covered || 0;
			procedure_row.patient_portion = (values.actual_fee || 0) - (values.insurance_covered || 0);
			procedure_row.duration_minutes = values.duration_minutes || 0;
			
			frm.refresh_field('tooth_procedures');
			// Immediately log this addition client-side
			let act_proc = frm.add_child('chart_activities');
			let cost = values.actual_fee || values.standard_fee || 0;
			act_proc.activity_type = 'Procedure Added';
			act_proc.activity_description = __('Added procedure {0} to tooth {1}', [values.procedure_code, selected_tooth]);
			act_proc.tooth_number = selected_tooth;
			act_proc.procedure_code = values.procedure_code;
			act_proc.new_value = `${values.procedure_code} (${values.status}) on ${values.surface}`;
			act_proc.cost_impact = cost;
			act_proc.activity_datetime = values.planned_date + ' 00:00:00';
			act_proc.performed_by = frappe.session.user;
			frm.refresh_field('chart_activities');
			update_activity_timeline(frm);
			
			// Save and reload to pick up server-appended activities, then refresh UI
			frm.save().then(() => {
				frm.reload_doc().then(() => {
					frappe.show_alert({
						message: __(`Procedure added: ${values.procedure_code} - Fee: ${format_currency(values.actual_fee || 0)}`),
						indicator: 'green'
					});
					create_interactive_dental_chart(frm);
					update_activity_timeline(frm);
				});
			});

			d.hide();
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
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
				default: 'Whole Tooth'
			},
			{
				fieldtype: 'Select',
				fieldname: 'severity',
				label: __('Severity'),
				options: '\nMild\nModerate\nSevere'
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Date',
				fieldname: 'date_identified',
				label: __('Date'),
				default: frappe.datetime.get_today(),
				reqd: 1
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
				condition_row.tooth_name = tooth_number;
				condition_row.condition_code = values.condition_code;
				condition_row.surface = values.surface;
				condition_row.severity = values.severity;
				condition_row.notes = values.notes;
				condition_row.date_identified = values.date_identified;
				condition_row.identified_by = frappe.session.user;
			});
			
			frm.refresh_field('tooth_conditions');
			// Bulk condition activity log
			let condCode = values.condition_code;
			let condSurf = values.surface;
			let condCount = window.selected_teeth.length;
			let condList = window.selected_teeth.join(', ');
			let actCond = frm.add_child('chart_activities');
			actCond.activity_type = 'Condition Added';
			actCond.activity_description = __('Added condition {0} to {1} teeth: {2}', [condCode, condCount, condList]);
			actCond.tooth_number = `Multiple (${condCount})`;
			actCond.condition_code = condCode;
			actCond.new_value = `${condCode} on ${condSurf}`;
			actCond.activity_datetime = values.date_identified + ' 00:00:00';
			actCond.performed_by = frappe.session.user;
			frm.refresh_field('chart_activities');
			update_activity_timeline(frm);
			
			// Save and reload to pick up server-appended activities
			frm.save().then(() => {
				frm.reload_doc().then(() => {
					create_interactive_dental_chart(frm);
					update_activity_timeline(frm);
				});
			});
			d.hide();
			clear_selection();
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
				options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
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
			},
			{
				fieldtype: 'Date',
				fieldname: 'planned_date',
				label: __('Date'),
				default: frappe.datetime.get_today(),
				reqd: 1
			}
		],
		primary_action_label: __('Add to All Selected'),
		primary_action: function(values) {
			let frm = window.current_frm;
			let total_cost = (values.actual_fee || 0) * window.selected_teeth.length;
			
			window.selected_teeth.forEach(tooth_number => {
				let procedure_row = frm.add_child('tooth_procedures');
				procedure_row.tooth_number = tooth_number;
				procedure_row.tooth_name = tooth_number;
				procedure_row.procedure_code = values.procedure_code;
				procedure_row.surface = values.surface;
				procedure_row.status = values.status;
				procedure_row.notes = values.notes;
				procedure_row.planned_date = values.planned_date;
				procedure_row.planned_by = frappe.session.user;
				procedure_row.standard_fee = values.standard_fee || 0;
				procedure_row.actual_fee = values.actual_fee || 0;
				procedure_row.insurance_covered = values.insurance_covered || 0;
				procedure_row.patient_portion = (values.actual_fee || 0) - (values.insurance_covered || 0);
				procedure_row.duration_minutes = values.duration_minutes || 0;
			});
			
			frm.refresh_field('tooth_procedures');
			// Bulk procedure activity log
			let procCode = values.procedure_code;
			let procSurf = values.surface;
			let procStatus = values.status;
			let procCount = window.selected_teeth.length;
			let procList = window.selected_teeth.join(', ');
			let procTotalCost = (values.actual_fee || 0) * procCount;
			let actProc = frm.add_child('chart_activities');
			actProc.activity_type = 'Procedure Added';
			actProc.activity_description = __('Added procedure {0} to {1} teeth: {2}', [procCode, procCount, procList]);
			actProc.tooth_number = `Multiple (${procCount})`;
			actProc.procedure_code = procCode;
			actProc.new_value = `${procCode} (${procStatus}) on ${procSurf}`;
			actProc.cost_impact = procTotalCost;
			actProc.activity_datetime = values.planned_date + ' 00:00:00';
			actProc.performed_by = frappe.session.user;
			frm.refresh_field('chart_activities');
			update_activity_timeline(frm);
			
			// Save and reload to pick up server-appended activities
			frm.save().then(() => {
				frm.reload_doc().then(() => {
					frappe.show_alert({ message: __(`Procedure added to ${window.selected_teeth.length} teeth - Total Cost: ${format_currency(total_cost)}`), indicator: 'green' });
					create_interactive_dental_chart(frm);
					update_activity_timeline(frm);
				});
			});
			d.hide();
			clear_selection();
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

// Function to show general procedure edit dialog
window.show_general_procedure_dialog = function(procedure_code, procedure_index) {
	let frm = window.current_frm;
	
	// Find the general procedure in the tooth_procedures table
	let general_procedures = frm.doc.tooth_procedures.filter(proc => proc.tooth_number === 'General');
	let procedure = general_procedures[procedure_index];
	
	if (!procedure) {
		frappe.msgprint('Procedure not found');
		return;
	}
	
	let dialog_fields = [
		{
			fieldtype: 'HTML',
			options: `
				<div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<h4 style="margin: 0 0 8px 0;">🔧 General Procedure Management</h4>
					<p style="margin: 0; opacity: 0.9;">Edit details for general procedure: <strong>${procedure.procedure_code}</strong></p>
				</div>
			`
		},
		{
			fieldtype: 'Section Break',
			label: '📋 Procedure Details'
		},
		{
			fieldtype: 'Link',
			fieldname: 'procedure_code',
			label: 'Procedure',
			options: 'Dental Procedure Master',
			default: procedure.procedure_code,
			read_only: 1
		},
		{
			fieldtype: 'Select',
			fieldname: 'status',
			label: 'Status',
			options: 'Planned\nIn Progress\nCompleted\nCancelled',
			default: procedure.status,
			reqd: 1
		},
		{
			fieldtype: 'Column Break'
		},
		{
			fieldtype: 'Date',
			fieldname: 'planned_date',
			label: 'Planned Date',
			default: procedure.planned_date
		},
		{
			fieldtype: 'Date',
			fieldname: 'status_change_date',
			label: 'Status Change Date',
			default: procedure.completed_date || procedure.planned_date || frappe.datetime.get_today(),
			description: 'Date when this status change occurred'
		},
		{
			fieldtype: 'Section Break',
			label: '💰 Cost Information'
		},
		{
			fieldtype: 'Currency',
			fieldname: 'standard_fee',
			label: 'Standard Fee',
			default: procedure.standard_fee,
			read_only: 1
		},
		{
			fieldtype: 'Currency',
			fieldname: 'actual_fee',
			label: 'Actual Fee',
			default: procedure.actual_fee
		},
		{
			fieldtype: 'Column Break'
		},
		{
			fieldtype: 'Currency',
			fieldname: 'insurance_covered',
			label: 'Insurance Covered',
			default: procedure.insurance_covered
		},
		{
			fieldtype: 'Currency',
			fieldname: 'patient_portion',
			label: 'Patient Portion',
			default: procedure.patient_portion,
			read_only: 1
		},
		{
			fieldtype: 'Section Break',
			label: '📝 Notes'
		},
		{
			fieldtype: 'Small Text',
			fieldname: 'notes',
			label: 'Notes',
			default: procedure.notes
		},
		{
			fieldtype: 'Small Text',
			fieldname: 'treatment_plan_notes',
			label: 'Treatment Plan Notes',
			default: procedure.treatment_plan_notes
		}
	];
	
	let d = new frappe.ui.Dialog({
		title: __('General Procedure - ') + procedure.procedure_code,
		fields: dialog_fields,
		size: 'large',
		primary_action_label: __('Save Changes'),
		primary_action: function(values) {
			save_general_procedure_changes(frm, procedure, values);
			d.hide();
		},
		secondary_action_label: __('Remove Procedure'),
		secondary_action: function() {
			frappe.confirm(
				'Are you sure you want to remove this general procedure?',
				function() {
					remove_general_procedure(frm, procedure);
					d.hide();
				}
			);
		}
	});
	
	// Add change handlers for cost calculation
	d.fields_dict.actual_fee.$input.on('change', function() {
		let actual_fee = parseFloat(d.get_value('actual_fee')) || 0;
		let insurance_covered = parseFloat(d.get_value('insurance_covered')) || 0;
		let patient_portion = actual_fee - insurance_covered;
		d.set_value('patient_portion', patient_portion);
	});
	
	d.fields_dict.insurance_covered.$input.on('change', function() {
		let actual_fee = parseFloat(d.get_value('actual_fee')) || 0;
		let insurance_covered = parseFloat(d.get_value('insurance_covered')) || 0;
		let patient_portion = actual_fee - insurance_covered;
		d.set_value('patient_portion', patient_portion);
	});
	
	d.show();
}

function save_general_procedure_changes(frm, procedure, values) {
	// Set multiple flags to prevent duplicate logging from various sources
	window.saving_from_enhanced_dialog = true;
	frm._saving_from_enhanced_dialog = true;
	window._bulk_saving = true;
	frm._bulk_saving = true;
	
	// Also set a flag to prevent server-side automatic logging
	frm._skip_server_activity_logging = true;
	
	const oldStatus = procedure.status;
	const newStatus = values.status;
	const statusChangeDate = values.status_change_date || frappe.datetime.get_today();
	
	// Update the procedure using frappe.model.set_value for reliable persistence
	frappe.model.set_value('Tooth Procedure', procedure.name, 'status', newStatus);
	frappe.model.set_value('Tooth Procedure', procedure.name, 'planned_date', values.planned_date);
	frappe.model.set_value('Tooth Procedure', procedure.name, 'actual_fee', values.actual_fee);
	frappe.model.set_value('Tooth Procedure', procedure.name, 'insurance_covered', values.insurance_covered);
	frappe.model.set_value('Tooth Procedure', procedure.name, 'patient_portion', values.patient_portion);
	frappe.model.set_value('Tooth Procedure', procedure.name, 'notes', values.notes);
	frappe.model.set_value('Tooth Procedure', procedure.name, 'treatment_plan_notes', values.treatment_plan_notes);
	
	// Handle status change with manual activity logging
	if (oldStatus !== newStatus) {
		// Log the status change manually with user-provided status change date
		let act = frm.add_child('chart_activities');
		act.activity_type = 'Procedure Status Changed';
		act.activity_description = __('Changed status of general procedure {0} to {1}', [procedure.procedure_code, newStatus]);
		act.tooth_number = 'General';
		act.procedure_code = procedure.procedure_code;
		act.new_value = `Status: ${newStatus}`;
		act.activity_datetime = statusChangeDate + ' ' + frappe.datetime.now_time();
		act.performed_by = frappe.session.user;
		
		// Update completed_date only if status is completed
		if (newStatus === 'Completed') {
			frappe.model.set_value('Tooth Procedure', procedure.name, 'completed_date', statusChangeDate);
		} else {
			// Clear completed date if status is not completed
			frappe.model.set_value('Tooth Procedure', procedure.name, 'completed_date', '');
		}
	}
	
	// Update fields and save
	frm.refresh_field('tooth_procedures');
	frm.refresh_field('chart_activities');
	
	// Clear all flags after a short delay to allow all events to process
	setTimeout(() => {
		window.saving_from_enhanced_dialog = false;
		frm._saving_from_enhanced_dialog = false;
		window._bulk_saving = false;
		frm._bulk_saving = false;
		frm._skip_server_activity_logging = false;
	}, 3000);
	
	// Set a flag to prevent server-side duplicate logging
	frm.doc._skip_activity_logging = 1;
	
	// Save the document
	frm.save().then(() => {
		// Clear the flag after saving
		frm.doc._skip_activity_logging = 0;
		
		// Refresh the UI components without reloading
		create_interactive_dental_chart(frm);
		update_activity_timeline(frm);
		frappe.show_alert({
			message: __('General procedure updated successfully'),
			indicator: 'green'
		});
	});
}

function remove_general_procedure(frm, procedure) {
	// Find and remove the procedure from the child table
	let procedures_to_remove = [];
	frm.doc.tooth_procedures.forEach((proc, index) => {
		if (proc.name === procedure.name) {
			procedures_to_remove.push(index);
		}
	});
	
	// Remove in reverse order to maintain indices
	procedures_to_remove.reverse().forEach(index => {
		frm.get_field('tooth_procedures').grid.grid_rows[index].remove();
	});
	
	frm.refresh_field('tooth_procedures');
	frm.save().then(() => {
		create_interactive_dental_chart(frm);
		update_activity_timeline(frm);
		frappe.show_alert({
			message: __('General procedure removed successfully'),
			indicator: 'green'
		});
	});
}

// Function to show invoice generation dialog with procedure selection
function show_invoice_generation_dialog(frm) {
	// Get all non-cancelled procedures
	let available_procedures = frm.doc.tooth_procedures.filter(proc => proc.status !== 'Cancelled');
	
	if (available_procedures.length === 0) {
		frappe.msgprint('No procedures available for invoicing');
		return;
	}
	
	// Check if any procedures have already been invoiced
	let uninvoiced_procedures = available_procedures.filter(proc => !proc.invoiced);
	
	let dialog_fields = [
		{
			fieldtype: 'HTML',
			options: `
				<div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<h4 style="margin: 0 0 8px 0;">🧾 Generate Invoice</h4>
					<p style="margin: 0; opacity: 0.9;">Select procedures to include in the new invoice for <strong>${frm.doc.patient}</strong></p>
				</div>
			`
		},
		{
			fieldtype: 'Section Break',
			label: '📋 Invoice Details'
		},
		{
			fieldtype: 'Date',
			fieldname: 'invoice_date',
			label: 'Invoice Date',
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldtype: 'Select',
			fieldname: 'payment_terms',
			label: 'Payment Terms',
			options: 'Immediate\nNet 15\nNet 30\nNet 60',
			default: 'Net 30'
		},
		{
			fieldtype: 'Column Break'
		},
		{
			fieldtype: 'Link',
			fieldname: 'practitioner',
			label: 'Practitioner',
			options: 'Healthcare Practitioner',
			default: frm.doc.dentist,
			reqd: 1
		},
		{
			fieldtype: 'Link',
			fieldname: 'dental_clinic',
			label: 'Dental Clinic',
			options: 'Dental Clinic',
			default: frm.doc.clinic
		},
		{
			fieldtype: 'Section Break',
			label: '🔧 Select Procedures to Invoice'
		},
		{
			fieldtype: 'HTML',
			fieldname: 'procedures_selection',
			options: generate_procedure_selection_html(available_procedures)
		},
		{
			fieldtype: 'Section Break',
			label: '💰 Invoice Summary'
		},
		{
			fieldtype: 'HTML',
			fieldname: 'invoice_summary',
			options: '<div id="invoice-summary">Select procedures to see summary</div>'
		}
	];
	
	let d = new frappe.ui.Dialog({
		title: __('Generate Invoice'),
		fields: dialog_fields,
		size: 'large',
		primary_action_label: __('Create Invoice'),
		primary_action: function(values) {
			create_invoice_from_selection(frm, values, d, false);
		},
		secondary_action_label: __('Create & Print'),
		secondary_action: function(values) {
			create_invoice_from_selection(frm, values, d, true);
		}
	});
	
	// Add event listeners for procedure checkboxes
	setTimeout(() => {
		attach_procedure_selection_handlers(d);
	}, 500);
	
	d.show();
}

function generate_procedure_selection_html(procedures) {
	let html = `
		<div style="max-height: 400px; overflow-y: auto;">
			<div style="margin-bottom: 15px;">
				<button type="button" class="btn btn-sm btn-primary" onclick="select_all_procedures()">Select All</button>
				<button type="button" class="btn btn-sm btn-secondary" onclick="clear_all_procedures()">Clear All</button>
				<button type="button" class="btn btn-sm btn-info" onclick="select_uninvoiced_only()">Uninvoiced Only</button>
			</div>
			<table class="table table-bordered" style="margin: 0;">
				<thead style="background: #f8f9fa;">
					<tr>
						<th width="5%">Select</th>
						<th width="15%">Procedure</th>
						<th width="10%">Tooth</th>
						<th width="10%">Surface</th>
						<th width="10%">Status</th>
						<th width="12%">Date</th>
						<th width="12%">Amount</th>
						<th width="8%">Invoiced</th>
						<th width="18%">Notes</th>
					</tr>
				</thead>
				<tbody>
	`;
	
	procedures.forEach((proc, index) => {
		let amount = proc.actual_fee || proc.standard_fee || 0;
		let status_color = proc.status === 'Completed' ? '#28a745' : 
						  proc.status === 'In Progress' ? '#17a2b8' : '#ffc107';
		let tooth_display = proc.tooth_number === 'General' ? 'General' : `Tooth ${proc.tooth_number}`;
		let invoiced_status = proc.invoiced ? '✅ Yes' : '❌ No';
		let invoiced_color = proc.invoiced ? '#28a745' : '#dc3545';
		
		html += `
			<tr data-procedure-index="${index}">
				<td style="text-align: center;">
					<input type="checkbox" class="procedure-checkbox" data-index="${index}" 
						   ${!proc.invoiced ? 'checked' : ''} />
				</td>
				<td><strong>${proc.procedure_code}</strong></td>
				<td>${tooth_display}</td>
				<td>${proc.surface}</td>
				<td>
					<span style="background: ${status_color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px;">
						${proc.status}
					</span>
				</td>
				<td>${frappe.datetime.str_to_user(proc.planned_date)}</td>
				<td><strong>${format_currency(amount)}</strong></td>
				<td style="color: ${invoiced_color}; font-weight: bold;">${invoiced_status}</td>
				<td style="font-size: 12px;">${proc.notes || '-'}</td>
			</tr>
		`;
	});
	
	html += `
				</tbody>
			</table>
		</div>
	`;
	
	return html;
}

function attach_procedure_selection_handlers(dialog) {
	// Store procedures data in dialog for easy access
	dialog.procedures_data = window.current_frm.doc.tooth_procedures.filter(proc => proc.status !== 'Cancelled');
	
	// Add change handlers for checkboxes
	$(dialog.$wrapper).find('.procedure-checkbox').on('change', function() {
		update_invoice_summary(dialog);
	});
	
	// Initial summary update
	update_invoice_summary(dialog);
}

function update_invoice_summary(dialog) {
	let selected_procedures = [];
	let total_amount = 0;
	
	$(dialog.$wrapper).find('.procedure-checkbox:checked').each(function() {
		let index = parseInt($(this).data('index'));
		let procedure = dialog.procedures_data[index];
		selected_procedures.push(procedure);
		total_amount += procedure.actual_fee || procedure.standard_fee || 0;
	});
	
	let summary_html = `
		<div style="background: #f8f9fa; padding: 15px; border-radius: 6px;">
			<h6 style="margin: 0 0 10px 0; color: #495057;">📊 Invoice Summary</h6>
			<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px;">
				<div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
					<div style="font-size: 12px; color: #666;">PROCEDURES</div>
					<div style="font-size: 18px; font-weight: bold; color: #007bff;">${selected_procedures.length}</div>
				</div>
				<div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
					<div style="font-size: 12px; color: #666;">SUBTOTAL</div>
					<div style="font-size: 18px; font-weight: bold; color: #28a745;">${format_currency(total_amount)}</div>
				</div>
				<div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
					<div style="font-size: 12px; color: #666;">EST. TOTAL</div>
					<div style="font-size: 18px; font-weight: bold; color: #333;">${format_currency(total_amount * 1.08)}</div>
					<div style="font-size: 10px; color: #666;">Including 8% tax</div>
				</div>
			</div>
			${selected_procedures.length === 0 ? 
				'<div style="color: #dc3545; text-align: center; font-style: italic;">No procedures selected</div>' : 
				`<div style="font-size: 13px; color: #666;">
					Selected: ${selected_procedures.map(p => `${p.procedure_code} (${p.tooth_number === 'General' ? 'General' : 'Tooth ' + p.tooth_number})`).join(', ')}
				</div>`
			}
		</div>
	`;
	
	dialog.get_field('invoice_summary').$wrapper.html(summary_html);
}

// Global functions for procedure selection buttons
window.select_all_procedures = function() {
	$('.procedure-checkbox').prop('checked', true).trigger('change');
}

window.clear_all_procedures = function() {
	$('.procedure-checkbox').prop('checked', false).trigger('change');
}

window.select_uninvoiced_only = function() {
	$('.procedure-checkbox').each(function() {
		let index = parseInt($(this).data('index'));
		let procedure = window.current_frm.doc.tooth_procedures.filter(proc => proc.status !== 'Cancelled')[index];
		$(this).prop('checked', !procedure.invoiced).trigger('change');
	});
}

function create_invoice_from_selection(frm, values, dialog, should_print) {
	// Get selected procedures
	let selected_procedures = [];
	$(dialog.$wrapper).find('.procedure-checkbox:checked').each(function() {
		let index = parseInt($(this).data('index'));
		let procedure = dialog.procedures_data[index];
		selected_procedures.push(procedure);
	});
	
	if (selected_procedures.length === 0) {
		frappe.msgprint('Please select at least one procedure');
		return;
	}
	
	// Calculate due date based on payment terms
	let due_date = values.invoice_date;
	if (values.payment_terms === 'Net 15') {
		due_date = frappe.datetime.add_days(values.invoice_date, 15);
	} else if (values.payment_terms === 'Net 30') {
		due_date = frappe.datetime.add_days(values.invoice_date, 30);
	} else if (values.payment_terms === 'Net 60') {
		due_date = frappe.datetime.add_days(values.invoice_date, 60);
	}
	
	// Create invoice document
	let invoice_doc = {
		doctype: 'Invoice',
		patient: frm.doc.patient,
		practitioner: values.practitioner,
		dental_clinic: values.dental_clinic,
		invoice_date: values.invoice_date,
		due_date: due_date,
		payment_terms: values.payment_terms,
		invoice_status: 'Draft',
		invoice_items: []
	};
	
	// Add selected procedures as invoice items
	selected_procedures.forEach(procedure => {
		// Get procedure name for description
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Dental Procedure Master',
				name: procedure.procedure_code
			},
			async: false,
			callback: function(r) {
				if (r.message) {
					let description = r.message.procedure_name;
					let tooth_info = procedure.tooth_number === 'General' ? 'General Treatment' : `Tooth ${procedure.tooth_number} (${procedure.surface})`;
					
					// For general procedures, ensure surface is "General Treatment" and tooth_number is empty
					let invoice_surface = procedure.tooth_number === 'General' ? 'General Treatment' : procedure.surface;
					let invoice_tooth_number = procedure.tooth_number === 'General' ? '' : procedure.tooth_number;
					
					invoice_doc.invoice_items.push({
						procedure_code: procedure.procedure_code,
						description: `${description} - ${tooth_info}`,
						tooth_number: invoice_tooth_number,
						surface: invoice_surface,
						quantity: 1,
						amount: procedure.actual_fee || procedure.standard_fee || 0
					});
				}
			}
		});
	});
	
	// Create the invoice
	frappe.call({
		method: 'frappe.client.insert',
		args: {
			doc: invoice_doc
		},
		callback: function(r) {
			if (r.message) {
				let invoice_name = r.message.name;
				
				// Mark selected procedures as invoiced
				selected_procedures.forEach(procedure => {
					frappe.model.set_value('Tooth Procedure', procedure.name, 'invoiced', 1);
					frappe.model.set_value('Tooth Procedure', procedure.name, 'invoice_reference', invoice_name);
				});
				
				// Save the dental chart to persist the invoiced flags
				frm.save().then(() => {
					dialog.hide();
					
					// Show success message
					frappe.show_alert({
						message: __('Invoice {0} created successfully with {1} procedures', [invoice_name, selected_procedures.length]),
						indicator: 'green'
					});
					
					// Refresh the dental chart to show updated invoicing status
					create_interactive_dental_chart(frm);
					render_invoice_section(frm);
					
					// Handle printing if requested
					if (should_print) {
						// Print the invoice
						print_invoice(invoice_name);
					}
					
					// Show action buttons for the created invoice
					show_invoice_actions(invoice_name, frm);
				});
			}
		}
	});
}

function save_tooth_changes(frm, tooth_number, existing_conditions, existing_procedures, values) {
	// Set multiple flags to prevent duplicate logging from various sources
	window.saving_from_enhanced_dialog = true;
	frm._saving_from_enhanced_dialog = true;
	window._bulk_saving = true;
	frm._bulk_saving = true;
	
	// Also set a flag to prevent server-side automatic logging
	frm._skip_server_activity_logging = true;
	
	// Update existing conditions using frappe.model.set_value for reliable persistence
	existing_conditions.forEach((condition, index) => {
		const name = condition.name;
		const newCode = values[`condition_code_${index}`]    || condition.condition_code;
		const newSurface = values[`condition_surface_${index}`] || condition.surface;
		const newSeverity = values[`condition_severity_${index}`]|| condition.severity;
		const newNotes = values[`condition_notes_${index}`]   || condition.notes;
		const newDate = values[`condition_date_${index}`]    || condition.date_identified;
		frappe.model.set_value('Tooth Condition', name, 'condition_code', newCode);
		frappe.model.set_value('Tooth Condition', name, 'surface', newSurface);
		frappe.model.set_value('Tooth Condition', name, 'severity', newSeverity);
		frappe.model.set_value('Tooth Condition', name, 'notes', newNotes);
		frappe.model.set_value('Tooth Condition', name, 'date_identified', newDate);
	});

	// Update existing procedures using frappe.model.set_value for reliable persistence
	existing_procedures.forEach((procedure, index) => {
		const name = procedure.name;
		const oldStatus = procedure.status;
		const newProcCode = values[`procedure_code_${index}`]   || procedure.procedure_code;
		const newSurface = values[`procedure_surface_${index}`] || procedure.surface;
		const newStatus = values[`procedure_status_${index}`]  || procedure.status;
		const newNotes = values[`procedure_notes_${index}`]    || procedure.notes;
		const newPlannedDate = values[`procedure_planned_date_${index}`] || procedure.planned_date;
		const statusChangeDate = values[`procedure_status_date_${index}`] || frappe.datetime.get_today();
		
		frappe.model.set_value('Tooth Procedure', name, 'procedure_code', newProcCode);
		frappe.model.set_value('Tooth Procedure', name, 'surface', newSurface);
		frappe.model.set_value('Tooth Procedure', name, 'notes', newNotes);
		frappe.model.set_value('Tooth Procedure', name, 'planned_date', newPlannedDate);
		
		// Always update the status (we'll handle logging separately)
		frappe.model.set_value('Tooth Procedure', name, 'status', newStatus);
		
		// Handle status change with manual activity logging
		if (oldStatus !== newStatus) {
			// Log the status change manually with user-provided status change date
			let act = frm.add_child('chart_activities');
			act.activity_type = 'Procedure Status Changed';
			act.activity_description = __('Changed status of {0} on tooth {1} to {2}', [newProcCode, tooth_number, newStatus]);
			act.tooth_number = tooth_number;
			act.procedure_code = newProcCode;
			act.new_value = `Status: ${newStatus}`;
			act.activity_datetime = statusChangeDate + ' ' + frappe.datetime.now_time();
			act.performed_by = frappe.session.user;
			
			// Update completed_date only if status is completed
			if (newStatus === 'Completed') {
				frappe.model.set_value('Tooth Procedure', name, 'completed_date', statusChangeDate);
			} else {
				// Clear completed date if status is not completed
				frappe.model.set_value('Tooth Procedure', name, 'completed_date', '');
			}
		}
	});
	
	// Update fields and save
	frm.refresh_field('tooth_conditions');
	frm.refresh_field('tooth_procedures');
	frm.refresh_field('chart_activities');
	
	// Clear all flags after a short delay to allow all events to process
	setTimeout(() => {
		window.saving_from_enhanced_dialog = false;
		frm._saving_from_enhanced_dialog = false;
		window._bulk_saving = false;
		frm._bulk_saving = false;
		frm._skip_server_activity_logging = false;
	}, 3000);
	
	// Set a flag to prevent server-side duplicate logging
	frm.doc._skip_activity_logging = 1;
	
	// Save the document
	frm.save().then(() => {
		// Clear the flag after saving
		frm.doc._skip_activity_logging = 0;
		
		// Refresh the UI components without reloading
		create_interactive_dental_chart(frm);
		update_activity_timeline(frm);
		frappe.show_alert({
			message: __('Tooth changes saved successfully'),
			indicator: 'green'
		});
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
			// Properly remove child row via grid API to flag deletion
			let grid = frm.fields_dict.tooth_conditions.grid;
			let row = grid.get_row(condition_name);
			if (row) {
				row.remove();
			}
			// Save form to persist deletion
			frm.save();
			
			// Close dialog and refresh chart
			window.current_tooth_dialog.hide();
			setTimeout(() => create_interactive_dental_chart(frm), 500);
			
			frappe.show_alert({
				message: __('Condition removed successfully'),
				indicator: 'green'
			});
		}
	);
}

window.remove_procedure = function(procedure_name) {
	frappe.confirm(
		'Are you sure you want to remove this procedure?',
		function() {
			// Find and remove the procedure
			let frm = window.current_frm;
			// Properly remove child row via grid API to flag deletion
			let grid = frm.fields_dict.tooth_procedures.grid;
			let row = grid.get_row(procedure_name);
			if (row) {
				row.remove();
			}
			// Save form to persist deletion
			frm.save();
			
			// Close dialog and refresh chart
			window.current_tooth_dialog.hide();
			setTimeout(() => create_interactive_dental_chart(frm), 500);
			
			frappe.show_alert({
				message: __('Procedure removed successfully'),
				indicator: 'green'
			});
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
							options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
							default: 'Whole Tooth'
						},
						{
							fieldtype: 'Date',
							fieldname: 'date_identified',
							label: __('Date'),
							default: frappe.datetime.get_today(),
							reqd: 1
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
						condition_row.date_identified = values.date_identified;
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
							options: 'Whole Tooth\nOcclusal\nIncisal\nMesial\nDistal\nBuccal\nLingual\nFacial\nGeneral Treatment',
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
							fieldtype: 'Date',
							fieldname: 'planned_date',
							label: __('Date'),
							default: frappe.datetime.get_today(),
							reqd: 1
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
						procedure_row.planned_date = values.planned_date;
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

// Activity Timeline Functions
function update_activity_timeline(frm) {
	// Update help text for editable history
	if (frm.doc.chart_activities && frm.doc.chart_activities.length > 0) {
		frm.set_df_property('chart_activities', 'description', 
			`📝 <strong>Editable History:</strong> Click any row to edit details. Use Activity History buttons for advanced management (add manual entries, export, cleanup). Total activities: ${frm.doc.chart_activities.length}`
		);
	}
	
	if (!frm.doc.chart_activities || frm.doc.chart_activities.length === 0) {
		let empty_html = `
			<div style="text-align: center; padding: 40px; color: #6c757d;">
				<div style="font-size: 48px; margin-bottom: 15px;">📋</div>
				<h5>No Activities Recorded Yet</h5>
				<p>Start adding conditions or procedures to see the activity timeline</p>
			</div>
		`;
		frm.get_field('activity_timeline').$wrapper.html(empty_html);
		return;
	}
	
	// Sort activities by date (newest first)
	let activities = [...frm.doc.chart_activities].sort((a, b) => new Date(b.activity_datetime) - new Date(a.activity_datetime));
	
	let timeline_html = `
		<div class="activity-timeline" style="position: relative; padding: 20px 0;">
			<div style="position: absolute; left: 30px; top: 0; bottom: 0; width: 2px; background: #dee2e6;"></div>
	`;
	
	activities.forEach((activity, index) => {
		let icon = get_activity_icon(activity.activity_type);
		let color = get_activity_color(activity.activity_type);
		let datetime = frappe.datetime.str_to_user(activity.activity_datetime);
		
		timeline_html += `
			<div style="position: relative; margin-bottom: 25px; padding-left: 70px;">
				<div style="position: absolute; left: 20px; width: 20px; height: 20px; 
							background: ${color}; border-radius: 50%; display: flex; 
							align-items: center; justify-content: center; color: white; 
							font-size: 12px; z-index: 1; border: 3px solid white; 
							box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
					${icon}
				</div>
				<div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; 
							padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); position: relative;">
					<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
						<h6 style="margin: 0; color: ${color};">${activity.activity_type}</h6>
						<div style="display: flex; gap: 8px; align-items: center;">
							<button class="btn btn-xs btn-secondary" onclick="edit_activity_from_timeline('${activity.name}')" 
									style="padding: 2px 6px; font-size: 10px;">✏️ Edit</button>
							<small style="color: #6c757d;">${datetime}</small>
						</div>
					</div>
					<p style="margin: 0 0 8px 0; font-weight: 500;">${activity.activity_description || 'No description'}</p>
					${activity.tooth_number ? `<div style="margin-bottom: 5px;"><strong>Tooth:</strong> ${activity.tooth_number}</div>` : ''}
					${activity.old_value ? `<div style="margin-bottom: 5px;"><strong>Previous:</strong> ${activity.old_value}</div>` : ''}
					${activity.new_value ? `<div style="margin-bottom: 5px;"><strong>Current:</strong> ${activity.new_value}</div>` : ''}
					${activity.cost_impact ? `<div style="margin-bottom: 5px;"><strong>Cost Impact:</strong> <span style="color: ${activity.cost_impact > 0 ? '#dc3545' : '#28a745'};">${format_currency(activity.cost_impact)}</span></div>` : ''}
					${activity.additional_notes ? `<div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 13px;">${activity.additional_notes}</div>` : ''}
					<div style="margin-top: 8px; font-size: 12px; color: #6c757d;">
						👨‍⚕️ ${activity.performed_by || 'Unknown'}
					</div>
				</div>
			</div>
		`;
	});
	
	timeline_html += '</div>';
	
	// Add summary stats
	let stats = get_activity_stats(activities);
	timeline_html += `
		<div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 15px; border-radius: 8px; margin-top: 20px;">
			<h6 style="margin: 0 0 10px 0;">📊 Activity Summary</h6>
			<div style="display: flex; gap: 20px; flex-wrap: wrap;">
				<div><strong>Total Activities:</strong> ${activities.length}</div>
				<div><strong>Conditions:</strong> ${stats.conditions}</div>
				<div><strong>Procedures:</strong> ${stats.procedures}</div>
				<div><strong>Visits:</strong> ${stats.visits}</div>
				<div><strong>Cost Changes:</strong> ${format_currency(stats.total_cost_impact)}</div>
			</div>
		</div>
	`;
	
	frm.get_field('activity_timeline').$wrapper.html(timeline_html);
}

function get_activity_icon(activity_type) {
	const icons = {
		'Condition Added': '🦷',
		'Condition Removed': '✅',
		'Condition Modified': '📝',
		'Procedure Added': '🔧',
		'Procedure Removed': '🗑️',
		'Procedure Status Changed': '🔄',
		'Procedure Cost Modified': '💰',
		'Visit Recorded': '📋',
		'Chart Updated': '📊',
		'Treatment Completed': '✨'
	};
	return icons[activity_type] || '📌';
}

function get_activity_color(activity_type) {
	const colors = {
		'Condition Added': '#dc3545',
		'Condition Removed': '#28a745',
		'Condition Modified': '#ffc107',
		'Procedure Added': '#007bff',
		'Procedure Removed': '#6c757d',
		'Procedure Status Changed': '#17a2b8',
		'Procedure Cost Modified': '#fd7e14',
		'Visit Recorded': '#28a745',
		'Chart Updated': '#6f42c1',
		'Treatment Completed': '#20c997'
	};
	return colors[activity_type] || '#6c757d';
}

function get_activity_stats(activities) {
	let stats = {
		conditions: 0,
		procedures: 0,
		visits: 0,
		total_cost_impact: 0
	};
	
	activities.forEach(activity => {
		if (activity.activity_type.includes('Condition')) {
			stats.conditions++;
		} else if (activity.activity_type.includes('Procedure')) {
			stats.procedures++;
		} else if (activity.activity_type.includes('Visit')) {
			stats.visits++;
		}
		
		if (activity.cost_impact) {
			stats.total_cost_impact += activity.cost_impact;
		}
	});
	
	return stats;
}

// Activity Management Functions
function add_manual_activity(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Add Manual Activity Entry'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				options: `
					<div style="background: linear-gradient(135deg, #6f42c1, #6610f2); color: white; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
						<h5 style="margin: 0;">✏️ Manual Activity Entry</h5>
						<p style="margin: 5px 0 0 0; opacity: 0.9;">Add a custom activity entry to the dental chart history</p>
					</div>
				`
			},
			{
				fieldtype: 'Select',
				fieldname: 'activity_type',
				label: __('Activity Type'),
				options: 'Condition Added\nCondition Removed\nCondition Modified\nProcedure Added\nProcedure Removed\nProcedure Status Changed\nProcedure Cost Modified\nVisit Recorded\nChart Updated\nTreatment Completed\nNote Added\nCustom Entry',
				reqd: 1,
				default: 'Note Added'
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'activity_description',
				label: __('Activity Description'),
				reqd: 1,
				description: __('Describe what happened in this activity')
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Datetime',
				fieldname: 'activity_datetime',
				label: __('Date & Time'),
				default: frappe.datetime.now(),
				reqd: 1
			},
			{
				fieldtype: 'Link',
				fieldname: 'performed_by',
				label: __('Performed By'),
				options: 'User',
				default: frappe.session.user,
				reqd: 1
			},
			{
				fieldtype: 'Section Break',
				label: __('Additional Details')
			},
			{
				fieldtype: 'Data',
				fieldname: 'tooth_number',
				label: __('Tooth Number'),
				description: __('If this activity relates to a specific tooth')
			},
			{
				fieldtype: 'Link',
				fieldname: 'condition_code',
				label: __('Related Condition'),
				options: 'Dental Condition Master'
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Link',
				fieldname: 'procedure_code',
				label: __('Related Procedure'),
				options: 'Dental Procedure Master'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'cost_impact',
				label: __('Cost Impact'),
				description: __('Positive for additional costs, negative for reductions')
			},
			{
				fieldtype: 'Section Break',
				label: __('Notes')
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'old_value',
				label: __('Previous Value'),
				description: __('What was the value before this change?')
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'new_value',
				label: __('New Value'),
				description: __('What is the value after this change?')
			},
			{
				fieldtype: 'Text',
				fieldname: 'additional_notes',
				label: __('Additional Notes'),
				description: __('Any other relevant information')
			}
		],
		primary_action_label: __('Add Activity'),
		primary_action: function(values) {
			// Add the manual activity to the chart
			let activity_row = frm.add_child('chart_activities');
			
			Object.keys(values).forEach(key => {
				if (values[key]) {
					activity_row[key] = values[key];
				}
			});
			
			frm.refresh_field('chart_activities');
			frm.save();
			d.hide();
			
			// Update timeline
			setTimeout(() => {
				update_activity_timeline(frm);
			}, 1000);
			
			frappe.show_alert({
				message: __('Manual activity added successfully'),
				indicator: 'green'
			});
		}
	});
	d.show();
}

function export_activity_log(frm) {
	if (!frm.doc.chart_activities || frm.doc.chart_activities.length === 0) {
		frappe.msgprint(__('No activities to export'));
		return;
	}
	
	// Prepare data for export
	let activities = frm.doc.chart_activities.map(activity => ({
		'Date & Time': frappe.datetime.str_to_user(activity.activity_datetime),
		'Activity Type': activity.activity_type,
		'Description': activity.activity_description,
		'Tooth Number': activity.tooth_number || '',
		'Condition': activity.condition_code || '',
		'Procedure': activity.procedure_code || '',
		'Cost Impact': activity.cost_impact ? frappe.format_value(activity.cost_impact, {'fieldtype': 'Currency'}) : '',
		'Previous Value': activity.old_value || '',
		'New Value': activity.new_value || '',
		'Performed By': activity.performed_by || '',
		'Notes': activity.additional_notes || ''
	}));
	
	// Create CSV content
	let csv_content = "data:text/csv;charset=utf-8,";
	let headers = Object.keys(activities[0]);
	csv_content += headers.join(',') + '\n';
	
	activities.forEach(activity => {
		let row = headers.map(header => {
			let value = activity[header] || '';
			// Escape commas and quotes in CSV
			if (value.includes(',') || value.includes('"')) {
				value = '"' + value.replace(/"/g, '""') + '"';
			}
			return value;
		});
		csv_content += row.join(',') + '\n';
	});
	
	// Download the file
	let encoded_uri = encodeURI(csv_content);
	let link = document.createElement("a");
	link.setAttribute("href", encoded_uri);
	link.setAttribute("download", `dental_chart_activities_${frm.doc.name}_${frappe.datetime.nowdate()}.csv`);
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	
	frappe.show_alert({
		message: __('Activity log exported successfully'),
		indicator: 'green'
	});
}

function clear_old_activities(frm) {
	if (!frm.doc.chart_activities || frm.doc.chart_activities.length === 0) {
		frappe.msgprint(__('No activities to clear'));
		return;
	}
	
	let d = new frappe.ui.Dialog({
		title: __('Clear Old Activities'),
		fields: [
			{
				fieldtype: 'HTML',
				options: `
					<div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
						<h6 style="margin: 0 0 8px 0; color: #856404;">⚠️ Warning</h6>
						<p style="margin: 0; color: #856404;">This action will permanently delete old activity entries. This cannot be undone.</p>
					</div>
				`
			},
			{
				fieldtype: 'Date',
				fieldname: 'cutoff_date',
				label: __('Delete activities older than'),
				default: frappe.datetime.add_days(frappe.datetime.nowdate(), -90),
				reqd: 1,
				description: __('All activities before this date will be deleted')
			},
			{
				fieldtype: 'HTML',
				options: `<p><strong>Current total activities:</strong> ${frm.doc.chart_activities.length}</p>`
			}
		],
		primary_action_label: __('Delete Old Activities'),
		primary_action: function(values) {
			let cutoff_date = new Date(values.cutoff_date);
			let activities_to_keep = [];
			let deleted_count = 0;
			
			frm.doc.chart_activities.forEach(activity => {
				let activity_date = new Date(activity.activity_datetime);
				if (activity_date >= cutoff_date) {
					activities_to_keep.push(activity);
				} else {
					deleted_count++;
				}
			});
			
			if (deleted_count === 0) {
				frappe.msgprint(__('No activities found older than the specified date'));
				d.hide();
				return;
			}
			
			frappe.confirm(
				__(`This will delete ${deleted_count} activities and keep ${activities_to_keep.length}. Continue?`),
				function() {
					// Clear the table and add back only the activities to keep
					frm.clear_table('chart_activities');
					activities_to_keep.forEach(activity => {
						let new_row = frm.add_child('chart_activities');
						Object.keys(activity).forEach(key => {
							new_row[key] = activity[key];
						});
					});
					
					frm.refresh_field('chart_activities');
					frm.save();
					d.hide();
					
					// Update timeline
					setTimeout(() => {
						update_activity_timeline(frm);
					}, 1000);
					
					frappe.show_alert({
						message: __(`Deleted ${deleted_count} old activities successfully`),
						indicator: 'green'
					});
				}
			);
		}
	});
	d.show();
}

function add_general_procedure(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Add General Procedure'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				options: `
					<div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
						<h5 style="margin: 0;">🔧 General Procedure</h5>
						<p style="margin: 5px 0 0 0; opacity: 0.9;">Add a procedure that applies to the entire mouth or general treatment</p>
					</div>
				`
			},
			{
				fieldtype: 'Link',
				fieldname: 'procedure_code',
				label: __('Procedure'),
				options: 'Dental Procedure Master',
				reqd: 1,
				change: function() {
					let procedure_code = this.get_value();
					if (procedure_code) {
						frappe.call({
							method: 'frappe.client.get',
							args: {
								doctype: 'Dental Procedure Master',
								name: procedure_code
							},
							callback: function(r) {
								if (r.message) {
									let procedure = r.message;
									d.set_value('standard_fee', procedure.standard_fee || 0);
									d.set_value('actual_fee', procedure.standard_fee || 0);
									update_general_cost_info_display(d, procedure);
								}
							}
						});
					}
				}
			},
			{
				fieldtype: 'Select',
				fieldname: 'status',
				label: __('Status'),
				options: 'Planned\nIn Progress\nCompleted\nCancelled',
				default: 'Planned',
				reqd: 1
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Date',
				fieldname: 'planned_date',
				label: __('Planned Date'),
				default: frappe.datetime.nowdate(),
				reqd: 1
			},
			{
				fieldtype: 'Link',
				fieldname: 'planned_by',
				label: __('Planned By'),
				options: 'User',
				default: frappe.session.user,
				reqd: 1
			},
			{
				fieldtype: 'Section Break',
				label: __('Cost Information')
			},
			{
				fieldtype: 'Currency',
				fieldname: 'standard_fee',
				label: __('Standard Fee'),
				read_only: 1,
				description: __('Standard fee from procedure master')
			},
			{
				fieldtype: 'Currency',
				fieldname: 'actual_fee',
				label: __('Actual Fee'),
				description: __('Actual fee to be charged (editable by doctor)'),
				change: function() {
					calculate_general_patient_portion(d);
				}
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'insurance_covered',
				label: __('Insurance Covered'),
				default: 0,
				description: __('Amount covered by insurance'),
				change: function() {
					calculate_general_patient_portion(d);
				}
			},
			{
				fieldtype: 'Currency',
				fieldname: 'patient_portion',
				label: __('Patient Portion'),
				read_only: 1,
				description: __('Amount patient needs to pay')
			},
			{
				fieldtype: 'Section Break'
			},
			{
				fieldtype: 'HTML',
				fieldname: 'cost_info_display',
				options: '<div id="general-cost-info"></div>'
			},
			{
				fieldtype: 'Section Break',
				label: __('Additional Information')
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: __('Notes')
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'treatment_plan_notes',
				label: __('Treatment Plan Notes')
			}
		],
		primary_action_label: __('Add General Procedure'),
		primary_action: function(values) {
			// Add the general procedure
			let procedure_row = frm.add_child('tooth_procedures');
			procedure_row.tooth_number = 'General'; // Special marker for general procedures
			procedure_row.tooth_name = 'General Treatment';
			procedure_row.procedure_code = values.procedure_code;
			procedure_row.surface = 'General Treatment';
			procedure_row.status = values.status;
			procedure_row.planned_date = values.planned_date;
			procedure_row.planned_by = values.planned_by;
			procedure_row.notes = values.notes;
			procedure_row.treatment_plan_notes = values.treatment_plan_notes;
			procedure_row.standard_fee = values.standard_fee || 0;
			procedure_row.actual_fee = values.actual_fee || values.standard_fee || 0;
			procedure_row.insurance_covered = values.insurance_covered || 0;
			procedure_row.patient_portion = values.patient_portion || 0;
			
			if (values.status === 'Completed') {
				procedure_row.completed_date = frappe.datetime.nowdate();
			}
			
			frm.refresh_field('tooth_procedures');
			frm.save();
			d.hide();
			
			// Refresh the chart
			setTimeout(() => {
				create_interactive_dental_chart(frm);
			}, 500);
			
			frappe.show_alert({
				message: __('General procedure added successfully'),
				indicator: 'green'
			});
		}
	});
	d.show();
}

function calculate_general_patient_portion(dialog) {
	let actual_fee = dialog.get_value('actual_fee') || 0;
	let insurance_covered = dialog.get_value('insurance_covered') || 0;
	let patient_portion = Math.max(0, actual_fee - insurance_covered);
	dialog.set_value('patient_portion', patient_portion);
}

function update_general_cost_info_display(dialog, procedure) {
	let actual_fee = dialog.get_value('actual_fee') || 0;
	let insurance_covered = dialog.get_value('insurance_covered') || 0;
	let patient_portion = actual_fee - insurance_covered;
	
	let cost_html = `
		<div style="background: linear-gradient(135deg, #e3f2fd, #bbdefb); padding: 15px; border-radius: 8px; margin: 10px 0;">
			<h6 style="margin: 0 0 10px 0; color: #1565c0;">💰 General Procedure Cost Breakdown</h6>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
				<div style="background: white; padding: 10px; border-radius: 4px;">
					<div style="font-size: 12px; color: #666; margin-bottom: 4px;">STANDARD FEE</div>
					<div style="font-size: 16px; font-weight: bold; color: #333;">${format_currency(procedure.standard_fee || 0)}</div>
				</div>
				<div style="background: white; padding: 10px; border-radius: 4px;">
					<div style="font-size: 12px; color: #666; margin-bottom: 4px;">ACTUAL FEE</div>
					<div style="font-size: 16px; font-weight: bold; color: #007bff;">${format_currency(actual_fee)}</div>
				</div>
				<div style="background: white; padding: 10px; border-radius: 4px;">
					<div style="font-size: 12px; color: #666; margin-bottom: 4px;">INSURANCE COVERED</div>
					<div style="font-size: 16px; font-weight: bold; color: #28a745;">${format_currency(insurance_covered)}</div>
				</div>
				<div style="background: white; padding: 10px; border-radius: 4px;">
					<div style="font-size: 12px; color: #666; margin-bottom: 4px;">PATIENT PORTION</div>
					<div style="font-size: 16px; font-weight: bold; color: ${patient_portion > 0 ? '#dc3545' : '#28a745'};">${format_currency(patient_portion)}</div>
				</div>
			</div>
			<div style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.7); border-radius: 4px; font-size: 13px;">
				<strong>Procedure:</strong> ${procedure.procedure_name || procedure.name} - General Treatment
			</div>
		</div>
	`;
	
	dialog.get_field('cost_info_display').$wrapper.html(cost_html);
}

// Enhanced timeline with edit functionality and multi-tooth grouping
window.edit_activity_from_timeline = function(activity_name) {
	let frm = window.current_frm;
	let activity = frm.doc.chart_activities.find(a => a.name === activity_name);
	
	if (!activity) {
		frappe.msgprint(__('Activity not found'));
		return;
	}
	
	let d = new frappe.ui.Dialog({
		title: __('Edit Activity: ') + activity.activity_type,
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				options: `
					<div style="background: linear-gradient(135deg, #17a2b8, #138496); color: white; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
						<h5 style="margin: 0;">✏️ Edit Activity</h5>
						<p style="margin: 5px 0 0 0; opacity: 0.9;">Modify the details of this activity entry</p>
					</div>
				`
			},
			{
				fieldtype: 'Select',
				fieldname: 'activity_type',
				label: __('Activity Type'),
				options: 'Condition Added\nCondition Removed\nCondition Modified\nProcedure Added\nProcedure Removed\nProcedure Status Changed\nProcedure Cost Modified\nVisit Recorded\nChart Updated\nTreatment Completed\nNote Added\nCustom Entry',
				default: activity.activity_type,
				reqd: 1
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'activity_description',
				label: __('Activity Description'),
				default: activity.activity_description,
				reqd: 1
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Datetime',
				fieldname: 'activity_datetime',
				label: __('Date & Time'),
				default: activity.activity_datetime,
				reqd: 1
			},
			{
				fieldtype: 'Link',
				fieldname: 'performed_by',
				label: __('Performed By'),
				options: 'User',
				default: activity.performed_by,
				reqd: 1
			},
			{
				fieldtype: 'Section Break',
				label: __('Additional Details')
			},
			{
				fieldtype: 'Data',
				fieldname: 'tooth_number',
				label: __('Tooth Number'),
				default: activity.tooth_number
			},
			{
				fieldtype: 'Link',
				fieldname: 'condition_code',
				label: __('Related Condition'),
				options: 'Dental Condition Master',
				default: activity.condition_code
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Link',
				fieldname: 'procedure_code',
				label: __('Related Procedure'),
				options: 'Dental Procedure Master',
				default: activity.procedure_code
			},
			{
				fieldtype: 'Currency',
				fieldname: 'cost_impact',
				label: __('Cost Impact'),
				default: activity.cost_impact
			},
			{
				fieldtype: 'Section Break',
				label: __('Notes')
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'old_value',
				label: __('Previous Value'),
				default: activity.old_value
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'new_value',
				label: __('New Value'),
				default: activity.new_value
			},
			{
				fieldtype: 'Text',
				fieldname: 'additional_notes',
				label: __('Additional Notes'),
				default: activity.additional_notes
			}
		],
		primary_action_label: __('Update Activity'),
		primary_action: function(values) {
			// Update the activity
			Object.keys(values).forEach(key => {
				if (values[key] !== undefined) {
					activity[key] = values[key];
				}
			});
			
			frm.refresh_field('chart_activities');
			frm.save();
			d.hide();
			
			// Update timeline
			setTimeout(() => {
				update_activity_timeline(frm);
			}, 1000);
			
			frappe.show_alert({
				message: __('Activity updated successfully'),
				indicator: 'green'
			});
		}
	});
	d.show(); 
}

// Catch status changes in the Tooth Procedure table and log them immediately
frappe.ui.form.on('Tooth Procedure', {
	status: function(frm, cdt, cdn) {
		// Skip if this change is coming from the enhanced dialog to prevent duplicates
		if (window.saving_from_enhanced_dialog || frm._saving_from_enhanced_dialog) {
			return;
		}
		
		// Also skip if we're in the middle of a batch save operation
		if (frm._bulk_saving || window._bulk_saving) {
			return;
		}
		
		let proc = locals[cdt][cdn];
		let newStatus = proc.status;
		// Prompt user for status date
		let d = new frappe.ui.Dialog({
			title: __('Set status date'),
			fields: [
				{fieldtype:'Date', fieldname:'status_date', label:__('Date'), default: frappe.datetime.nowdate(), reqd:1}
			],
			primary_action_label: __('Save'),
			primary_action: function(values) {
				// Update completed_date if applicable
				if (newStatus === 'Completed') {
					frappe.model.set_value(cdt, cdn, 'completed_date', values.status_date);
				}
				// Log activity with chosen date
				let act = frm.add_child('chart_activities');
				act.activity_type = 'Procedure Status Changed';
				act.activity_description = __('Changed status of {0} on tooth {1} to {2}', [proc.procedure_code, proc.tooth_number, newStatus]);
				act.tooth_number = proc.tooth_number;
				act.procedure_code = proc.procedure_code;
				act.new_value = `Status: ${newStatus}`;
				act.activity_datetime = values.status_date + ' ' + frappe.datetime.now_time();
				act.performed_by = frappe.session.user;
				frm.refresh_field('chart_activities');
				update_activity_timeline(frm);
				frm.save();
				d.hide();
			}
		});
		d.show();
	}
});

// Log changes to Tooth Condition child rows and persist edits
function log_condition_change(frm, cdt, cdn) {
    let cond = locals[cdt][cdn];
    let act = frm.add_child('chart_activities');
    act.activity_type = 'Condition Modified';
    act.activity_description = __('Modified condition {0} on tooth {1}', [cond.condition_code, cond.tooth_number]);
    act.tooth_number = cond.tooth_number;
    act.condition_code = cond.condition_code;
    act.new_value = `${cond.condition_code} on ${cond.surface}` + (cond.severity ? ` (${cond.severity})` : '');
    act.activity_datetime = frappe.datetime.now_datetime();
    act.performed_by = frappe.session.user;
    
    frm.refresh_field('chart_activities');
    update_activity_timeline(frm);
    frm.save();
}

// Catch field changes in the Tooth Condition child table to log and save
frappe.ui.form.on('Tooth Condition', {
    condition_code: log_condition_change,
    surface: log_condition_change,
    severity: log_condition_change,
    notes: log_condition_change
});

// Payment section: fetch and display payment cards with enhanced functionality
function render_payment_section(frm) {
    // Remove existing payments section to avoid duplicates
    $('.dental-payments-section').remove();
    frappe.call({
        method: 'dentcharts.dentcharts.doctype.dental_payment_entry.dental_payment_entry.get_payments_for_patient',
        args: { patient: frm.doc.patient },
        callback: function(r) {
            if (r.message) {
                let payments = r.message;
                
                // Calculate payment statistics
                let total_payments = payments.reduce((sum, p) => sum + (p.payment_amount || 0), 0);
                let recent_payments = payments.filter(p => {
                    let payment_date = new Date(p.payment_date);
                    let thirty_days_ago = new Date();
                    thirty_days_ago.setDate(thirty_days_ago.getDate() - 30);
                    return payment_date >= thirty_days_ago;
                });
                let recent_total = recent_payments.reduce((sum, p) => sum + (p.payment_amount || 0), 0);
                
                // Create summary card
                let summary_html = `
                    <div style="display:flex; gap:15px; margin-bottom:20px; flex-wrap:wrap;">
                        <div class="summary-card" style="background:linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color:white; padding:20px; border-radius:12px; min-width:200px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                            <div style="font-size:24px; font-weight:bold; margin-bottom:5px;">${format_currency(total_payments)}</div>
                            <div style="opacity:0.9;">💳 Total Payments</div>
                            <div style="font-size:12px; margin-top:5px; opacity:0.8;">${payments.length} payment${payments.length !== 1 ? 's' : ''}</div>
                        </div>
                        
                        <div class="summary-card" style="background:linear-gradient(135deg, #00cec9 0%, #00b894 100%); color:white; padding:20px; border-radius:12px; min-width:200px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                            <div style="font-size:24px; font-weight:bold; margin-bottom:5px;">${format_currency(recent_total)}</div>
                            <div style="opacity:0.9;">📅 Last 30 Days</div>
                            <div style="font-size:12px; margin-top:5px; opacity:0.8;">${recent_payments.length} recent</div>
                        </div>
                    </div>
                `;
                
                let cards = payments.map(p => {
                    let method_color = get_payment_method_color(p.payment_method);
                    let status_color = get_payment_status_color(p.payment_status);
                    
                    return `
                        <div class="payment-card" onclick="edit_payment_quick('${p.name}')" style="
                            background:${status_color.bg}; 
                            border:2px solid ${status_color.border}; 
                            padding:18px; 
                            border-radius:12px; 
                            min-width:260px; 
                            cursor:pointer; 
                            transition:all 0.3s ease;
                            box-shadow:0 3px 10px rgba(0,0,0,0.1);
                        " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.15)'" 
                           onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 3px 10px rgba(0,0,0,0.1)'">
                            
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                                <div style="font-weight:bold; font-size:16px; color:${status_color.text};">💳 ${frappe.datetime.str_to_user(p.payment_date)}</div>
                                <div style="background:${status_color.badge}; color:white; padding:4px 8px; border-radius:20px; font-size:11px; font-weight:bold;">
                                    ${p.payment_status}
                                </div>
                            </div>
                            
                            <div style="margin-bottom:12px;">
                                <div style="font-size:24px; font-weight:bold; color:${status_color.text};">
                                    ${format_currency(p.payment_amount)}
                                </div>
                                ${p.invoice ? `<div style="font-size:12px; color:${status_color.text}; opacity:0.8;">Invoice: ${p.invoice}</div>` : ''}
                            </div>
                            
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <div style="background:${method_color}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:bold;">
                                    ${p.payment_method}
                                </div>
                                ${p.reference_number ? `<div style="font-size:11px; color:${status_color.text}; opacity:0.7;">Ref: ${p.reference_number}</div>` : ''}
                            </div>
                            
                            ${p.notes ? `
                                <div style="background:rgba(0,0,0,0.05); padding:8px; border-radius:6px; margin-top:8px;">
                                    <div style="font-size:11px; color:${status_color.text}; opacity:0.8;">${p.notes}</div>
                                </div>
                            ` : ''}
                        </div>`;
                }).join('');

                let html = `
                    <div class="dental-payments-section" style="margin-top:30px;">
                        <h5 style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
                            💳 ${__('Payments & Transactions')}
                            <button class="btn btn-sm btn-success" onclick="record_payment_for_patient()" style="margin-left:auto; border-radius:6px;">
                                ➕ New Payment
                            </button>
                        </h5>
                        
                        ${summary_html}
                        
                        <div style="display:flex; gap:15px; flex-wrap:wrap; align-items:flex-start;">
                            ${cards}
                        </div>
                    </div>
                `;
                // Append below chart
                $('.dental-chart-container').append(html);
            }
        }
    });
}

// Custom dialog to record a general payment (not against an invoice)
window.record_payment_for_patient = function() {
    let frm = window.current_frm;
    let dialog = new frappe.ui.Dialog({
        title: __('Record Payment'),
        fields: [
            {fieldtype:'Link', fieldname:'invoice', label:__('Invoice'), options:'Invoice', reqd:1},
            {fieldtype:'Currency', fieldname:'payment_amount', label:__('Payment Amount'), reqd:1},
            {fieldtype:'Select', fieldname:'payment_method', label:__('Payment Method'), options:'Cash\nCredit Card\nDebit Card\nCheck\nBank Transfer\nOnline Payment', default:'Cash', reqd:1},
            {fieldtype:'Date', fieldname:'payment_date', label:__('Payment Date'), default: frappe.datetime.get_today(), reqd:1},
            {fieldtype:'Data', fieldname:'reference_number', label:__('Reference Number')},
            {fieldtype:'Text', fieldname:'notes', label:__('Notes')}
        ],
        primary_action_label: __('Submit'),
        primary_action: function(values) {
            let doc = {
                doctype: 'Dental Payment Entry',
                invoice: values.invoice,
                patient: frm.doc.patient,
                payment_amount: values.payment_amount,
                payment_method: values.payment_method,
                payment_date: values.payment_date,
                reference_number: values.reference_number,
                notes: values.notes
            };
            frappe.call({method:'frappe.client.insert', args:{doc:doc}, callback:function(r) {
                frappe.call({method:'frappe.client.submit', args:{doc:r.message}, callback:function(){
                    dialog.hide();
                    frappe.show_alert({message:__('Payment recorded'), indicator:'green'});
                    render_payment_section(frm);
                    render_invoice_section(frm);
                }});
            }});
        }
    });
    dialog.set_value('invoice', '');
    dialog.show();
};

// Invoice section: fetch and display invoice cards with enhanced functionality
function render_invoice_section(frm) {
    // Remove existing invoices section to avoid duplicates
    $('.dental-invoices-section').remove();
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Invoice',
            filters: { patient: frm.doc.patient },
            fields: ['name', 'invoice_status', 'payment_status', 'total_amount', 'paid_amount', 'outstanding_amount', 'creation', 'due_date'],
            order_by: 'creation desc'
        },
        callback: function(r) {
            if (r.message) {
                let invoices = r.message;
                
                // Calculate summary statistics
                let total_invoiced = invoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0);
                let total_paid = invoices.reduce((sum, inv) => sum + (inv.paid_amount || 0), 0);
                let total_outstanding = invoices.reduce((sum, inv) => sum + (inv.outstanding_amount || 0), 0);
                let pending_invoices = invoices.filter(inv => inv.outstanding_amount > 0);
                
                // Create summary cards
                let summary_html = `
                    <div style="display:flex; gap:15px; margin-bottom:20px; flex-wrap:wrap;">
                        <div class="summary-card" style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:20px; border-radius:12px; min-width:200px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                            <div style="font-size:24px; font-weight:bold; margin-bottom:5px;">${format_currency(total_invoiced)}</div>
                            <div style="opacity:0.9;">💰 Total Invoiced</div>
                            <div style="font-size:12px; margin-top:5px; opacity:0.8;">${invoices.length} invoice${invoices.length !== 1 ? 's' : ''}</div>
                        </div>
                        
                        <div class="summary-card" style="background:linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color:white; padding:20px; border-radius:12px; min-width:200px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                            <div style="font-size:24px; font-weight:bold; margin-bottom:5px;">${format_currency(total_paid)}</div>
                            <div style="opacity:0.9;">✅ Total Paid</div>
                            <div style="font-size:12px; margin-top:5px; opacity:0.8;">${((total_paid/total_invoiced)*100 || 0).toFixed(1)}% collected</div>
                        </div>
                        
                        <div class="summary-card" style="background:linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%); color:white; padding:20px; border-radius:12px; min-width:200px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                            <div style="font-size:24px; font-weight:bold; margin-bottom:5px;">${format_currency(total_outstanding)}</div>
                            <div style="opacity:0.9;">⏰ Outstanding</div>
                            <div style="font-size:12px; margin-top:5px; opacity:0.8;">${pending_invoices.length} pending</div>
                        </div>
                    </div>
                `;
                
                // Create individual invoice cards with color coding
                let cards = invoices.map(inv => {
                    let status_color = get_invoice_status_color(inv.payment_status, inv.outstanding_amount);
                    let is_overdue = inv.due_date && new Date(inv.due_date) < new Date() && inv.outstanding_amount > 0;
                    
                    return `
                        <div class="invoice-card" onclick="edit_invoice_quick('${inv.name}')" style="
                            background:${status_color.bg}; 
                            border:2px solid ${status_color.border}; 
                            padding:18px; 
                            border-radius:12px; 
                            min-width:280px; 
                            cursor:pointer; 
                            transition:all 0.3s ease;
                            box-shadow:0 3px 10px rgba(0,0,0,0.1);
                            position:relative;
                            ${is_overdue ? 'animation: pulse-red 2s infinite;' : ''}
                        " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.15)'" 
                           onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 3px 10px rgba(0,0,0,0.1)'">
                            
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                                <div style="font-weight:bold; font-size:16px; color:${status_color.text};">📄 ${inv.name}</div>
                                <div style="background:${status_color.badge}; color:white; padding:4px 8px; border-radius:20px; font-size:11px; font-weight:bold;">
                                    ${inv.payment_status}
                                </div>
                            </div>
                            
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
                                <div style="color:${status_color.text};">
                                    <div style="font-size:12px; opacity:0.8;">Total Amount</div>
                                    <div style="font-weight:bold;">${format_currency(inv.total_amount)}</div>
                                </div>
                                <div style="color:${status_color.text};">
                                    <div style="font-size:12px; opacity:0.8;">Paid Amount</div>
                                    <div style="font-weight:bold;">${format_currency(inv.paid_amount)}</div>
                                </div>
                            </div>
                            
                            ${inv.outstanding_amount > 0 ? `
                                <div style="background:rgba(255,107,107,0.1); border:1px solid #ff6b6b; padding:8px; border-radius:6px; margin-bottom:12px;">
                                    <div style="color:#d63031; font-weight:bold; font-size:14px;">
                                        💸 Due: ${format_currency(inv.outstanding_amount)}
                                    </div>
                                    ${inv.due_date ? `<div style="font-size:11px; color:#636e72; margin-top:2px;">Due: ${frappe.datetime.str_to_user(inv.due_date)}</div>` : ''}
                                </div>
                            ` : `
                                <div style="background:rgba(0,184,148,0.1); border:1px solid #00b894; padding:8px; border-radius:6px; margin-bottom:12px;">
                                    <div style="color:#00b894; font-weight:bold; font-size:14px;">
                                        ✅ Fully Paid
                                    </div>
                                </div>
                            `}
                            
                            <div style="display:flex; gap:8px; margin-top:12px;">
                                <button class="btn btn-xs btn-primary" onclick="event.stopPropagation(); record_payment_for_invoice('${inv.name}', ${inv.outstanding_amount})" 
                                        style="flex:1; border-radius:6px;">
                                    💳 Payment
                                </button>
                                <button class="btn btn-xs btn-secondary" onclick="event.stopPropagation(); print_invoice('${inv.name}')" 
                                        style="border-radius:6px;">
                                    🖨️ Print
                                </button>
                            </div>
                            
                            ${is_overdue ? `
                                <div style="position:absolute; top:-5px; right:-5px; background:#ff3838; color:white; border-radius:50%; width:20px; height:20px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">
                                    !
                                </div>
                            ` : ''}
                        </div>`;
                }).join('');
                
                let html = `
                    <div class="dental-invoices-section" style="margin-top:30px;">
                        <h5 style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
                            🧾 ${__('Invoices & Billing')} 
                            <button class="btn btn-sm btn-success" onclick="show_invoice_generation_dialog(cur_frm)" style="margin-left:auto; border-radius:6px;">
                                ➕ New Invoice
                            </button>
                        </h5>
                        
                        ${summary_html}
                        
                        <div style="display:flex; gap:15px; flex-wrap:wrap; align-items:flex-start;">
                            ${cards}
                        </div>
                        
                        <style>
                            @keyframes pulse-red {
                                0% { box-shadow: 0 3px 10px rgba(0,0,0,0.1); }
                                50% { box-shadow: 0 3px 15px rgba(255,107,107,0.4); }
                                100% { box-shadow: 0 3px 10px rgba(0,0,0,0.1); }
                            }
                        </style>
                    </div>`;
                // Append below chart
                $('.dental-chart-container').append(html);
            }
        }
    });
}

// Custom dialog to record a payment in one step (insert + submit)
window.record_payment_for_invoice = function(invoice, amount) {
    let frm = window.current_frm;
    let dialog = new frappe.ui.Dialog({
        title: __('Record Payment for {0}', [invoice]),
        fields: [
            {fieldtype:'Currency', fieldname:'payment_amount', label:__('Payment Amount'), reqd:1, default: amount},
            {fieldtype:'Select', fieldname:'payment_method', label:__('Payment Method'), options:'Cash\nCredit Card\nDebit Card\nCheck\nBank Transfer\nOnline Payment', default:'Cash', reqd:1},
            {fieldtype:'Date', fieldname:'payment_date', label:__('Payment Date'), default: frappe.datetime.get_today(), reqd:1},
            {fieldtype:'Data', fieldname:'reference_number', label:__('Reference Number')},
            {fieldtype:'Text', fieldname:'notes', label:__('Notes')}
        ],
        primary_action_label: __('Submit'),
        primary_action: function(values) {
            let doc = {
                doctype: 'Dental Payment Entry',
                invoice: invoice,
                patient: frm.doc.patient,
                payment_amount: values.payment_amount,
                payment_method: values.payment_method,
                payment_date: values.payment_date,
                reference_number: values.reference_number,
                notes: values.notes
            };
            frappe.call({
                method: 'frappe.client.insert', args: {doc: doc}, callback: function(r) {
                    let name = r.message.name;
                    frappe.call({method: 'frappe.client.submit', args: {doc: r.message}, callback: function() {
                        dialog.hide();
                        frappe.show_alert({message: __('Payment recorded'), indicator:'green'});
                        render_payment_section(frm);
                        render_invoice_section(frm);
                    }});
                }
            });
        }
    });
    dialog.show();
};

// Helper function to print invoice
function print_invoice(invoice_name) {
	// Use Frappe's print functionality
	frappe.utils.print(
		'Invoice',
		invoice_name,
		null, // print_format (use default)
		null, // letterhead
		null  // language
	);
}

// Helper function to get invoice status colors
function get_invoice_status_color(payment_status, outstanding_amount) {
	if (payment_status === 'Paid' || outstanding_amount <= 0) {
		return {
			bg: 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)',
			border: '#28a745',
			text: '#155724',
			badge: '#28a745'
		};
	} else if (payment_status === 'Partially Paid') {
		return {
			bg: 'linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)',
			border: '#ffc107',
			text: '#856404',
			badge: '#ffc107'
		};
	} else if (payment_status === 'Unpaid' || payment_status === 'Overdue') {
		return {
			bg: 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)',
			border: '#dc3545',
			text: '#721c24',
			badge: '#dc3545'
		};
	} else {
		return {
			bg: 'linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%)',
			border: '#6c757d',
			text: '#495057',
			badge: '#6c757d'
		};
	}
}

// Quick edit invoice function
function edit_invoice_quick(invoice_name) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Invoice',
			name: invoice_name
		},
		callback: function(r) {
			if (r.message) {
				let invoice = r.message;
				show_invoice_edit_dialog(invoice);
			}
		}
	});
}

// Show invoice edit dialog
function show_invoice_edit_dialog(invoice) {
	let d = new frappe.ui.Dialog({
		title: `📄 Edit Invoice: ${invoice.name}`,
		fields: [
			{
				fieldtype: 'Section Break',
				label: '📋 Basic Information'
			},
			{
				fieldtype: 'Data',
				fieldname: 'title',
				label: 'Title',
				default: invoice.title
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Select',
				fieldname: 'invoice_status',
				label: 'Invoice Status',
				options: 'Draft\nSent\nPaid\nCancelled',
				default: invoice.invoice_status,
				reqd: 1
			},
			{
				fieldtype: 'Section Break',
				label: '💰 Financial Details'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'total_amount',
				label: 'Total Amount',
				default: invoice.total_amount,
				reqd: 1
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'paid_amount',
				label: 'Paid Amount',
				default: invoice.paid_amount || 0
			},
			{
				fieldtype: 'Section Break',
				label: '📅 Dates'
			},
			{
				fieldtype: 'Date',
				fieldname: 'invoice_date',
				label: 'Invoice Date',
				default: invoice.invoice_date
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Date',
				fieldname: 'due_date',
				label: 'Due Date',
				default: invoice.due_date
			},
			{
				fieldtype: 'Section Break',
				label: '📝 Additional Information'
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: 'Notes',
				default: invoice.notes
			},
			{
				fieldtype: 'HTML',
				fieldname: 'summary',
				options: `
					<div style="background:#f8f9fa; padding:15px; border-radius:8px; margin-top:15px;">
						<h6>📊 Invoice Summary</h6>
						<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
							<div><strong>Outstanding:</strong> <span id="outstanding-amount">${format_currency((invoice.total_amount || 0) - (invoice.paid_amount || 0))}</span></div>
							<div><strong>Payment Status:</strong> <span id="payment-status">${invoice.payment_status || 'Unpaid'}</span></div>
						</div>
					</div>
				`
			}
		],
		size: 'large',
		primary_action_label: '💾 Save Changes',
		primary_action: function(values) {
			// Calculate outstanding amount
			let outstanding = (values.total_amount || 0) - (values.paid_amount || 0);
			
			// Determine payment status
			let payment_status = 'Unpaid';
			if (values.paid_amount >= values.total_amount) {
				payment_status = 'Paid';
			} else if (values.paid_amount > 0) {
				payment_status = 'Partially Paid';
			}
			
			// Update invoice
			frappe.call({
				method: 'frappe.client.set_value',
				args: {
					doctype: 'Invoice',
					name: invoice.name,
					fieldname: {
						'title': values.title,
						'invoice_status': values.invoice_status,
						'total_amount': values.total_amount,
						'paid_amount': values.paid_amount,
						'outstanding_amount': outstanding,
						'payment_status': payment_status,
						'invoice_date': values.invoice_date,
						'due_date': values.due_date,
						'notes': values.notes
					}
				},
				callback: function(r) {
					if (r.message) {
						d.hide();
						frappe.show_alert({
							message: `Invoice ${invoice.name} updated successfully`,
							indicator: 'green'
						});
						
						// Refresh the invoice section
						render_invoice_section(cur_frm);
					}
				}
			});
		},
		secondary_action_label: '🖨️ Print Invoice',
		secondary_action: function() {
			print_invoice(invoice.name);
		}
	});
	
	// Add real-time calculation
	d.fields_dict.total_amount.$input.on('change', update_invoice_summary);
	d.fields_dict.paid_amount.$input.on('change', update_invoice_summary);
	
	function update_invoice_summary() {
		let total = parseFloat(d.get_value('total_amount') || 0);
		let paid = parseFloat(d.get_value('paid_amount') || 0);
		let outstanding = total - paid;
		
		let payment_status = 'Unpaid';
		if (paid >= total) {
			payment_status = 'Paid';
		} else if (paid > 0) {
			payment_status = 'Partially Paid';
		}
		
		$('#outstanding-amount').text(format_currency(outstanding));
		$('#payment-status').text(payment_status);
	}
	
	d.show();
}

// Helper function to get payment method colors
function get_payment_method_color(method) {
	switch(method) {
		case 'Cash': return '#27ae60';
		case 'Credit Card': return '#3498db';
		case 'Debit Card': return '#9b59b6';
		case 'Check': return '#f39c12';
		case 'Bank Transfer': return '#34495e';
		case 'Online Payment': return '#e74c3c';
		default: return '#95a5a6';
	}
}

// Helper function to get payment status colors
function get_payment_status_color(status) {
	switch(status) {
		case 'Completed':
		case 'Success':
			return {
				bg: 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)',
				border: '#28a745',
				text: '#155724',
				badge: '#28a745'
			};
		case 'Pending':
			return {
				bg: 'linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)',
				border: '#ffc107',
				text: '#856404',
				badge: '#ffc107'
			};
		case 'Failed':
		case 'Cancelled':
			return {
				bg: 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)',
				border: '#dc3545',
				text: '#721c24',
				badge: '#dc3545'
			};
		default:
			return {
				bg: 'linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%)',
				border: '#6c757d',
				text: '#495057',
				badge: '#6c757d'
			};
	}
}

// Quick edit payment function
function edit_payment_quick(payment_name) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Dental Payment Entry',
			name: payment_name
		},
		callback: function(r) {
			if (r.message) {
				let payment = r.message;
				show_payment_edit_dialog(payment);
			}
		}
	});
}

// Show payment edit dialog
function show_payment_edit_dialog(payment) {
	let d = new frappe.ui.Dialog({
		title: `💳 Edit Payment: ${payment.name}`,
		fields: [
			{
				fieldtype: 'Section Break',
				label: '📋 Payment Information'
			},
			{
				fieldtype: 'Link',
				fieldname: 'invoice',
				label: 'Invoice',
				options: 'Invoice',
				default: payment.invoice
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Select',
				fieldname: 'payment_status',
				label: 'Payment Status',
				options: 'Pending\nCompleted\nFailed\nCancelled',
				default: payment.payment_status || 'Completed',
				reqd: 1
			},
			{
				fieldtype: 'Section Break',
				label: '💰 Amount & Method'
			},
			{
				fieldtype: 'Currency',
				fieldname: 'payment_amount',
				label: 'Payment Amount',
				default: payment.payment_amount,
				reqd: 1
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Select',
				fieldname: 'payment_method',
				label: 'Payment Method',
				options: 'Cash\nCredit Card\nDebit Card\nCheck\nBank Transfer\nOnline Payment',
				default: payment.payment_method,
				reqd: 1
			},
			{
				fieldtype: 'Section Break',
				label: '📅 Date & Reference'
			},
			{
				fieldtype: 'Date',
				fieldname: 'payment_date',
				label: 'Payment Date',
				default: payment.payment_date,
				reqd: 1
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldtype: 'Data',
				fieldname: 'reference_number',
				label: 'Reference Number',
				default: payment.reference_number
			},
			{
				fieldtype: 'Section Break',
				label: '📝 Additional Information'
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: 'Notes',
				default: payment.notes
			},
			{
				fieldtype: 'HTML',
				fieldname: 'payment_summary',
				options: `
					<div style="background:#f8f9fa; padding:15px; border-radius:8px; margin-top:15px;">
						<h6>📊 Payment Summary</h6>
						<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
							<div><strong>Patient:</strong> ${payment.patient}</div>
							<div><strong>Created:</strong> ${frappe.datetime.str_to_user(payment.creation)}</div>
						</div>
					</div>
				`
			}
		],
		size: 'large',
		primary_action_label: '💾 Save Changes',
		primary_action: function(values) {
			// Update payment
			frappe.call({
				method: 'frappe.client.set_value',
				args: {
					doctype: 'Dental Payment Entry',
					name: payment.name,
					fieldname: {
						'invoice': values.invoice,
						'payment_status': values.payment_status,
						'payment_amount': values.payment_amount,
						'payment_method': values.payment_method,
						'payment_date': values.payment_date,
						'reference_number': values.reference_number,
						'notes': values.notes
					}
				},
				callback: function(r) {
					if (r.message) {
						d.hide();
						frappe.show_alert({
							message: `Payment ${payment.name} updated successfully`,
							indicator: 'green'
						});
						
						// Refresh both payment and invoice sections
						render_payment_section(cur_frm);
						render_invoice_section(cur_frm);
					}
				}
			});
		},
		secondary_action_label: '🗑️ Delete Payment',
		secondary_action: function() {
			frappe.confirm(
				`Are you sure you want to delete payment ${payment.name}?`,
				function() {
					frappe.call({
						method: 'frappe.client.delete',
						args: {
							doctype: 'Dental Payment Entry',
							name: payment.name
						},
						callback: function(r) {
							d.hide();
							frappe.show_alert({
								message: `Payment ${payment.name} deleted successfully`,
								indicator: 'red'
							});
							
							// Refresh both sections
							render_payment_section(cur_frm);
							render_invoice_section(cur_frm);
						}
					});
				}
			);
		}
	});
	
	d.show();
}

// Helper function to show invoice action buttons
function show_invoice_actions(invoice_name, frm) {
	// Create a temporary dialog with action buttons
	let action_dialog = new frappe.ui.Dialog({
		title: __('Invoice Created'),
		fields: [
			{
				fieldname: 'message',
				fieldtype: 'HTML',
				options: `
					<div class="text-center" style="padding: 20px;">
						<p><strong>Invoice ${invoice_name} has been created successfully!</strong></p>
						<p>What would you like to do next?</p>
					</div>
				`
			}
		],
		primary_action_label: __('View Invoice'),
		primary_action: function() {
			action_dialog.hide();
			frappe.set_route('Form', 'Invoice', invoice_name);
		},
		secondary_action_label: __('Print Invoice'),
		secondary_action: function() {
			print_invoice(invoice_name);
		}
	});
	
	// Add a "Stay Here" button
	action_dialog.$wrapper.find('.modal-footer').prepend(`
		<button class="btn btn-default btn-sm" onclick="$('.modal').modal('hide')">
			${__('Stay on Dental Chart')}
		</button>
	`);
	
	action_dialog.show();
	
	// Auto-hide after 10 seconds if user doesn't interact
	setTimeout(() => {
		if (action_dialog.display) {
			action_dialog.hide();
		}
	}, 10000);
}