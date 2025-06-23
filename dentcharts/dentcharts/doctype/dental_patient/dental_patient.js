// Copyright (c) 2024, Ananthu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Patient', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.is_new()) {
			frm.add_custom_button(__('View Healthcare Patient'), function() {
				frappe.set_route('Form', 'Patient', frm.doc.healthcare_patient);
			});
			
			frm.add_custom_button(__('Create Appointment'), function() {
				frappe.new_doc('Patient Appointment', {
					patient: frm.doc.healthcare_patient,
					patient_name: frm.doc.patient_name
				});
			});
			
			// Add dental chart button with master chart functionality
			frm.add_custom_button(__('Dental Chart'), function() {
				// Check if patient has existing master dental chart
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Dental Chart',
						filters: {
							patient: frm.doc.healthcare_patient
						},
						fields: ['name', 'chart_date', 'status', 'dentist_name', 'creation'],
						order_by: 'creation asc',
						limit: 1
					},
					callback: function(r) {
						if (r.message && r.message.length > 0) {
							// Patient has master chart, open it directly
							frappe.set_route('Form', 'Dental Chart', r.message[0].name);
						} else {
							// No existing chart, create master chart
							frm.create_master_dental_chart();
						}
					}
				});
			});
		}
	},
	
	create_master_dental_chart: function(frm) {
		// Show dialog to choose dentition type for master chart
		let d = new frappe.ui.Dialog({
			title: __('Create Master Dental Chart'),
			fields: [
				{
					fieldtype: 'HTML',
					options: `<div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
						<h5 style="margin: 0 0 10px 0; color: #1565c0;">📋 Master Dental Chart</h5>
						<p style="margin: 0; color: #424242;">This will create a permanent dental chart for ${frm.doc.patient_name}. 
						All future visits and treatments will be recorded in this single chart.</p>
					</div>`
				},
				{
					fieldtype: 'Select',
					fieldname: 'dentition_type',
					label: __('Patient\'s Dentition Type'),
					options: ['Permanent', 'Primary', 'Mixed'],
					default: 'Permanent',
					reqd: 1,
					description: __('• Permanent: Adult teeth (32 teeth)<br>• Primary: Children with baby teeth (20 teeth)<br>• Mixed: Children with both baby and adult teeth')
				}
			],
			primary_action_label: __('Create Master Chart'),
			primary_action: function(values) {
				// Get default dentist if available
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Healthcare Practitioner',
						filters: {
							department: ['like', '%dent%']
						},
						fields: ['name', 'practitioner_name'],
						limit: 1
					},
					callback: function(r) {
						let default_dentist = r.message && r.message.length > 0 ? r.message[0].name : '';
						
						// Create master dental chart
						frappe.new_doc('Dental Chart', {
							patient: frm.doc.healthcare_patient,
							patient_name: frm.doc.patient_name,
							dentist: default_dentist,
							chart_date: frappe.datetime.nowdate(),
							status: 'Active',
							dentition_type: values.dentition_type,
							chart_type: 'Master Chart'
						});
					}
				});
				d.hide();
			}
		});
		d.show();
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
	}
}); 