frappe.ui.form.on('Treatment Plan', {
	refresh: function(frm) {
		// Add custom buttons based on plan status
		if (frm.doc.plan_status === 'Draft') {
			frm.add_custom_button(__('Activate Plan'), function() {
				frm.call('activate_plan').then(() => {
					frm.refresh();
				});
			}).addClass('btn-primary');
		}
		
		if (frm.doc.plan_status === 'Active' || frm.doc.plan_status === 'In Progress') {
			frm.add_custom_button(__('Complete Plan'), function() {
				frm.call('complete_plan').then(() => {
					frm.refresh();
				});
			}).addClass('btn-success');
			
			frm.add_custom_button(__('Cancel Plan'), function() {
				frappe.prompt('Cancellation Reason', function(data) {
					frm.call('cancel_plan', {
						reason: data.value
					}).then(() => {
						frm.refresh();
					});
				});
			}).addClass('btn-danger');
		}
		
		// Add button to generate from dental chart
		if (frm.doc.dental_chart && frm.doc.plan_status === 'Draft') {
			frm.add_custom_button(__('Generate from Chart'), function() {
				frm.call('generate_from_dental_chart', {
					dental_chart_name: frm.doc.dental_chart
				}).then(() => {
					frm.refresh();
				});
			});
		}
		
		// Add progress indicator
		if (frm.doc.plan_progress !== undefined) {
			frm.dashboard.add_progress(__('Treatment Progress'), frm.doc.plan_progress);
		}
		
		// Color-code status
		if (frm.doc.plan_status) {
			const status_colors = {
				'Draft': 'grey',
				'Active': 'blue',
				'In Progress': 'orange',
				'Completed': 'green',
				'Cancelled': 'red',
				'On Hold': 'yellow'
			};
			frm.add_custom_button(frm.doc.plan_status, null, status_colors[frm.doc.plan_status]);
		}
	},
	
	patient: function(frm) {
		// Auto-link dental chart when patient is selected
		if (frm.doc.patient) {
			frappe.db.get_value('Dental Chart', {'patient': frm.doc.patient}, 'name').then(r => {
				if (r.message && r.message.name) {
					frm.set_value('dental_chart', r.message.name);
				}
			});
		}
	},
	
	insurance_coverage_percentage: function(frm) {
		// Recalculate totals when insurance coverage changes
		calculate_plan_totals(frm);
	},
	
	plan_items_add: function(frm, cdt, cdn) {
		// Auto-assign sequence number for new items
		const row = locals[cdt][cdn];
		if (!row.treatment_sequence) {
			row.treatment_sequence = frm.doc.plan_items.length;
		}
	}
});

frappe.ui.form.on('Treatment Plan Item', {
	procedure_code: function(frm, cdt, cdn) {
		// Auto-populate procedure details when procedure is selected
		const row = locals[cdt][cdn];
		if (row.procedure_code) {
			frappe.db.get_doc('Dental Procedure Master', row.procedure_code).then(procedure => {
				frappe.model.set_value(cdt, cdn, 'estimated_cost', procedure.standard_fee);
				frappe.model.set_value(cdt, cdn, 'estimated_duration', procedure.duration_minutes);
				frappe.model.set_value(cdt, cdn, 'insurance_coverage_percentage', procedure.insurance_coverage_percentage);
				
				// Set urgency for emergency procedures
				if (procedure.category === 'Emergency') {
					frappe.model.set_value(cdt, cdn, 'urgency_flag', 1);
					frappe.model.set_value(cdt, cdn, 'priority', 'Urgent');
				}
				
				// Recalculate totals
				calculate_plan_totals(frm);
			});
		}
	},
	
	estimated_cost: function(frm, cdt, cdn) {
		// Recalculate insurance amounts when cost changes
		const row = locals[cdt][cdn];
		calculate_item_costs(row);
		calculate_plan_totals(frm);
	},
	
	insurance_coverage_percentage: function(frm, cdt, cdn) {
		// Recalculate insurance amounts when coverage changes
		const row = locals[cdt][cdn];
		calculate_item_costs(row);
		calculate_plan_totals(frm);
	},
	
	item_status: function(frm, cdt, cdn) {
		// Update plan progress when item status changes
		update_plan_progress(frm);
	},
	
	plan_items_remove: function(frm) {
		// Recalculate totals when items are removed
		calculate_plan_totals(frm);
		update_plan_progress(frm);
	}
});

function calculate_item_costs(row) {
	if (row.estimated_cost && row.insurance_coverage_percentage) {
		row.insurance_amount = flt(row.estimated_cost * row.insurance_coverage_percentage / 100, 2);
		row.patient_portion = flt(row.estimated_cost - row.insurance_amount, 2);
	} else {
		row.insurance_amount = 0;
		row.patient_portion = row.estimated_cost || 0;
	}
}

function calculate_plan_totals(frm) {
	let total_cost = 0;
	let total_duration = 0;
	let total_insurance = 0;
	
	frm.doc.plan_items.forEach(item => {
		if (item.estimated_cost) {
			total_cost += flt(item.estimated_cost);
		}
		if (item.estimated_duration) {
			total_duration += flt(item.estimated_duration);
		}
		if (item.insurance_amount) {
			total_insurance += flt(item.insurance_amount);
		}
	});
	
	frm.set_value('total_estimated_cost', total_cost);
	frm.set_value('total_estimated_duration', total_duration);
	frm.set_value('insurance_amount', total_insurance);
	frm.set_value('patient_portion', total_cost - total_insurance);
}

function update_plan_progress(frm) {
	if (!frm.doc.plan_items || frm.doc.plan_items.length === 0) {
		frm.set_value('plan_progress', 0);
		return;
	}
	
	const total_items = frm.doc.plan_items.length;
	const completed_items = frm.doc.plan_items.filter(item => item.item_status === 'Completed').length;
	
	const progress = (completed_items / total_items) * 100;
	
	frm.set_value('total_items', total_items);
	frm.set_value('completed_items', completed_items);
	frm.set_value('plan_progress', flt(progress, 2));
	
	// Auto-update plan status
	if (progress === 100 && frm.doc.plan_status !== 'Completed') {
		frm.set_value('plan_status', 'Completed');
		frm.set_value('actual_completion_date', frappe.datetime.get_today());
	} else if (progress > 0 && frm.doc.plan_status === 'Draft') {
		frm.set_value('plan_status', 'In Progress');
	}
} 