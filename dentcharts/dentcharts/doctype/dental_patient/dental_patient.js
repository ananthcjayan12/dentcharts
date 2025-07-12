// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Patient', {
	refresh: function(frm) {
		// Add custom buttons for existing patients only
		if (!frm.is_new() && frm.doc.healthcare_patient) {
			
			// Dental Chart Button - Primary Action
			frm.add_custom_button(__('🦷 Dental Chart'), function() {
				frm.open_dental_chart();
			}, __('Quick Actions'));
			
			// Schedule Appointment Button
			frm.add_custom_button(__('📅 Schedule Appointment'), function() {
				frm.schedule_appointment();
			}, __('Quick Actions'));
			
			// View Healthcare Patient Button
			frm.add_custom_button(__('👤 View Patient'), function() {
				frappe.set_route('Form', 'Patient', frm.doc.healthcare_patient);
			}, __('Quick Actions'));
			
			// Create Treatment Plan Button
			frm.add_custom_button(__('📋 Treatment Plan'), function() {
				frm.create_treatment_plan();
			}, __('Quick Actions'));
			
			// View Appointments Button
			frm.add_custom_button(__('📋 View Appointments'), function() {
				frm.view_appointments();
			}, __('Quick Actions'));
			
			// Create Invoice Button
			frm.add_custom_button(__('💰 Create Invoice'), function() {
				frm.create_invoice();
			}, __('Quick Actions'));
		}
	},
	
	open_dental_chart: function(frm) {
		// Check if patient has existing dental charts
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Dental Chart',
				filters: {
					patient: frm.doc.healthcare_patient
				},
				fields: ['name', 'chart_date', 'status', 'chart_type', 'dentist_name'],
				order_by: 'creation desc',
				limit: 10
			},
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					// Show chart selection dialog
					frm.show_chart_selection_dialog(r.message);
				} else {
					// No charts exist, create master chart
					frm.create_master_dental_chart();
				}
			}
		});
	},
	
	show_chart_selection_dialog: function(frm, charts) {
		let chart_options = charts.map(chart => 
			`${chart.chart_type} - ${chart.chart_date} (${chart.status})`
		).join('\n');
		
		let d = new frappe.ui.Dialog({
			title: __('Select Dental Chart'),
			fields: [
				{
					fieldtype: 'HTML',
					options: `<div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
						<h5 style="margin: 0 0 10px 0; color: #1565c0;">🦷 Dental Charts for ${frm.doc.patient_name}</h5>
						<p style="margin: 0; color: #424242;">Select a chart to view or create a new one.</p>
					</div>`
				},
				{
					fieldtype: 'Select',
					fieldname: 'selected_chart',
					label: __('Existing Charts'),
					options: charts.map(chart => chart.name).join('\n'),
					description: __('Choose an existing chart to view')
				},
				{
					fieldtype: 'Button',
					fieldname: 'create_new',
					label: __('Create New Chart'),
					description: __('Create a new dental chart')
				}
			],
			primary_action_label: __('Open Chart'),
			primary_action: function(values) {
				if (values.selected_chart) {
					frappe.set_route('Form', 'Dental Chart', values.selected_chart);
				}
				d.hide();
			},
			secondary_action_label: __('Cancel'),
			secondary_action: function() {
				d.hide();
			}
		});
		
		// Handle create new button
		d.fields_dict.create_new.$wrapper.on('click', function() {
			d.hide();
			frm.create_master_dental_chart();
		});
		
		d.show();
	},
	
	create_master_dental_chart: function(frm) {
		let d = new frappe.ui.Dialog({
			title: __('Create Dental Chart'),
			fields: [
				{
					fieldtype: 'HTML',
					options: `<div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
						<h5 style="margin: 0 0 10px 0; color: #2e7d32;">🦷 New Dental Chart</h5>
						<p style="margin: 0; color: #424242;">Creating a new dental chart for ${frm.doc.patient_name}</p>
					</div>`
				},
				{
					fieldtype: 'Select',
					fieldname: 'chart_type',
					label: __('Chart Type'),
					options: 'Master Chart\nComprehensive\nLimited Exam\nEmergency\nFollow-up\nConsultation',
					default: 'Master Chart',
					reqd: 1
				},
				{
					fieldtype: 'Select',
					fieldname: 'dentition_type',
					label: __('Dentition Type'),
					options: 'Permanent\nPrimary\nMixed',
					default: 'Permanent',
					reqd: 1
				},
				{
					fieldtype: 'Link',
					fieldname: 'dentist',
					label: __('Dentist'),
					options: 'Healthcare Practitioner',
					description: __('Select the treating dentist')
				},
				{
					fieldtype: 'Small Text',
					fieldname: 'chief_complaint',
					label: __('Chief Complaint'),
					default: frm.doc.chief_complaint || '',
					description: __('Patient\'s main complaint')
				}
			],
			primary_action_label: __('Create Chart'),
			primary_action: function(values) {
				// Create the dental chart
				frappe.new_doc('Dental Chart', {
					patient: frm.doc.healthcare_patient,
					patient_name: frm.doc.patient_name,
					chart_type: values.chart_type,
					dentition_type: values.dentition_type,
					dentist: values.dentist,
					chief_complaint: values.chief_complaint,
					status: 'Active',
					chart_date: frappe.datetime.nowdate()
				});
				d.hide();
			},
			secondary_action_label: __('Cancel'),
			secondary_action: function() {
				d.hide();
			}
		});
		d.show();
	},
	
	schedule_appointment: function(frm) {
		// Create new dental appointment
		frappe.new_doc('Dental Appointment', {
			patient: frm.doc.healthcare_patient,
			patient_name: frm.doc.patient_name,
			appointment_date: frappe.datetime.add_days(frappe.datetime.nowdate(), 1),
			appointment_type: 'Consultation',
			priority: 'Medium'
		});
	},
	
	create_treatment_plan: function(frm) {
		// Create new treatment plan
		frappe.new_doc('Treatment Plan', {
			patient: frm.doc.healthcare_patient,
			patient_name: frm.doc.patient_name,
			plan_date: frappe.datetime.nowdate(),
			plan_status: 'Draft'
		});
	},
	
	view_appointments: function(frm) {
		// Open list view of appointments for this patient
		frappe.set_route('List', 'Dental Appointment', {
			patient: frm.doc.healthcare_patient
		});
	},
	
	create_invoice: function(frm) {
		// Create new invoice
		frappe.new_doc('Invoice', {
			patient: frm.doc.healthcare_patient,
			patient_name: frm.doc.patient_name,
			invoice_date: frappe.datetime.nowdate(),
			due_date: frappe.datetime.add_days(frappe.datetime.nowdate(), 30)
		});
	},
	
	validate: function(frm) {
		// Additional client-side validation
		if (frm.doc.date_of_registration) {
			let today = new Date();
			let registration_date = new Date(frm.doc.date_of_registration);
			if (registration_date > today) {
				frappe.msgprint(__('Date of Registration cannot be in the future'));
				return false;
			}
		}
		
		if (frm.doc.source && frm.doc.source.trim() === '') {
			frappe.msgprint(__('Source cannot be empty if provided'));
			return false;
		}
	},
	
	healthcare_patient: function(frm) {
		// Fetch patient name when healthcare patient is selected
		if (frm.doc.healthcare_patient) {
			frappe.db.get_value('Patient', frm.doc.healthcare_patient, 'patient_name')
				.then(r => {
					if (r.message) {
						frm.set_value('patient_name', r.message.patient_name);
					}
				});
		}
	},
	
	emergency_phone: function(frm) {
		// Validate emergency phone number
		if (frm.doc.emergency_phone && frm.doc.emergency_phone.length < 10) {
			frappe.msgprint(__('Please enter a valid emergency phone number'));
		}
	},
	
	date_of_registration: function(frm) {
		// Validate date of registration
		if (frm.doc.date_of_registration) {
			let today = new Date();
			let registration_date = new Date(frm.doc.date_of_registration);
			if (registration_date > today) {
				frappe.msgprint(__('Date of Registration cannot be in the future'));
				frm.set_value('date_of_registration', '');
			}
		}
	},
	
	source: function(frm) {
		// Validate source field is not empty
		if (frm.doc.source && frm.doc.source.trim() === '') {
			frappe.msgprint(__('Source cannot be empty if provided'));
			frm.set_value('source', '');
		}
	},
	
	chief_complaint: function(frm) {
		// Auto-save chief complaint to linked dental chart if available
		if (frm.doc.chief_complaint && frm.doc.healthcare_patient) {
			// This will be handled server-side when the chart is created
		}
	}
}); 