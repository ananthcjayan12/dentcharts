/**
 * Patient Dashboard JavaScript
 * Main controller for patient dashboard functionality
 * Uses modern ES6+ features and simple module pattern
 */

class PatientDashboard {
    constructor() {
        this.currentPatient = null;
        this.components = {};
        this.cache = new Map();
        this.init();
    }

    /**
     * Initialize the dashboard
     */
    init() {
        console.log('Initializing Patient Dashboard...');
        this.setupEventListeners();
        this.loadDashboardData();
        this.initializeComponents();
    }

    /**
     * Setup event listeners for dashboard interactions
     */
    setupEventListeners() {
        // Patient search functionality
        const searchInput = document.getElementById('patient-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handlePatientSearch(e.target.value);
            });
        }

        // Patient selection
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('patient-item')) {
                const patientId = e.target.dataset.patientId;
                this.selectPatient(patientId);
            }
        });

        // Dashboard card interactions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('dashboard-card')) {
                this.handleCardClick(e.target);
            }
        });

        // Summary navigation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('summary-nav-item')) {
                this.navigateToSummary(e.target.dataset.date);
            }
        });
    }

    /**
     * Load initial dashboard data
     */
    async loadDashboardData() {
        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.get_dashboard_stats',
                args: {}
            });

            if (response.message) {
                this.renderDashboardCards(response.message);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    /**
     * Initialize dashboard components
     */
    initializeComponents() {
        // Initialize patient search component
        this.components.patientSearch = new PatientSearch();
        
        // Initialize patient list component
        this.components.patientList = new PatientList();
        
        // Initialize summary component
        this.components.summary = new PatientSummary();
        
        // Initialize chart wrapper
        this.components.chart = new DentalChartWrapper();
        
        // Initialize payment component
        this.components.payment = new PaymentHistory();
    }

    /**
     * Handle patient search
     */
    async handlePatientSearch(query) {
        if (query.length < 2) {
            this.clearPatientList();
            return;
        }

        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.search_patients',
                args: { query: query }
            });

            if (response.message) {
                this.renderPatientList(response.message);
            }
        } catch (error) {
            console.error('Error searching patients:', error);
        }
    }

    /**
     * Select a patient and load their data
     */
    async selectPatient(patientId) {
        try {
            this.showLoading('Loading patient data...');
            
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.get_patient_data',
                args: { patient_id: patientId }
            });

            if (response.message) {
                this.currentPatient = response.message;
                this.renderPatientDashboard(response.message);
                this.hideLoading();
            }
        } catch (error) {
            console.error('Error loading patient data:', error);
            this.showError('Failed to load patient data');
            this.hideLoading();
        }
    }

    /**
     * Render dashboard cards with statistics
     */
    renderDashboardCards(data) {
        const cardsContainer = document.getElementById('dashboard-cards');
        if (!cardsContainer) return;

        cardsContainer.innerHTML = `
            <div class="dashboard-card patients-card" data-type="patients">
                <div class="card-header">
                    <h3>Patients</h3>
                    <i class="fas fa-users"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.total_patients || 0}</div>
                    <div class="card-description">Total Patients</div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.createNewPatient()">
                        Add Patient
                    </button>
                </div>
            </div>

            <div class="dashboard-card appointments-card" data-type="appointments">
                <div class="card-header">
                    <h3>Appointments</h3>
                    <i class="fas fa-calendar"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.today_appointments || 0}</div>
                    <div class="card-description">Today's Appointments</div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.createNewAppointment()">
                        Schedule
                    </button>
                </div>
            </div>

            <div class="dashboard-card accounts-card" data-type="accounts">
                <div class="card-header">
                    <h3>Accounts</h3>
                    <i class="fas fa-dollar-sign"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">$${data.total_outstanding || 0}</div>
                    <div class="card-description">Outstanding Balance</div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.viewAccounts()">
                        View Details
                    </button>
                </div>
            </div>

            <div class="dashboard-card stats-card" data-type="stats">
                <div class="card-header">
                    <h3>Statistics</h3>
                    <i class="fas fa-chart-bar"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.completed_treatments || 0}</div>
                    <div class="card-description">Completed Treatments</div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.viewStatistics()">
                        View Report
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render patient list from search results
     */
    renderPatientList(patients) {
        const patientList = document.getElementById('patient-list');
        if (!patientList) return;

        patientList.innerHTML = patients.map(patient => `
            <div class="patient-item" data-patient-id="${patient.name}">
                <div class="patient-info">
                    <div class="patient-name">${patient.patient_name}</div>
                    <div class="patient-details">
                        <span class="patient-id">ID: ${patient.patient_id}</span>
                        <span class="patient-age">Age: ${patient.age}</span>
                    </div>
                </div>
                <div class="patient-actions">
                    <button class="btn btn-sm btn-primary" onclick="patientDashboard.selectPatient('${patient.name}')">
                        Select
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Clear patient list
     */
    clearPatientList() {
        const patientList = document.getElementById('patient-list');
        if (patientList) {
            patientList.innerHTML = '';
        }
    }

    /**
     * Render patient dashboard with all components
     */
    renderPatientDashboard(patientData) {
        // Render patient header
        this.renderPatientHeader(patientData);
        
        // Load and render chart
        this.loadDentalChart(patientData.name);
        
        // Load and render payment history
        this.loadPaymentHistory(patientData.name);
        
        // Load and render patient summary
        this.loadPatientSummary(patientData.name);
        
        // Show patient dashboard section
        this.showPatientDashboard();
    }

    /**
     * Render patient header information
     */
    renderPatientHeader(patientData) {
        const headerContainer = document.getElementById('patient-header');
        if (!headerContainer) return;

        headerContainer.innerHTML = `
            <div class="patient-header-info">
                <div class="patient-name">${patientData.patient_name}</div>
                <div class="patient-details">
                    <span class="patient-id">ID: ${patientData.patient_id}</span>
                    <span class="patient-age">Age: ${patientData.age}</span>
                    <span class="patient-sex">Sex: ${patientData.sex}</span>
                    <span class="patient-date">Last Visit: ${patientData.last_visit_date || 'N/A'}</span>
                </div>
            </div>
            <div class="patient-actions">
                <button class="btn btn-primary" onclick="patientDashboard.recordVisit('${patientData.name}')">
                    <i class="fas fa-plus"></i> Record Visit
                </button>
                <button class="btn btn-secondary" onclick="patientDashboard.editPatient('${patientData.name}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
            </div>
        `;
    }

    /**
     * Load dental chart for patient
     */
    async loadDentalChart(patientId) {
        try {
            const chartContainer = document.getElementById('dental-chart-container');
            if (!chartContainer) return;

            // Initialize chart wrapper
            this.components.chart.init(chartContainer, patientId);
            
        } catch (error) {
            console.error('Error loading dental chart:', error);
            this.showError('Failed to load dental chart');
        }
    }

    /**
     * Load payment history for patient
     */
    async loadPaymentHistory(patientId) {
        try {
            const paymentContainer = document.getElementById('payment-history-container');
            if (!paymentContainer) return;

            // Initialize payment component
            this.components.payment.init(paymentContainer, patientId);
            await this.components.payment.loadPayments();
            
        } catch (error) {
            console.error('Error loading payment history:', error);
            this.showError('Failed to load payment history');
        }
    }

    /**
     * Load patient summary
     */
    async loadPatientSummary(patientId) {
        try {
            const summaryContainer = document.getElementById('patient-summary-container');
            if (!summaryContainer) return;

            // Initialize summary component
            this.components.summary.init(summaryContainer, patientId);
            await this.components.summary.loadSummary();
            
        } catch (error) {
            console.error('Error loading patient summary:', error);
            this.showError('Failed to load patient summary');
        }
    }

    /**
     * Show patient dashboard section
     */
    showPatientDashboard() {
        const dashboardSection = document.getElementById('patient-dashboard-section');
        const mainDashboard = document.getElementById('main-dashboard');
        
        if (dashboardSection && mainDashboard) {
            mainDashboard.style.display = 'none';
            dashboardSection.style.display = 'block';
        }
    }

    /**
     * Handle dashboard card clicks
     */
    handleCardClick(card) {
        const cardType = card.dataset.type;
        
        switch (cardType) {
            case 'patients':
                this.showPatientList();
                break;
            case 'appointments':
                this.showAppointments();
                break;
            case 'accounts':
                this.showAccounts();
                break;
            case 'stats':
                this.showStatistics();
                break;
        }
    }

    /**
     * Show loading indicator
     */
    showLoading(message = 'Loading...') {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.className = 'loading-overlay';
        loadingDiv.innerHTML = `
            <div class="loading-content">
                <div class="spinner"></div>
                <div class="loading-message">${message}</div>
            </div>
        `;
        document.body.appendChild(loadingDiv);
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        frappe.show_alert(message, 5);
    }

    /**
     * Action methods for dashboard functionality
     */
    createNewPatient() {
        frappe.new_doc('Dental Patient');
    }

    createNewAppointment() {
        frappe.new_doc('Dental Appointment');
    }

    recordVisit(patientId) {
        frappe.new_doc('Dental Appointment', {
            patient: patientId
        });
    }

    editPatient(patientId) {
        frappe.set_route('Form', 'Dental Patient', patientId);
    }

    viewAccounts() {
        frappe.set_route('List', 'Dental Payment Entry');
    }

    viewStatistics() {
        frappe.set_route('List', 'Dental Chart Activity');
    }

    showPatientList() {
        frappe.set_route('List', 'Dental Patient');
    }

    showAppointments() {
        frappe.set_route('List', 'Dental Appointment');
    }
}

