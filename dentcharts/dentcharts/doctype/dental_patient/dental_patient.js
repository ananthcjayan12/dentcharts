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
			
			// Add dental chart button with actual functionality
			frm.add_custom_button(__('Dental Chart'), function() {
				// Check if patient has existing dental charts
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Dental Chart',
						filters: {
							patient: frm.doc.healthcare_patient
						},
						fields: ['name', 'chart_date', 'status', 'dentist_name'],
						order_by: 'chart_date desc',
						limit: 1
					},
					callback: function(r) {
						if (r.message && r.message.length > 0) {
							// Patient has existing charts, show options
							let d = new frappe.ui.Dialog({
								title: __('Dental Chart Options'),
								fields: [
									{
										fieldtype: 'HTML',
										options: `<p><strong>Latest Chart:</strong> ${r.message[0].name} (${frappe.datetime.str_to_user(r.message[0].chart_date)})</p>
												 <p><strong>Status:</strong> ${r.message[0].status}</p>
												 <p><strong>Dentist:</strong> ${r.message[0].dentist_name || 'Not specified'}</p>`
									}
								],
								primary_action_label: __('View Latest Chart'),
								primary_action: function() {
									frappe.set_route('Form', 'Dental Chart', r.message[0].name);
									d.hide();
								}
							});
							
							// Add custom buttons for other actions
							d.set_secondary_action_label(__('Create New Chart'));
							d.set_secondary_action(function() {
								frm.create_new_dental_chart();
								d.hide();
							});
							
							// Add third button manually
							d.$wrapper.find('.modal-footer').prepend(`
								<button class="btn btn-default btn-sm" id="view-all-charts-btn">
									${__('View All Charts')}
								</button>
							`);
							
							d.$wrapper.find('#view-all-charts-btn').click(function() {
								frappe.set_route('List', 'Dental Chart', {
									patient: frm.doc.healthcare_patient
								});
								d.hide();
							});
							
							d.show();
						} else {
							// No existing charts, create new one
							frm.create_new_dental_chart();
						}
					}
				});
			});
		}
	},
	
	create_new_dental_chart: function(frm) {
		// Show dialog to choose dentition type
		let d = new frappe.ui.Dialog({
			title: __('Create New Dental Chart'),
			fields: [
				{
					fieldtype: 'Select',
					fieldname: 'dentition_type',
					label: __('Dentition Type'),
					options: ['Permanent', 'Primary', 'Mixed'],
					default: 'Permanent',
					reqd: 1,
					description: __('Select the type of teeth to chart:<br>• Permanent: Adult teeth (32 teeth)<br>• Primary: Baby teeth (20 teeth)<br>• Mixed: Both permanent and primary teeth')
				},
				{
					fieldtype: 'Select',
					fieldname: 'chart_type',
					label: __('Chart Type'),
					options: ['Comprehensive', 'Limited Exam', 'Emergency', 'Follow-up', 'Consultation'],
					default: 'Comprehensive',
					reqd: 1
				}
			],
			primary_action_label: __('Create Chart'),
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
						
						// Create new dental chart with selected dentition type
						frappe.new_doc('Dental Chart', {
							patient: frm.doc.healthcare_patient,
							patient_name: frm.doc.patient_name,
							dentist: default_dentist,
							chart_date: frappe.datetime.nowdate(),
							status: 'Draft',
							dentition_type: values.dentition_type,
							chart_type: values.chart_type
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