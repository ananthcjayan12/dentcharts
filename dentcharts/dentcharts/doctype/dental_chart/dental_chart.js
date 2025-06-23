// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Chart', {
	refresh: function(frm) {
		// Show interactive dental chart
		if (!frm.is_new()) {
			// Remove old chart if exists
			frm.dashboard.clear_headline();
			
			// Create interactive dental chart
			create_interactive_dental_chart(frm);
			
			// Add traditional buttons as fallback
			frm.add_custom_button(__('Add Condition (Manual)'), function() {
				add_tooth_condition(frm);
			});
			
			frm.add_custom_button(__('Add Procedure (Manual)'), function() {
				add_tooth_procedure(frm);
			});
		}
		
		// Show dentition type info
		if (frm.doc.dentition_type) {
			frm.set_df_property('dentition_type', 'description', get_dentition_description(frm.doc.dentition_type));
		}
	},
	
	dentition_type: function(frm) {
		// Update description when dentition type changes
		frm.set_df_property('dentition_type', 'description', get_dentition_description(frm.doc.dentition_type));
		
		// Clear existing conditions and procedures if dentition type changes
		if (!frm.is_new() && frm.doc.tooth_conditions && frm.doc.tooth_conditions.length > 0) {
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
	
	after_save: function(frm) {
		// Refresh interactive chart after saving
		if (!frm.is_new()) {
			setTimeout(() => {
				create_interactive_dental_chart(frm);
			}, 500);
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
				
				// Add chart to the form
				frm.dashboard.add_section(chart_html, __('Interactive Dental Chart'));
			}
		}
	});
}

function build_interactive_chart_html(frm, chart_data) {
	let html = `
		<div class="dental-chart-container" style="background: white; padding: 20px; border: 1px solid #d1d8dd; border-radius: 6px; margin: 10px 0;">
			<div style="text-align: center; margin-bottom: 20px;">
				<h4>${chart_data.patient} - ${chart_data.dentition_type} Dentition Chart</h4>
				<p style="color: #6c757d; margin-bottom: 15px;">Click on any tooth to add conditions or procedures</p>
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

	// Add click handlers after DOM is ready
	setTimeout(() => {
		attach_tooth_click_handlers(frm);
	}, 100);

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
					position: relative;"
			 onmouseover="this.style.transform='scale(1.1)'; this.style.zIndex='10';"
			 onmouseout="this.style.transform='scale(1)'; this.style.zIndex='1';"
			 title="Click to add condition or procedure to tooth ${tooth_number}">
			<div>${tooth_number}</div>
			${has_conditions ? '<div style="color: #dc3545; font-size: 10px;">🦷</div>' : ''}
			${has_procedures ? '<div style="color: #007bff; font-size: 10px;">🔧</div>' : ''}
		</div>
	`;
}

function attach_tooth_click_handlers(frm) {
	$(document).off('click', '.tooth-element');
	$(document).on('click', '.tooth-element', function() {
		let tooth_number = $(this).data('tooth');
		show_tooth_action_dialog(frm, tooth_number);
	});
}

