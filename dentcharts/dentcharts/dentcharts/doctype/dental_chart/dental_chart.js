frappe.ui.form.on('Dental Chart', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			create_interactive_dental_chart(frm);
			update_activity_timeline(frm);
			// Add Generate Invoice button if there are completed procedures
			let completed = (frm.doc.tooth_procedures || []).filter(proc => proc.status === 'Completed');
			if (completed.length) {
				frm.add_custom_button(__('Generate Invoice'), function() {
					let items = completed.map(function(proc) {
						return {
							procedure_code: proc.procedure_code,
							description: proc.procedure_name,
							tooth_number: proc.tooth_number,
							surface: proc.surface,
							quantity: 1,
							amount: proc.actual_fee || proc.standard_fee
						};
					});
					frappe.route_options = {
						patient: frm.doc.patient,
						practitioner: frm.doc.dentist,
						dental_clinic: frm.doc.clinic,
						invoice_items: items
					};
					frappe.new_doc('Invoice');
				}, __('Actions'));
			}
		}
	}
}); 