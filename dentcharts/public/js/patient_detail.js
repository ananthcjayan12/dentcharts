// Patient Detail Dashboard JavaScript

const PatientDetail = {
    currentPatientId: null,
    patientData: null,
    billingSummary: null,
    
    // Initialize patient detail dashboard
    init: function(patientId) {
        console.log('Patient Detail Dashboard JavaScript loaded');
        this.currentPatientId = patientId || window.currentPatientId;
        
        if (!this.currentPatientId) {
            console.error('No patient ID provided');
            return;
        }
        
        this.loadPatientData();
        this.setupEventListeners();
    },

    // Load comprehensive patient data
    loadPatientData: function() {
        console.log('Loading patient data for:', this.currentPatientId);
        this.showLoading();
        
        const self = this;
        
        if (typeof frappe !== 'undefined' && frappe.call) {
            this.loadDataWithFrappe();
        } else {
            this.loadDataWithFetch();
        }
    },

    // Load data using frappe.call
    loadDataWithFrappe: function() {
        const self = this;
        frappe.call({
            method: 'dentcharts.templates.pages.patient_detail.get_patient_detail_data',
            args: { patient_id: this.currentPatientId },
            callback: (response) => {
                console.log('Frappe API Response:', response);
                self.handlePatientDataResponse(response.message);
            },
            error: (error) => {
                console.error('Frappe API failed:', error);
                self.showError('Failed to load patient data');
                self.hideLoading();
            }
        });
    },

    // Load data using fetch API
    loadDataWithFetch: function() {
        const self = this;
        
        fetch('/api/method/dentcharts.templates.pages.patient_detail.get_patient_detail_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': this.getCSRFToken()
            },
            body: JSON.stringify({ patient_id: this.currentPatientId })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Fetch API Response:', data);
            self.handlePatientDataResponse(data.message);
        })
        .catch(error => {
            console.error('Fetch API failed:', error);
            self.showError('Failed to load patient data');
            self.hideLoading();
        });
    },

    // Handle patient data response
    handlePatientDataResponse: function(responseData) {
        if (responseData && responseData.success && responseData.data) {
            console.log('Successfully loaded patient data:', responseData.data);
            this.patientData = responseData.data;
            this.renderPatientData();
            this.loadBillingSummary(); // Load billing summary after patient data
        } else {
            console.error('API returned unsuccessful response:', responseData);
            this.showError('Failed to load patient data');
        }
        this.hideLoading();
    },

    // Load billing summary data
    loadBillingSummary: function() {
        fetch(`/api/method/dentcharts.templates.pages.patient_detail.get_patient_billing_summary?patient_id=${this.currentPatientId}`)
            .then(response => response.json())
            .then(data => {
                if (data.message && data.message.success) {
                    this.billingSummary = data.message.data;
                    this.renderBillingSummary();
                }
            })
            .catch(error => {
                console.error('Error loading billing summary:', error);
            });
    },

    // Load enhanced notebook summary
    loadNotebookSummary: function() {
        fetch(`/api/method/dentcharts.templates.pages.patient_detail.get_patient_notebook_summary?patient_id=${this.patientId}&limit=15`)
            .then(response => response.json())
            .then(data => {
                if (data.message && data.message.success) {
                    this.notebookData = data.message.data;
                    this.renderEnhancedNotebook();
                }
            })
            .catch(error => {
                console.error('Error loading notebook summary:', error);
            });
    },

    // Render all patient data
    renderPatientData: function() {
        if (!this.patientData) return;
        
        this.updatePatientHeader();
        this.updateOverviewStats();
        this.renderRecentActivity();
        this.renderMedicalHistory();
        this.renderPaymentsTable();
        this.loadNotebookSummary(); // Use enhanced notebook instead of basic one
    },

    // Update patient header information
    updatePatientHeader: function() {
        const patient = this.patientData.patient_info;
        
        if (patient.age) {
            const ageEl = document.getElementById('patient-age');
            if (ageEl) ageEl.textContent = `Age: ${patient.age}`;
        }
    },

    // Update overview statistics
    updateOverviewStats: function() {
        const appointments = this.patientData.appointments || [];
        const payments = this.patientData.payments || [];
        const chartData = this.patientData.chart_data || [];
        
        // Total appointments
        const totalAppointmentsEl = document.getElementById('total-appointments');
        if (totalAppointmentsEl) totalAppointmentsEl.textContent = appointments.length;
        
        // Total procedures (from chart data)
        const totalProceduresEl = document.getElementById('total-procedures');
        if (totalProceduresEl) totalProceduresEl.textContent = chartData.length;
        
        // Total payments
        const totalPayments = payments.reduce((sum, payment) => sum + (payment.payment_amount || 0), 0);
        const totalPaymentsEl = document.getElementById('total-payments');
        if (totalPaymentsEl) totalPaymentsEl.textContent = this.formatCurrency(totalPayments);
        
        // Last visit
        const lastVisitEl = document.getElementById('last-visit');
        if (lastVisitEl && appointments.length > 0) {
            lastVisitEl.textContent = this.formatDate(appointments[0].appointment_date);
        } else if (lastVisitEl) {
            lastVisitEl.textContent = 'No visits';
        }
    },

    // Render recent activity
    renderRecentActivity: function() {
        const activityList = document.getElementById('recent-activity-list');
        if (!activityList) return;
        
        const appointments = this.patientData.appointments || [];
        activityList.innerHTML = '';
        
        if (appointments.length === 0) {
            activityList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-details">No recent activity</div>
                    </div>
                </div>
            `;
            return;
        }
        
        appointments.slice(0, 5).forEach(appointment => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-info">
                    <div class="activity-date">${this.formatDate(appointment.appointment_date)}</div>
                    <div class="activity-details">
                        <strong>${appointment.status || 'Appointment'}</strong>
                        ${appointment.practitioner ? ` - ${appointment.practitioner}` : ''}
                    </div>
                    ${appointment.chief_complaint ? `<div class="activity-complaint">${appointment.chief_complaint}</div>` : ''}
                </div>
                <div class="activity-status status-${(appointment.status || '').toLowerCase()}">
                    ${appointment.status || 'Scheduled'}
                </div>
            `;
            activityList.appendChild(activityItem);
        });
    },

    // Render medical history
    renderMedicalHistory: function() {
        const history = this.patientData.medical_history || {};
        
        // Dental history
        const dentalHistoryEl = document.getElementById('dental-history-content');
        if (dentalHistoryEl) {
            dentalHistoryEl.innerHTML = history.dental_history || 'No dental history recorded';
        }
        
        // Allergies
        const allergiesEl = document.getElementById('allergies-content');
        if (allergiesEl) {
            allergiesEl.innerHTML = history.dental_allergies || 'No allergies recorded';
        }
        
        // Previous work
        const previousWorkEl = document.getElementById('previous-work-content');
        if (previousWorkEl) {
            previousWorkEl.innerHTML = history.previous_dental_work || 'No previous dental work recorded';
        }
        
        // Insurance
        const insuranceEl = document.getElementById('insurance-content');
        if (insuranceEl) {
            insuranceEl.innerHTML = history.dental_insurance || 'No insurance information recorded';
        }
    },

    // Render payments table with enhanced details
    renderPaymentsTable: function() {
        const tbody = document.getElementById('payments-table-body');
        if (!tbody) return;
        
        const payments = this.patientData.payments || [];
        tbody.innerHTML = '';
        
        if (payments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 2rem; color: #7f8c8d;">
                        No payments recorded
                    </td>
                </tr>
            `;
            return;
        }
        
        payments.forEach(payment => {
            const statusBadge = this.getPaymentStatusBadge(payment.payment_status);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatDate(payment.posting_date)}</td>
                <td class="payment-amount">${this.formatCurrency(payment.payment_amount)}</td>
                <td>
                    <span class="payment-method-badge method-${(payment.payment_method || '').toLowerCase().replace(' ', '-')}">
                        ${payment.payment_method || 'N/A'}
                    </span>
                </td>
                <td>${statusBadge}</td>
                <td>${payment.reference_number || 'N/A'}</td>
                <td>${payment.received_by || 'N/A'}</td>
                <td class="payment-notes">${this.truncateText(payment.notes || 'N/A', 30)}</td>
                <td>
                    <button class="action-btn view-small" onclick="viewPayment('${payment.name}')" title="View Payment">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${payment.invoice ? `
                        <button class="action-btn edit-small" onclick="viewInvoice('${payment.invoice}')" title="View Invoice">
                            <i class="fas fa-file-invoice"></i>
                        </button>
                    ` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });
        
        // Load billing summary after payments are rendered
        this.loadBillingSummary();
    },

    // Get payment status badge
    getPaymentStatusBadge: function(status) {
        const statusClass = (status || '').toLowerCase().replace(' ', '-');
        const statusText = status || 'Unknown';
        return `<span class="status-badge status-${statusClass}">${statusText}</span>`;
    },

    // Truncate text for display
    truncateText: function(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    // Render notebook-style summary
    renderNotebookSummary: function() {
        const notebookContent = document.getElementById('notebook-content');
        if (!notebookContent) return;
        
        const activities = this.patientData.activity_summary || [];
        notebookContent.innerHTML = '';
        
        if (activities.length === 0) {
            notebookContent.innerHTML = `
                <div class="notebook-entry">
                    <div class="entry-content">
                        <p>No visit records available for notebook summary.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        activities.forEach(activity => {
            const entryDiv = document.createElement('div');
            entryDiv.className = 'notebook-entry';
            
            let proceduresHtml = '';
            if (activity.procedures && activity.procedures.length > 0) {
                proceduresHtml = `
                    <div class="entry-section">
                        <h4>Procedures:</h4>
                        <ul>
                            ${activity.procedures.map(proc => `<li>Tooth ${proc.tooth}: ${proc.procedure}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            let findingsHtml = '';
            if (activity.findings && activity.findings.length > 0) {
                findingsHtml = `
                    <div class="entry-section">
                        <h4>Findings:</h4>
                        <ul>
                            ${activity.findings.map(finding => `<li>Tooth ${finding.tooth}: ${finding.finding}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            entryDiv.innerHTML = `
                <div class="entry-header">
                    <h3>🗓️ ${this.formatDate(activity.date)} ${activity.doctor ? `(${activity.doctor})` : ''}</h3>
                </div>
                <div class="entry-content">
                    ${activity.chief_complaint ? `
                        <div class="entry-section">
                            <h4>Chief Complaint:</h4>
                            <p>${activity.chief_complaint}</p>
                        </div>
                    ` : ''}
                    
                    ${activity.notes ? `
                        <div class="entry-section">
                            <h4>Notes:</h4>
                            <p>${activity.notes}</p>
                        </div>
                    ` : ''}
                    
                    ${findingsHtml}
                    ${proceduresHtml}
                    
                    <div class="entry-footer">
                        <span class="entry-status">Status: ${activity.status || 'Completed'}</span>
                        ${activity.time ? `<span class="entry-time">Time: ${activity.time}</span>` : ''}
                    </div>
                </div>
            `;
            
            notebookContent.appendChild(entryDiv);
        });
    },

    // Render enhanced notebook-style summary
    renderEnhancedNotebook: function() {
        const notebookContent = document.getElementById('notebook-content');
        if (!notebookContent || !this.notebookData) return;
        
        const entries = this.notebookData.notebook_entries || [];
        notebookContent.innerHTML = '';
        
        if (entries.length === 0) {
            notebookContent.innerHTML = `
                <div class="no-data-notebook">
                    <i class="fas fa-book-open fa-3x"></i>
                    <h3>No Visit Records</h3>
                    <p>No visit records found for this patient.</p>
                </div>
            `;
            return;
        }
        
        entries.forEach((entry, index) => {
            const entryDiv = document.createElement('div');
            entryDiv.className = 'notebook-entry enhanced';
            
            // Visit status indicator
            const statusIndicator = this.getVisitStatusIndicator(entry.status);
            
            // Quick stats
            const quickStats = this.generateQuickStats(entry);
            
            entryDiv.innerHTML = `
                <div class="entry-header enhanced">
                    <div class="visit-date-section">
                        <h3>
                            <i class="fas fa-calendar-day"></i>
                            ${this.formatDate(entry.date)}
                            ${entry.time ? `at ${entry.time}` : ''}
                        </h3>
                        <div class="visit-metadata">
                            ${entry.doctor ? `<span class="doctor-name"><i class="fas fa-user-md"></i> Dr. ${entry.doctor}</span>` : ''}
                            ${statusIndicator}
                            ${entry.appointment_type ? `<span class="appointment-type">${entry.appointment_type}</span>` : ''}
                        </div>
                    </div>
                    ${quickStats}
                </div>
                
                <div class="entry-content enhanced">
                    <!-- Narrative Summary -->
                    <div class="narrative-section">
                        <div class="narrative-text">
                            <i class="fas fa-quote-left"></i>
                            <p>${entry.narrative_summary || 'Visit completed without specific notes.'}</p>
                        </div>
                    </div>
                    
                    <!-- Detailed Sections -->
                    ${this.renderDetailedSections(entry)}
                    
                    <!-- Footer with additional info -->
                    <div class="entry-footer enhanced">
                        ${entry.estimated_cost ? `<span class="cost-info"><i class="fas fa-dollar-sign"></i> Estimated: $${entry.estimated_cost}</span>` : ''}
                        ${entry.payment_status ? `<span class="payment-status">Payment: ${entry.payment_status}</span>` : ''}
                        ${entry.special_instructions ? `<span class="special-note"><i class="fas fa-exclamation-circle"></i> Special Instructions</span>` : ''}
                    </div>
                </div>
            `;
            
            notebookContent.appendChild(entryDiv);
        });
    },

    // Generate quick stats for entry header
    generateQuickStats: function(entry) {
        const stats = [];
        
        if (entry.procedure_count > 0) {
            stats.push(`<span class="quick-stat procedures"><i class="fas fa-tools"></i> ${entry.procedure_count} procedure${entry.procedure_count > 1 ? 's' : ''}</span>`);
        }
        
        if (entry.finding_count > 0) {
            stats.push(`<span class="quick-stat findings"><i class="fas fa-search"></i> ${entry.finding_count} finding${entry.finding_count > 1 ? 's' : ''}</span>`);
        }
        
        if (entry.payment_total > 0) {
            stats.push(`<span class="quick-stat payment"><i class="fas fa-credit-card"></i> $${entry.payment_total.toFixed(2)}</span>`);
        }
        
        if (stats.length === 0) {
            stats.push(`<span class="quick-stat consultation"><i class="fas fa-comments"></i> Consultation</span>`);
        }
        
        return `<div class="quick-stats">${stats.join('')}</div>`;
    },

    // Get visit status indicator
    getVisitStatusIndicator: function(status) {
        const statusClass = (status || 'completed').toLowerCase().replace(' ', '-');
        const statusIcon = {
            'completed': 'fas fa-check-circle',
            'scheduled': 'fas fa-clock',
            'cancelled': 'fas fa-times-circle',
            'no-show': 'fas fa-user-times'
        }[statusClass] || 'fas fa-circle';
        
        return `<span class="status-indicator status-${statusClass}"><i class="${statusIcon}"></i> ${status || 'Completed'}</span>`;
    },

    // Render detailed sections for entry
    renderDetailedSections: function(entry) {
        let sections = [];
        
        // Chief complaint section
        if (entry.chief_complaint) {
            sections.push(`
                <div class="detail-section complaint">
                    <h4><i class="fas fa-user-injured"></i> Chief Complaint</h4>
                    <p>${entry.chief_complaint}</p>
                </div>
            `);
        }
        
        // Procedures section
        if (entry.procedures && entry.procedures.length > 0) {
            const proceduresList = entry.procedures.map(proc => `
                <li class="procedure-item">
                    <div class="procedure-header">
                        <span class="tooth-number">Tooth ${proc.tooth_number || 'N/A'}</span>
                        <span class="procedure-name">${proc.procedure_name}</span>
                    </div>
                    <div class="procedure-details">
                        ${proc.status ? `<span class="procedure-status">${proc.status}</span>` : ''}
                        ${proc.cost ? `<span class="procedure-cost">$${proc.cost}</span>` : ''}
                    </div>
                    ${proc.notes ? `<p class="procedure-notes">${proc.notes}</p>` : ''}
                </li>
            `).join('');
            
            sections.push(`
                <div class="detail-section procedures">
                    <h4><i class="fas fa-tools"></i> Procedures Performed</h4>
                    <ul class="procedures-list">${proceduresList}</ul>
                </div>
            `);
        }
        
        // Findings section
        if (entry.findings && entry.findings.length > 0) {
            const findingsList = entry.findings.map(finding => `
                <li class="finding-item">
                    <div class="finding-header">
                        <span class="tooth-number">Tooth ${finding.tooth_number || 'N/A'}</span>
                        <span class="finding-name">${finding.finding}</span>
                    </div>
                    <div class="finding-details">
                        ${finding.severity ? `<span class="severity severity-${finding.severity.toLowerCase()}">${finding.severity}</span>` : ''}
                        ${finding.status ? `<span class="finding-status">${finding.status}</span>` : ''}
                    </div>
                    ${finding.notes ? `<p class="finding-notes">${finding.notes}</p>` : ''}
                </li>
            `).join('');
            
            sections.push(`
                <div class="detail-section findings">
                    <h4><i class="fas fa-search"></i> Clinical Findings</h4>
                    <ul class="findings-list">${findingsList}</ul>
                </div>
            `);
        }
        
        // Treatment plan section
        if (entry.treatment_plan) {
            sections.push(`
                <div class="detail-section treatment-plan">
                    <h4><i class="fas fa-clipboard-list"></i> Treatment Plan</h4>
                    <p>${entry.treatment_plan}</p>
                </div>
            `);
        }
        
        // Notes sections
        const noteSections = [];
        if (entry.notes) {
            noteSections.push(`<div class="note-item"><strong>Practitioner Notes:</strong> ${entry.notes}</div>`);
        }
        if (entry.patient_notes) {
            noteSections.push(`<div class="note-item"><strong>Patient Notes:</strong> ${entry.patient_notes}</div>`);
        }
        if (entry.special_instructions) {
            noteSections.push(`<div class="note-item special"><strong>Special Instructions:</strong> ${entry.special_instructions}</div>`);
        }
        
        if (noteSections.length > 0) {
            sections.push(`
                <div class="detail-section notes">
                    <h4><i class="fas fa-sticky-note"></i> Notes</h4>
                    <div class="notes-container">${noteSections.join('')}</div>
                </div>
            `);
        }
        
        // Payments section
        if (entry.payments && entry.payments.length > 0) {
            const paymentsList = entry.payments.map(payment => `
                <li class="payment-item">
                    <span class="payment-amount">$${payment.payment_amount.toFixed(2)}</span>
                    <span class="payment-method">${payment.payment_method}</span>
                    ${payment.reference_number ? `<span class="payment-ref">${payment.reference_number}</span>` : ''}
                </li>
            `).join('');
            
            sections.push(`
                <div class="detail-section payments">
                    <h4><i class="fas fa-credit-card"></i> Payments</h4>
                    <ul class="payments-list">${paymentsList}</ul>
                </div>
            `);
        }
        
        return sections.join('');
    },

    // Render billing summary
    renderBillingSummary: function() {
        if (!this.billingSummary) return;
        
        const summary = this.billingSummary.payment_summary;
        
        // Update payment statistics
        const totalPaidEl = document.getElementById('total-paid-amount');
        if (totalPaidEl) totalPaidEl.textContent = this.formatCurrency(summary.total_paid || 0);
        
        const totalPaymentsCountEl = document.getElementById('total-payments-count');
        if (totalPaymentsCountEl) totalPaymentsCountEl.textContent = summary.total_payments || 0;
        
        const averagePaymentEl = document.getElementById('average-payment');
        if (averagePaymentEl) averagePaymentEl.textContent = this.formatCurrency(summary.average_payment || 0);
        
        const lastPaymentDateEl = document.getElementById('last-payment-date');
        if (lastPaymentDateEl && summary.last_payment_date) {
            lastPaymentDateEl.textContent = this.formatDate(summary.last_payment_date);
        }
        
        // Render payment method breakdown
        this.renderPaymentMethodBreakdown(summary);
        
        // Render outstanding invoices
        this.renderOutstandingInvoices();
    },

    // Render payment method breakdown
    renderPaymentMethodBreakdown: function(summary) {
        const methodsContainer = document.getElementById('payment-methods-breakdown');
        if (!methodsContainer) return;
        
        const methods = [
            { name: 'Cash', count: summary.cash_payments || 0, color: '#28a745' },
            { name: 'Card', count: summary.card_payments || 0, color: '#007bff' },
            { name: 'Bank Transfer', count: summary.bank_payments || 0, color: '#6f42c1' },
            { name: 'Insurance', count: summary.insurance_payments || 0, color: '#fd7e14' }
        ];
        
        methodsContainer.innerHTML = methods.map(method => `
            <div class="payment-method-item">
                <div class="method-indicator" style="background-color: ${method.color}"></div>
                <span class="method-name">${method.name}</span>
                <span class="method-count">${method.count}</span>
            </div>
        `).join('');
    },

    // Render outstanding invoices
    renderOutstandingInvoices: function() {
        const invoicesContainer = document.getElementById('outstanding-invoices');
        if (!invoicesContainer) return;
        
        const invoices = this.billingSummary.outstanding_invoices || [];
        
        if (invoices.length === 0) {
            invoicesContainer.innerHTML = '<p class="no-data">No outstanding invoices</p>';
            return;
        }
        
        invoicesContainer.innerHTML = invoices.map(invoice => `
            <div class="invoice-item">
                <div class="invoice-header">
                    <span class="invoice-number">${invoice.name}</span>
                    <span class="invoice-amount">${this.formatCurrency(invoice.outstanding_amount)}</span>
                </div>
                <div class="invoice-details">
                    <span class="invoice-date">Due: ${this.formatDate(invoice.due_date)}</span>
                    <span class="invoice-status status-${invoice.status.toLowerCase().replace(' ', '-')}">${invoice.status}</span>
                </div>
            </div>
        `).join('');
        
        // Update total outstanding
        const totalOutstandingEl = document.getElementById('total-outstanding');
        if (totalOutstandingEl) {
            totalOutstandingEl.textContent = this.formatCurrency(this.billingSummary.total_outstanding || 0);
        }
    },

    // Tab switching functionality
    switchTab: function(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        const clickedTab = event.target.closest('.tab-btn');
        if (clickedTab) clickedTab.classList.add('active');
        
        const targetContent = document.getElementById(`${tabName}-tab`);
        if (targetContent) targetContent.classList.add('active');
    },

    // Setup event listeners
    setupEventListeners: function() {
        // Tab switching event delegation
        const tabNavigation = document.querySelector('.tab-navigation');
        if (tabNavigation) {
            tabNavigation.addEventListener('click', (e) => {
                const tabBtn = e.target.closest('.tab-btn');
                if (tabBtn) {
                    const tabName = tabBtn.onclick.toString().match(/'([^']+)'/)[1];
                    this.switchTab(tabName);
                }
            });
        }
    },

    // Utility functions
    getCSRFToken: function() {
        const tokenElement = document.querySelector('meta[name="csrf-token"]');
        return tokenElement ? tokenElement.getAttribute('content') : '';
    },

    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount || 0);
    },

    formatDate: function(dateStr) {
        if (!dateStr) return 'N/A';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    showLoading: function() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
    },

    hideLoading: function() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    },

    showError: function(message) {
        console.error('Patient Detail Error:', message);
        if (typeof frappe !== 'undefined' && frappe.msgprint) {
            frappe.msgprint({
                title: 'Error',
                message: message,
                indicator: 'red'
            });
        } else {
            alert(message);
        }
    }
};

// Global function bindings for HTML onclick events
function switchTab(tabName) {
    PatientDetail.switchTab(tabName);
}

function editPatient(patientId) {
    window.open(`/app/dental-patient/${patientId}`, '_blank');
}

function scheduleAppointment(patientId) {
    window.open('/app/dental-appointment/new', '_blank');
}

function recordPayment(patientId) {
    window.open('/app/dental-payment-entry/new', '_blank');
}

function openDentalChart(patientId) {
    // This will open the existing dental chart system
    window.open(`/app/dental-chart/${patientId}`, '_blank');
}

function viewPayment(paymentId) {
    window.open(`/app/dental-payment-entry/${paymentId}`, '_blank');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    PatientDetail.init();
});

// Auto-initialize if frappe is available
if (typeof frappe !== 'undefined') {
    frappe.ready(() => {
        PatientDetail.init();
    });
}