function show_tooth_action_dialog(frm, tooth_number) {
	// Refresh form to ensure we have latest data
	frm.refresh_fields();
	
	// Get existing conditions and procedures for this tooth
	// Debug: Log the data to console
	console.log('Selected tooth:', tooth_number);
	console.log('All conditions:', frm.doc.tooth_conditions);
	console.log('All procedures:', frm.doc.tooth_procedures);
	
	let existing_conditions = (frm.doc.tooth_conditions || []).filter(c => {
		console.log('Checking condition tooth:', c.tooth_number, 'against:', tooth_number);
		// Handle both direct match and string conversion, also check if it's a link field
		return c.tooth_number === tooth_number || 
			   c.tooth_number === tooth_number.toString() ||
			   (c.tooth_number && c.tooth_number.toString() === tooth_number.toString());
	});
	let existing_procedures = (frm.doc.tooth_procedures || []).filter(p => {
		console.log('Checking procedure tooth:', p.tooth_number, 'against:', tooth_number);
		// Handle both direct match and string conversion, also check if it's a link field
		return p.tooth_number === tooth_number || 
			   p.tooth_number === tooth_number.toString() ||
			   (p.tooth_number && p.tooth_number.toString() === tooth_number.toString());
	});
	
	console.log('Filtered conditions:', existing_conditions);
	console.log('Filtered procedures:', existing_procedures);
	
	let tooth_info_html = `
		<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
			<h5 style="margin: 0 0 10px 0; color: #495057;">Tooth ${tooth_number}</h5>
			${existing_conditions.length > 0 ? `
				<p style="margin: 5px 0;"><strong>🦷 Existing Conditions (${existing_conditions.length}):</strong></p>
				<ul style="margin: 5px 0 10px 20px; padding: 0;">
					${existing_conditions.map(c => `
						<li style="margin: 5px 0; padding: 5px; background: #fff3cd; border-radius: 3px;">
							<strong>${c.condition_code || 'Unknown'}</strong> 
							${c.condition_name ? `(${c.condition_name})` : ''} - ${c.surface || 'Unknown Surface'}
							${c.severity ? `<br><small>Severity: ${c.severity}</small>` : ''}
							${c.date_identified ? `<br><small>Date: ${c.date_identified}</small>` : ''}
						</li>
					`).join('')}
				</ul>
			` : '<p style="margin: 5px 0; color: #6c757d;">No existing conditions</p>'}
			
			${existing_procedures.length > 0 ? `
				<p style="margin: 5px 0;"><strong>🔧 Existing Procedures (${existing_procedures.length}):</strong></p>
				<ul style="margin: 5px 0 10px 20px; padding: 0;">
					${existing_procedures.map(p => `
						<li style="margin: 5px 0; padding: 5px; background: #d1ecf1; border-radius: 3px;">
							<strong>${p.procedure_code || 'Unknown'}</strong> 
							${p.procedure_name ? `(${p.procedure_name})` : ''} - ${p.surface || 'Unknown Surface'}
							<span style="float: right; font-weight: bold; color: ${p.status === 'Completed' ? '#28a745' : p.status === 'In Progress' ? '#007bff' : '#6c757d'};">
								${p.status || 'Unknown'}
							</span>
							${p.planned_date ? `<br><small>Planned: ${p.planned_date}</small>` : ''}
							${p.completed_date ? `<br><small>Completed: ${p.completed_date}</small>` : ''}
						</li>
					`).join('')}
				</ul>
			` : '<p style="margin: 5px 0; color: #6c757d;">No existing procedures</p>'}
		</div>
	`;

	let d = new frappe.ui.Dialog({
		title: __('Tooth Actions - ') + tooth_number,
		fields: [
			{
				fieldtype: 'HTML',
				options: tooth_info_html
			},
			{
				fieldtype: 'Section Break',
				label: __('Actions')
			}
		],
		primary_action_label: __('Add Condition'),
		primary_action: function() {
			d.hide();
			add_tooth_condition_for_tooth(frm, tooth_number);
		}
	});

	// Add procedure button using the correct method
	d.set_secondary_action_label(__('Add Procedure'));
	d.set_secondary_action(function() {
		d.hide();
		add_tooth_procedure_for_tooth(frm, tooth_number);
	});

	// Add view details button if there are existing items
	if (existing_conditions.length > 0 || existing_procedures.length > 0) {
		d.$wrapper.find('.modal-footer').prepend(`
			<button class="btn btn-default btn-sm" id="view-tooth-details-btn">
				${__('View Details')}
			</button>
		`);
		
		d.$wrapper.find('#view-tooth-details-btn').click(function() {
			d.hide();
			show_tooth_details(frm, tooth_number, existing_conditions, existing_procedures);
		});
	}

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
			procedure_row.tooth_number = selected_tooth;
			procedure_row.procedure_code = values.procedure_code;
			procedure_row.surface = values.surface;
			procedure_row.status = values.status;
			procedure_row.notes = values.notes;
			procedure_row.planned_date = frappe.datetime.nowdate();
			procedure_row.planned_by = frappe.session.user;
			
			frm.refresh_field('tooth_procedures');
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