// Patient Dashboard JavaScript - Simple and Reusable

const PatientDashboard = {
    // Initialize dashboard
    init: function() {
        console.log('Patient Dashboard JavaScript loaded');
        this.loadDashboardData();
        this.setupEventListeners();
        this.setupSearch();
    },

    // Load dashboard data from backend
    loadDashboardData: function() {
        console.log('Loading dashboard data...');
        this.showLoading();
        
        // Use frappe.call to get dashboard data
        if (typeof frappe !== 'undefined') {
            frappe.call({
                method: 'dentcharts.patient_management.patient_dashboard.get_dashboard_data',
                callback: (response) => {
                    if (response.message && response.message.success) {
                        this.updateDashboardCards(response.message.data);
                        this.loadPatientList();
                        this.loadRecentActivity(response.message.data.recent_activity);
                    } else {
                        console.error('Failed to load dashboard data:', response.message);
                        this.loadSampleData();
                    }
                    this.hideLoading();
                },
                error: (error) => {
                    console.error('Error loading dashboard data:', error);
                    this.loadSampleData();
                    this.hideLoading();
                }
            });
        } else {
            // Load sample data if frappe is not available
            this.loadSampleData();
        }
    },

    // Load sample data for testing
    loadSampleData: function() {
        console.log('Loading sample data...');
        setTimeout(() => {
            this.updateDashboardCards({
                patient_stats: {
                    total: 150,
                    active: 120,
                    new_this_month: 25
                },
                appointment_stats: {
                    today: 12,
                    upcoming: 8,
                    completed_this_month: 45
                },
                payment_stats: {
                    outstanding: 5420,
                    received_this_month: 12500,
                    recent_payments: 8
                }
            });
            this.loadSamplePatientList();
            this.loadSampleActivity();
            this.hideLoading();
        }, 1000);
    },

    // Update dashboard cards with data
    updateDashboardCards: function(data) {
        console.log('Updating dashboard cards with data:', data);
        
        // Update patients card
        if (data.patient_stats) {
            const totalPatientsEl = document.getElementById('total-patients');
            const activePatientsEl = document.getElementById('active-patients');
            const newPatientsEl = document.getElementById('new-patients');
            
            if (totalPatientsEl) totalPatientsEl.textContent = data.patient_stats.total || 0;
            if (activePatientsEl) activePatientsEl.textContent = data.patient_stats.active || 0;
            if (newPatientsEl) newPatientsEl.textContent = data.patient_stats.new_this_month || 0;
        }

        // Update appointments card
        if (data.appointment_stats) {
            const todayAppointmentsEl = document.getElementById('today-appointments');
            const upcomingAppointmentsEl = document.getElementById('upcoming-appointments');
            const completedAppointmentsEl = document.getElementById('completed-appointments');
            
            if (todayAppointmentsEl) todayAppointmentsEl.textContent = data.appointment_stats.today || 0;
            if (upcomingAppointmentsEl) upcomingAppointmentsEl.textContent = data.appointment_stats.upcoming || 0;
            if (completedAppointmentsEl) completedAppointmentsEl.textContent = data.appointment_stats.completed_this_month || 0;
        }

        // Update payments card
        if (data.payment_stats) {
            const outstandingBalanceEl = document.getElementById('outstanding-balance');
            const receivedPaymentsEl = document.getElementById('received-payments');
            const recentPaymentsEl = document.getElementById('recent-payments');
            
            if (outstandingBalanceEl) outstandingBalanceEl.textContent = this.formatCurrency(data.payment_stats.outstanding || 0);
            if (receivedPaymentsEl) receivedPaymentsEl.textContent = this.formatCurrency(data.payment_stats.received_this_month || 0);
            if (recentPaymentsEl) recentPaymentsEl.textContent = data.payment_stats.recent_payments || 0;
        }
    },

    // Load patient list
    loadPatientList: function(searchTerm = '') {
        if (typeof frappe !== 'undefined') {
            frappe.call({
                method: 'dentcharts.patient_management.patient_dashboard.get_patient_list',
                args: {
                    search_term: searchTerm,
                    limit: 20
                },
                callback: (response) => {
                    if (response.message && response.message.success) {
                        this.displayPatientList(response.message.patients);
                    } else {
                        console.error('Failed to load patient list');
                        this.loadSamplePatientList();
                    }
                },
                error: (error) => {
                    console.error('Error loading patient list:', error);
                    this.loadSamplePatientList();
                }
            });
        } else {
            this.loadSamplePatientList();
        }
    },

    // Load sample patient list
    loadSamplePatientList: function() {
        const samplePatients = [
            {
                name: 'PAT-001',
                patient_name: 'John Doe',
                age: 35,
                mobile_number: '555-0123',
                email: 'john.doe@email.com',
                modified: '2024-07-10'
            },
            {
                name: 'PAT-002',
                patient_name: 'Jane Smith',
                age: 28,
                mobile_number: '555-0456',
                email: 'jane.smith@email.com',
                modified: '2024-07-08'
            },
            {
                name: 'PAT-003',
                patient_name: 'Bob Johnson',
                age: 45,
                mobile_number: '555-0789',
                email: 'bob.johnson@email.com',
                modified: '2024-07-05'
            }
        ];
        this.displayPatientList(samplePatients);
    },

    // Display patient list in table
    displayPatientList: function(patients) {
        const tbody = document.getElementById('patient-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';

        if (patients.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: #7f8c8d;">
                        No patients found
                    </td>
                </tr>
            `;
            return;
        }

        patients.forEach(patient => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="patient-name">${patient.patient_name || 'N/A'}</div>
                    <div class="patient-contact">${patient.email || 'No email'}</div>
                </td>
                <td>${patient.age || 'N/A'}</td>
                <td>
                    <div class="patient-contact">${patient.mobile_number || 'N/A'}</div>
                </td>
                <td>${this.formatDate(patient.modified)}</td>
                <td>
                    <div class="patient-actions">
                        <button class="action-btn view" onclick="PatientDashboard.viewPatient('${patient.name}')">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="action-btn edit" onclick="PatientDashboard.editPatient('${patient.name}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    },

    // Load sample activity
    loadSampleActivity: function() {
        const activities = [
            {
                patient_name: 'John Doe',
                appointment_status: 'Completed',
                practitioner: 'Dr. Smith',
                appointment_date: '2024-07-15',
                appointment_time: '10:00'
            },
            {
                patient_name: 'Jane Smith',
                appointment_status: 'Scheduled',
                practitioner: 'Dr. Johnson',
                appointment_date: '2024-07-15',
                appointment_time: '14:00'
            }
        ];
        this.loadRecentActivity(activities);
    },

    // Load recent activity
    loadRecentActivity: function(activities) {
        const activityList = document.getElementById('recent-activity-list');
        if (!activityList) return;
        
        activityList.innerHTML = '';

        if (!activities || activities.length === 0) {
            activityList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-details">No recent activity</div>
                    </div>
                </div>
            `;
            return;
        }

        activities.forEach(activity => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-info">
                    <div class="activity-patient">${activity.patient_name || 'Unknown Patient'}</div>
                    <div class="activity-details">
                        ${activity.appointment_status || 'Appointment'} - ${activity.practitioner || 'Unknown Doctor'}
                    </div>
                </div>
                <div class="activity-time">${this.formatDateTime(activity.appointment_date, activity.appointment_time)}</div>
            `;
            activityList.appendChild(activityItem);
        });
    },

    // Setup event listeners
    setupEventListeners: function() {
        console.log('Setting up event listeners...');
        
        // Card click handlers
        const patientsCard = document.getElementById('patients-card');
        if (patientsCard) {
            patientsCard.addEventListener('click', () => {
                this.viewAllPatients();
            });
        }

        const appointmentsCard = document.getElementById('appointments-card');
        if (appointmentsCard) {
            appointmentsCard.addEventListener('click', () => {
                this.viewAllAppointments();
            });
        }

        const paymentsCard = document.getElementById('payments-card');
        if (paymentsCard) {
            paymentsCard.addEventListener('click', () => {
                this.viewPaymentReports();
            });
        }
    },

    // Setup search functionality
    setupSearch: function() {
        const searchInput = document.getElementById('patient-search');
        if (searchInput) {
            let searchTimeout;

            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.loadPatientList(e.target.value);
                }, 300); // Debounce search
            });
        }
    },

    // Patient actions
    viewPatient: function(patientId) {
        console.log('Viewing patient:', patientId);
        // Navigate to individual patient dashboard
        window.location.href = `/app/patient-dashboard/${patientId}`;
    },

    editPatient: function(patientId) {
        console.log('Editing patient:', patientId);
        // Navigate to patient edit form
        window.location.href = `/app/dental-patient/${patientId}`;
    },

    viewAllPatients: function() {
        console.log('Viewing all patients');
        // Navigate to patients list
        window.location.href = '/app/dental-patient';
    },

    viewAllAppointments: function() {
        console.log('Viewing all appointments');
        // Navigate to appointments list
        window.location.href = '/app/dental-appointment';
    },

    viewPaymentReports: function() {
        console.log('Viewing payment reports');
        // Navigate to payment reports
        window.location.href = '/app/dental-payment-entry';
    },

    // Quick actions
    createNewPatient: function() {
        console.log('Creating new patient');
        // Navigate to new patient form
        window.location.href = '/app/dental-patient/new';
    },

    scheduleAppointment: function() {
        console.log('Scheduling appointment');
        // Navigate to new appointment form
        window.location.href = '/app/dental-appointment/new';
    },

    // Utility functions
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
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

    formatDateTime: function(dateStr, timeStr) {
        if (!dateStr) return 'N/A';
        const date = new Date(dateStr);
        let result = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
        
        if (timeStr) {
            result += ` ${timeStr}`;
        }
        
        return result;
    },

    // Loading and error handling
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
        console.error('Dashboard Error:', message);
        // Show error message using frappe's messaging system
        if (typeof frappe !== 'undefined' && frappe.msgprint) {
            frappe.msgprint({
                title: 'Error',
                message: message,
                indicator: 'red'
            });
        } else {
            alert(message);
        }
    },

    showSuccess: function(message) {
        console.log('Dashboard Success:', message);
        // Show success message using frappe's messaging system
        if (typeof frappe !== 'undefined' && frappe.msgprint) {
            frappe.msgprint({
                title: 'Success',
                message: message,
                indicator: 'green'
            });
        } else {
            alert(message);
        }
    }
};

// Global function bindings for HTML onclick events
function createNewPatient() {
    PatientDashboard.createNewPatient();
}

function scheduleAppointment() {
    PatientDashboard.scheduleAppointment();
}

function viewAllPatients() {
    PatientDashboard.viewAllPatients();
}

function viewAllAppointments() {
    PatientDashboard.viewAllAppointments();
}

function viewPaymentReports() {
    PatientDashboard.viewPaymentReports();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    PatientDashboard.init();
});

// Auto-initialize if frappe is available
if (typeof frappe !== 'undefined') {
    frappe.ready(() => {
        PatientDashboard.init();
    });
}
