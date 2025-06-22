frappe.ui.form.on('Invoice', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 1) {
			// Add payment button
			if (frm.doc.payment_status !== 'Paid') {
				frm.add_custom_button(__('Record Payment'), function() {
					record_payment_dialog(frm);
				}, __('Actions'));
			}
			
			// Add send invoice button
			if (frm.doc.invoice_status === 'Draft') {
				frm.add_custom_button(__('Send Invoice'), function() {
					frappe.call({
						method: 'send_invoice',
						doc: frm.doc,
						callback: function(r) {
							frm.reload_doc();
						}
					});
				}, __('Actions'));
			}
			
			// Add cancel invoice button
			if (frm.doc.invoice_status !== 'Cancelled') {
				frm.add_custom_button(__('Cancel Invoice'), function() {
					cancel_invoice_dialog(frm);
				}, __('Actions'));
			}
		}
		
		// Color-code based on status
		set_status_colors(frm);
		
		// Show payment history
		if (frm.doc.name) {
			show_payment_history(frm);
		}
	},
	
	patient: function(frm) {
		// Auto-populate patient details
		if (frm.doc.patient) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Patient',
					name: frm.doc.patient
				},
				callback: function(r) {
					if (r.message) {
						// You can set billing address or other patient details here
						frm.set_value('billing_address', r.message.address || '');
					}
				}
			});
		}
	},
	
	treatment_plan: function(frm) {
		// Auto-populate items from treatment plan
		if (frm.doc.treatment_plan) {
			frappe.call({
				method: 'dentcharts.dentcharts.doctype.invoice.invoice.Invoice.create_from_treatment_plan',
				args: {
					treatment_plan_name: frm.doc.treatment_plan
				},
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(__('Items populated from treatment plan'));
						frm.reload_doc();
					}
				}
			});
		}
	},
	
	insurance_coverage_percentage: function(frm) {
		// Recalculate insurance amounts when percentage changes
		calculate_insurance_amounts(frm);
	},
	
	payment_terms: function(frm) {
		// Auto-set due date based on payment terms
		if (frm.doc.invoice_date && frm.doc.payment_terms) {
			let due_date = frappe.datetime.add_days(frm.doc.invoice_date, get_payment_term_days(frm.doc.payment_terms));
			frm.set_value('due_date', due_date);
		}
	}
});

frappe.ui.form.on('Invoice Item', {
	procedure_code: function(frm, cdt, cdn) {
		// Auto-populate procedure details
		let row = locals[cdt][cdn];
		if (row.procedure_code) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Dental Procedure Master',
					name: row.procedure_code
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'description', r.message.procedure_name);
						if (!row.amount) {
							frappe.model.set_value(cdt, cdn, 'amount', r.message.standard_fee);
						}
					}
				}
			});
		}
	},
	
	quantity: function(frm, cdt, cdn) {
		calculate_item_total(frm, cdt, cdn);
	},
	
	amount: function(frm, cdt, cdn) {
		calculate_item_total(frm, cdt, cdn);
	},
	
	invoice_items_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_item_total(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total = flt(row.quantity) * flt(row.amount);
	frappe.model.set_value(cdt, cdn, 'total_amount', total);
	calculate_totals(frm);
}

function calculate_totals(frm) {
	let subtotal = 0;
	
	frm.doc.invoice_items.forEach(function(item) {
		subtotal += flt(item.total_amount || item.amount || 0);
	});
	
	frm.set_value('subtotal', subtotal);
	frm.set_value('total_amount', subtotal + flt(frm.doc.tax_amount || 0));
	
	calculate_insurance_amounts(frm);
}

