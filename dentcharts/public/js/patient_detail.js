// Patient Detail Dashboard JavaScript

const PatientDetail = {
    currentPatientId: null,
    patientData: null,
    
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
        } else {
            console.error('API returned unsuccessful response:', responseData);
            this.showError('Failed to load patient data');
        }
        this.hideLoading();
    },

    // Render all patient data
    renderPatientData: function() {
        if (!this.patientData) return;
        
        this.updatePatientHeader();
        this.updateOverviewStats();
        this.renderRecentActivity();
        this.renderMedicalHistory();
        this.renderPaymentsTable();
        this.renderNotebookSummary();
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

    // Render payments table
    renderPaymentsTable: function() {
        const tbody = document.getElementById('payments-table-body');
        if (!tbody) return;
        
        const payments = this.patientData.payments || [];
        tbody.innerHTML = '';
        
        if (payments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem; color: #7f8c8d;">
                        No payments recorded
                    </td>
                </tr>
            `;
            return;
        }
        
        payments.forEach(payment => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatDate(payment.posting_date)}</td>
                <td>${this.formatCurrency(payment.payment_amount)}</td>
                <td>${payment.payment_method || 'N/A'}</td>
                <td>${payment.reference_number || 'N/A'}</td>
                <td>${payment.notes || 'N/A'}</td>
                <td>
                    <button class="action-btn view-small" onclick="viewPayment('${payment.name}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
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
