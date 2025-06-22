// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Appointment', {
	refresh: function(frm) {
		// Add custom buttons based on appointment status
		add_custom_buttons(frm);
		
		// Set field properties
		set_field_properties(frm);
		
		// Auto-refresh every 5 minutes for real-time updates
		if (frm.doc.status === "In Progress") {
			setTimeout(() => frm.reload_doc(), 300000);
		}
	},
	
	onload: function(frm) {
		// Set default values for new appointments
		if (frm.is_new()) {
			set_default_values(frm);
		}
		
		// Set filters for link fields
		set_link_filters(frm);
	},
	
	patient: function(frm) {
		// Auto-populate patient-related fields
		if (frm.doc.patient) {
			get_patient_details(frm);
		}
	},
	
	practitioner: function(frm) {
		// Auto-populate practitioner-related fields
		if (frm.doc.practitioner) {
			get_practitioner_details(frm);
		}
	},
	
	appointment_date: function(frm) {
		// Check availability when date changes
		if (frm.doc.appointment_date && frm.doc.practitioner) {
			check_practitioner_availability(frm);
		}
	},
	
	appointment_time: function(frm) {
		// Validate time slot availability
		if (frm.doc.appointment_time && frm.doc.practitioner && frm.doc.appointment_date) {
			validate_time_slot(frm);
		}
	},
	
	appointment_type: function(frm) {
		// Set default duration based on appointment type
		set_default_duration(frm);
	},
	
	dental_chart: function(frm) {
		// Load chart procedures when chart is selected
		if (frm.doc.dental_chart) {
			load_chart_procedures(frm);
		}
	}
});

// Child table events for planned procedures
frappe.ui.form.on('Appointment Procedure', {
	procedure_code: function(frm, cdt, cdn) {
		// Auto-populate procedure details
		var row = locals[cdt][cdn];
		if (row.procedure_code) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Dental Procedure Master',
					name: row.procedure_code
				},
				callback: function(r) {
					if (r.message) {
						var procedure = r.message;
						frappe.model.set_value(cdt, cdn, 'estimated_duration', procedure.duration_minutes);
						frappe.model.set_value(cdt, cdn, 'estimated_cost', procedure.standard_fee);
						
						// Refresh totals
						calculate_appointment_totals(frm);
					}
				}
			});
		}
	},
	
	planned_procedures_remove: function(frm) {
		// Recalculate totals when procedure is removed
		calculate_appointment_totals(frm);
	}
});

function add_custom_buttons(frm) {
	// Clear existing custom buttons
	frm.custom_buttons = {};
	
	if (frm.doc.status === "Scheduled") {
		frm.add_custom_button(__('Confirm'), function() {
			confirm_appointment(frm);
		}, __('Actions'));
		
		frm.add_custom_button(__('Cancel'), function() {
			cancel_appointment(frm);
		}, __('Actions'));
		
		frm.add_custom_button(__('Reschedule'), function() {
			reschedule_appointment(frm);
		}, __('Actions'));
	}
	
	if (frm.doc.status === "Confirmed") {
		frm.add_custom_button(__('Start Appointment'), function() {
			start_appointment(frm);
		}, __('Actions'));
		
		frm.add_custom_button(__('Mark No Show'), function() {
			mark_no_show(frm);
		}, __('Actions'));
	}
	
	if (frm.doc.status === "In Progress") {
		frm.add_custom_button(__('Complete'), function() {
			complete_appointment(frm);
		}, __('Actions'));
	}
	
	// Always available buttons
	frm.add_custom_button(__('Send Reminder'), function() {
		send_reminder(frm);
	}, __('Communications'));
	
	frm.add_custom_button(__('View Schedule'), function() {
		view_practitioner_schedule(frm);
	}, __('View'));
	
	if (frm.doc.dental_chart) {
		frm.add_custom_button(__('Open Dental Chart'), function() {
			frappe.set_route('Form', 'Dental Chart', frm.doc.dental_chart);
		}, __('View'));
	}
}

