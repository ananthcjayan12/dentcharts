frappe.ui.form.on('Dental Chart', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			create_interactive_dental_chart(frm);
			update_activity_timeline(frm);
		}
	}
}); 