function calculate_insurance_amounts(frm) {
	if (frm.doc.insurance_coverage_percentage && frm.doc.total_amount) {
		let insurance_amount = flt(frm.doc.total_amount * frm.doc.insurance_coverage_percentage / 100);
		frm.set_value('insurance_amount', insurance_amount);
		frm.set_value('patient_portion', frm.doc.total_amount - insurance_amount);
	}
	
	// Calculate outstanding amount
	let outstanding = flt(frm.doc.total_amount) - flt(frm.doc.paid_amount || 0);
	frm.set_value('outstanding_amount', outstanding);
}

function get_payment_term_days(payment_terms) {
	switch(payment_terms) {
		case 'Immediate': return 0;
		case 'Net 15': return 15;
		case 'Net 30': return 30;
		case 'Net 60': return 60;
		default: return 30;
	}
}

function record_payment_dialog(frm) {
	let dialog = new frappe.ui.Dialog({
		title: __('Record Payment'),
		fields: [
			{
				fieldtype: 'Currency',
				fieldname: 'payment_amount',
				label: __('Payment Amount'),
				reqd: 1,
				default: frm.doc.outstanding_amount
			},
			{
				fieldtype: 'Select',
				fieldname: 'payment_method',
				label: __('Payment Method'),
				options: 'Cash\nCredit Card\nDebit Card\nCheck\nBank Transfer\nOnline Payment',
				default: 'Cash',
				reqd: 1
			},
			{
				fieldtype: 'Date',
				fieldname: 'payment_date',
				label: __('Payment Date'),
				default: frappe.datetime.get_today(),
				reqd: 1
			},
			{
				fieldtype: 'Data',
				fieldname: 'reference_number',
				label: __('Reference Number')
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'notes',
				label: __('Notes')
			}
		],
		primary_action_label: __('Record Payment'),
		primary_action: function(values) {
			frappe.call({
				method: 'record_payment',
				doc: frm.doc,
				args: {
					payment_amount: values.payment_amount,
					payment_method: values.payment_method,
					payment_date: values.payment_date,
					reference_number: values.reference_number
				},
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(__('Payment recorded successfully'));
						frm.reload_doc();
						dialog.hide();
					}
				}
			});
		}
	});
	
	dialog.show();
}

function cancel_invoice_dialog(frm) {
	frappe.prompt([
		{
			fieldtype: 'Small Text',
			fieldname: 'reason',
			label: __('Cancellation Reason'),
			reqd: 1
		}
	], function(values) {
		frappe.call({
			method: 'cancel_invoice',
			doc: frm.doc,
			args: {
				reason: values.reason
			},
			callback: function(r) {
				frappe.msgprint(__('Invoice cancelled'));
				frm.reload_doc();
			}
		});
	}, __('Cancel Invoice'));
}

function set_status_colors(frm) {
	// Color-code invoice status
	if (frm.doc.invoice_status === 'Overdue') {
		frm.dashboard.set_headline_alert(__('This invoice is overdue'), 'red');
	} else if (frm.doc.payment_status === 'Paid') {
		frm.dashboard.set_headline_alert(__('Invoice fully paid'), 'green');
	} else if (frm.doc.payment_status === 'Partially Paid') {
		frm.dashboard.set_headline_alert(__('Invoice partially paid'), 'orange');
	}
}

function show_payment_history(frm) {
	// Show payment history in dashboard
	frappe.call({
		method: 'get_payment_history',
		doc: frm.doc,
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let payment_html = '<h5>Payment History</h5><table class="table table-condensed">';
				payment_html += '<thead><tr><th>Date</th><th>Amount</th><th>Method</th><th>Reference</th></tr></thead><tbody>';
				
				r.message.forEach(function(payment) {
					payment_html += `<tr>
						<td>${frappe.datetime.str_to_user(payment.payment_date)}</td>
						<td>${format_currency(payment.payment_amount)}</td>
						<td>${payment.payment_method}</td>
						<td>${payment.reference_number || ''}</td>
					</tr>`;
				});
				
				payment_html += '</tbody></table>';
				frm.dashboard.add_section(payment_html);
			}
		}
	});
} 