function set_field_properties(frm) {
	// Make certain fields read-only based on status
	if (frm.doc.status === "Completed" || frm.doc.status === "Cancelled") {
		frm.set_df_property('appointment_date', 'read_only', 1);
		frm.set_df_property('appointment_time', 'read_only', 1);
		frm.set_df_property('practitioner', 'read_only', 1);
		frm.set_df_property('patient', 'read_only', 1);
	}
	
	// Show/hide fields based on status
	frm.toggle_display('cancellation_reason', frm.doc.status === 'Cancelled');
	frm.toggle_display('follow_up_appointment', frm.doc.follow_up_appointment);
	
	// Set field colors based on priority
	if (frm.doc.priority === "Urgent") {
		frm.set_df_property('priority', 'color', 'Red');
	} else if (frm.doc.priority === "High") {
		frm.set_df_property('priority', 'color', 'Orange');
	}
}

function set_default_values(frm) {
	// Set default appointment date to tomorrow
	var tomorrow = frappe.datetime.add_days(frappe.datetime.get_today(), 1);
	frm.set_value('appointment_date', tomorrow);
	
	// Set default time to 9 AM
	frm.set_value('appointment_time', '09:00:00');
	
	// Set default duration
	frm.set_value('duration_minutes', 60);
}

function set_link_filters(frm) {
	// Filter practitioners to only show active dental practitioners
	frm.set_query('practitioner', function() {
		return {
			filters: {
				'status': 'Active'
			}
		};
	});
	
	// Filter patients to only show active patients
	frm.set_query('patient', function() {
		return {
			filters: {
				'status': 'Active'
			}
		};
	});
	
	// Filter dental charts to only show charts for the selected patient
	frm.set_query('dental_chart', function() {
		if (frm.doc.patient) {
			return {
				filters: {
					'patient': frm.doc.patient
				}
			};
		}
	});
	
	// Filter procedure codes to only show active procedures
	frm.set_query('procedure_code', 'planned_procedures', function() {
		return {
			filters: {
				'is_active': 1
			}
		};
	});
}

function get_patient_details(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Patient',
			name: frm.doc.patient
		},
		callback: function(r) {
			if (r.message) {
				// Auto-populate dental chart if exists
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Dental Chart',
						filters: {
							'patient': frm.doc.patient
						},
						limit: 1,
						order_by: 'creation desc'
					},
					callback: function(chart_response) {
						if (chart_response.message && chart_response.message.length > 0) {
							frm.set_value('dental_chart', chart_response.message[0].name);
						}
					}
				});
			}
		}
	});
}

function get_practitioner_details(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Healthcare Practitioner',
			name: frm.doc.practitioner
		},
		callback: function(r) {
			if (r.message) {
				// Get dental practitioner details for consultation fee
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Dental Practitioner',
						filters: {
							'healthcare_practitioner': frm.doc.practitioner
						},
						fields: ['consultation_fee', 'dental_clinic']
					},
					callback: function(dental_response) {
						if (dental_response.message && dental_response.message.length > 0) {
							var dental_practitioner = dental_response.message[0];
							if (dental_practitioner.dental_clinic) {
								frm.set_value('dental_clinic', dental_practitioner.dental_clinic);
							}
						}
					}
				});
			}
		}
	});
}

function check_practitioner_availability(frm) {
	frappe.call({
		method: 'dentcharts.dentcharts.doctype.dental_appointment.dental_appointment.DentalAppointment.get_available_time_slots',
		args: {
			practitioner: frm.doc.practitioner,
			date: frm.doc.appointment_date,
			duration: frm.doc.duration_minutes || 60
		},
		callback: function(r) {
			if (r.message) {
				var available_slots = r.message;
				if (available_slots.length === 0) {
					frappe.msgprint(__('No available time slots for this practitioner on the selected date.'));
				} else {
					// Show available slots in a dialog
					show_available_slots_dialog(frm, available_slots);
				}
			}
		}
	});
}