/**
 * Patient Search Component
 */
class PatientSearch {
    constructor() {
        this.searchTimeout = null;
    }

    search(query) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }

    async performSearch(query) {
        // Implementation handled by main dashboard
    }
}

/**
 * Patient List Component
 */
class PatientList {
    constructor() {
        this.patients = [];
    }

    render(patients) {
        this.patients = patients;
        // Implementation handled by main dashboard
    }
}

/**
 * Patient Summary Component
 */
class PatientSummary {
    constructor() {
        this.container = null;
        this.patientId = null;
    }

    init(container, patientId) {
        this.container = container;
        this.patientId = patientId;
    }

    async loadSummary() {
        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.get_patient_summary',
                args: { patient_id: this.patientId }
            });

            if (response.message) {
                this.renderSummary(response.message);
            }
        } catch (error) {
            console.error('Error loading patient summary:', error);
        }
    }

    renderSummary(summaryData) {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="summary-header">
                <h3>Patient Summary</h3>
                <div class="summary-actions">
                    <button class="btn btn-sm btn-primary" onclick="patientDashboard.exportSummary()">
                        Export
                    </button>
                </div>
            </div>
            <div class="summary-content">
                ${this.renderSummaryEntries(summaryData.summary_by_date)}
            </div>
        `;
    }

    renderSummaryEntries(entries) {
        if (!entries || entries.length === 0) {
            return '<div class="no-summary">No summary data available</div>';
        }

        return entries.map(entry => `
            <div class="summary-entry" data-date="${entry.date}">
                <div class="summary-date">
                    <h4>${entry.date}</h4>
                    <span class="doctor-name">${entry.doctor || 'Unknown'}</span>
                </div>
                <div class="summary-content">
                    ${entry.chief_complaint ? `<div class="complaint"><strong>Chief Complaint:</strong> ${entry.chief_complaint}</div>` : ''}
                    ${entry.notes ? `<div class="notes"><strong>Notes:</strong> ${entry.notes}</div>` : ''}
                    ${this.renderFindings(entry.findings)}
                    ${this.renderProcedures(entry.procedures)}
                    ${this.renderConditions(entry.conditions)}
                    ${entry.manual_notes ? `<div class="manual-notes"><strong>Manual Notes:</strong> ${entry.manual_notes}</div>` : ''}
                </div>
            </div>
        `).join('');
    }

    renderFindings(findings) {
        if (!findings || findings.length === 0) return '';
        
        return `
            <div class="findings">
                <strong>Findings:</strong>
                <ul>
                    ${findings.map(finding => `<li>${finding}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    renderProcedures(procedures) {
        if (!procedures || procedures.length === 0) return '';
        
        return `
            <div class="procedures">
                <strong>Procedures:</strong>
                <ul>
                    ${procedures.map(proc => `
                        <li>
                            Tooth ${proc.tooth}: ${proc.procedure} (${proc.status}) - $${proc.cost}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    renderConditions(conditions) {
        if (!conditions || conditions.length === 0) return '';
        
        return `
            <div class="conditions">
                <strong>Conditions:</strong>
                <ul>
                    ${conditions.map(cond => `
                        <li>
                            Tooth ${cond.tooth}: ${cond.condition} (${cond.severity})
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
}

/**
 * Dental Chart Wrapper Component
 */
class DentalChartWrapper {
    constructor() {
        this.container = null;
        this.patientId = null;
    }

    init(container, patientId) {
        this.container = container;
        this.patientId = patientId;
        this.loadChart();
    }

    loadChart() {
        if (!this.container) return;

        // Load existing dental chart interface
        this.container.innerHTML = `
            <div class="chart-header">
                <h3>Dental Chart</h3>
                <div class="chart-actions">
                    <button class="btn btn-sm btn-primary" onclick="patientDashboard.saveChart()">
                        Save Changes
                    </button>
                </div>
            </div>
            <div id="dental-chart-visual">
                <!-- Existing chart will be loaded here -->
            </div>
        `;

        // Initialize existing chart functionality
        this.initializeChart();
    }

    initializeChart() {
        // Use existing dental chart functionality
        if (typeof create_interactive_dental_chart !== 'undefined') {
            create_interactive_dental_chart(this.patientId);
        } else {
            console.warn('Dental chart functionality not available');
            this.container.innerHTML += '<div class="chart-error">Dental chart functionality not available</div>';
        }
    }
}

/**
 * Payment History Component
 */
class PaymentHistory {
    constructor() {
        this.container = null;
        this.patientId = null;
    }

    init(container, patientId) {
        this.container = container;
        this.patientId = patientId;
    }

    async loadPayments() {
        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.get_patient_payments',
                args: { patient_id: this.patientId }
            });

            if (response.message) {
                this.renderPayments(response.message);
            }
        } catch (error) {
            console.error('Error loading payments:', error);
        }
    }

    renderPayments(payments) {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="payment-header">
                <h3>Payment History</h3>
                <div class="payment-actions">
                    <button class="btn btn-sm btn-primary" onclick="patientDashboard.recordPayment('${this.patientId}')">
                        Record Payment
                    </button>
                </div>
            </div>
            <div class="payment-content">
                ${this.renderPaymentList(payments)}
            </div>
        `;
    }

    renderPaymentList(payments) {
        if (!payments || payments.length === 0) {
            return '<div class="no-payments">No payment history available</div>';
        }

        return `
            <div class="payment-list">
                ${payments.map(payment => `
                    <div class="payment-item">
                        <div class="payment-date">${payment.date}</div>
                        <div class="payment-amount">$${payment.amount}</div>
                        <div class="payment-status ${payment.status.toLowerCase()}">${payment.status}</div>
                        <div class="payment-description">${payment.description || ''}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.patientDashboard = new PatientDashboard();
});

// Export for global access
window.PatientDashboard = PatientDashboard; 