function show_available_slots_dialog(frm, available_slots) {
	var dialog = new frappe.ui.Dialog({
		title: __('Available Time Slots'),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'slots_html'
			}
		]
	});
	
	var html = '<div class="available-slots">';
	available_slots.forEach(function(slot) {
		html += `<div class="slot-item" style="padding: 10px; margin: 5px; border: 1px solid #ccc; cursor: pointer;" 
				 data-time="${slot.start_time}">
				 ${slot.start_time} - ${slot.end_time}
				 </div>`;
	});
	html += '</div>';
	
	dialog.fields_dict.slots_html.$wrapper.html(html);
	
	// Add click handlers
	dialog.fields_dict.slots_html.$wrapper.find('.slot-item').click(function() {
		var selected_time = $(this).data('time');
		frm.set_value('appointment_time', selected_time);
		dialog.hide();
	});
	
	dialog.show();
}

function set_default_duration(frm) {
	var duration_map = {
		'Consultation': 30,
		'Routine Checkup': 45,
		'Cleaning': 60,
		'Filling': 90,
		'Root Canal': 120,
		'Extraction': 60,
		'Emergency': 30,
		'Follow-up': 30,
		'Cosmetic': 90,
		'Orthodontic': 45
	};
	
	if (frm.doc.appointment_type && duration_map[frm.doc.appointment_type]) {
		frm.set_value('duration_minutes', duration_map[frm.doc.appointment_type]);
	}
}

function calculate_appointment_totals(frm) {
	var total_duration = 0;
	var total_cost = 0;
	
	frm.doc.planned_procedures.forEach(function(procedure) {
		if (procedure.estimated_duration) {
			total_duration += procedure.estimated_duration;
		}
		if (procedure.estimated_cost) {
			total_cost += procedure.estimated_cost;
		}
	});
	
	frm.set_value('duration_minutes', total_duration || 60);
	frm.set_value('estimated_cost', total_cost);
	frm.set_value('patient_portion', total_cost * 0.3); // 30% patient portion
}

function confirm_appointment(frm) {
	frappe.call({
		method: 'confirm_appointment',
		doc: frm.doc,
		callback: function(r) {
			frm.reload_doc();
			frappe.show_alert(__('Appointment confirmed successfully'));
		}
	});
}

function cancel_appointment(frm) {
	frappe.prompt('Cancellation Reason', function(data) {
		frappe.call({
			method: 'cancel_appointment',
			doc: frm.doc,
			args: {
				reason: data.value
			},
			callback: function(r) {
				frm.reload_doc();
				frappe.show_alert(__('Appointment cancelled'));
			}
		});
	});
}

function start_appointment(frm) {
	frm.set_value('status', 'In Progress');
	frm.save();
}

function complete_appointment(frm) {
	frappe.call({
		method: 'mark_completed',
		doc: frm.doc,
		callback: function(r) {
			frm.reload_doc();
			frappe.show_alert(__('Appointment completed successfully'));
		}
	});
}

function mark_no_show(frm) {
	frappe.call({
		method: 'mark_no_show',
		doc: frm.doc,
		callback: function(r) {
			frm.reload_doc();
			frappe.show_alert(__('Appointment marked as No Show'));
		}
	});
}

function send_reminder(frm) {
	frappe.call({
		method: 'send_reminder_notification',
		doc: frm.doc,
		callback: function(r) {
			frappe.show_alert(__('Reminder sent successfully'));
		}
	});
}

function view_practitioner_schedule(frm) {
	if (frm.doc.practitioner && frm.doc.appointment_date) {
		frappe.route_options = {
			"practitioner": frm.doc.practitioner,
			"appointment_date": frm.doc.appointment_date
		};
		frappe.set_route("query-report", "Practitioner Schedule");
	}
} 