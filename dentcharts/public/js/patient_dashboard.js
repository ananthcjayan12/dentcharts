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
        
        // Try frappe.call first, then fetch API
        if (typeof frappe !== 'undefined' && frappe.call) {
            console.log('Using frappe.call to load dashboard data...');
            this.loadDataWithFrappe();
        } else {
            console.log('Using fetch API to load dashboard data...');
            this.loadDataWithFetch();
        }
    },

    // Load data using frappe.call
    loadDataWithFrappe: function() {
        frappe.call({
            method: 'dentcharts.templates.pages.patient_dashboard.get_dashboard_data',
            callback: (response) => {
                console.log('Frappe API Response:', response);
                this.handleApiResponse(response.message);
            },
            error: (error) => {
                console.error('Frappe API failed:', error);
                this.hideLoading();
                throw error; // Don't fallback, let the error be visible
            }
        });
    },

    // Load data using fetch API
    loadDataWithFetch: function() {
        const self = this;
        console.log('Making fetch API request to get dashboard data...');
        
        fetch('/api/method/dentcharts.templates.pages.patient_dashboard.get_dashboard_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': this.getCSRFToken()
            }
        })
        .then(response => {
            console.log('Fetch API response status:', response.status);
            console.log('Fetch API response headers:', response.headers);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Fetch API Response:', data);
            self.handleApiResponse(data.message);
        })
        .catch(error => {
            console.error('Fetch API failed:', error);
            this.hideLoading();
            throw error; // Don't fallback, let the error be visible
        })
        .finally(() => {
            self.hideLoading();
        });
    },

    // Handle API response from either method
    handleApiResponse: function(responseData) {
        if (responseData && responseData.success && responseData.data) {
            console.log('Successfully loaded real data:', responseData.data);
            this.updateDashboardCards(responseData.data);
            this.loadPatientList();
            this.loadRecentActivity(responseData.data.recent_activity);
        } else {
            console.error('API returned unsuccessful response:', responseData);
            throw new Error('API returned unsuccessful response');
        }
    },

    // Get CSRF token for fetch requests
    getCSRFToken: function() {
        const tokenElement = document.querySelector('meta[name="csrf-token"]');
        return tokenElement ? tokenElement.getAttribute('content') : '';
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

        // Update payments card - Fixed to use new structure
        if (data.payment_stats) {
            const totalReceivedEl = document.getElementById('total-received');
            const receivedPaymentsEl = document.getElementById('received-payments');
            const recentPaymentsEl = document.getElementById('recent-payments');
            
            // Use total_received instead of outstanding_balance
            if (totalReceivedEl) totalReceivedEl.textContent = this.formatCurrency(data.payment_stats.total_received || 0);
            if (receivedPaymentsEl) receivedPaymentsEl.textContent = this.formatCurrency(data.payment_stats.received_this_month || 0);
            if (recentPaymentsEl) recentPaymentsEl.textContent = data.payment_stats.recent_payments || 0;
        }
    },

    // Load patient list
    loadPatientList: function(searchTerm = '') {
        console.log('Loading patient list with search term:', searchTerm);
        
        const loadPatients = (response) => {
            console.log('Patient list response:', response);
            if (response && response.success) {
                console.log('Successfully loaded patient list:', response.patients);
                this.displayPatientList(response.patients);
            } else {
                console.error('Failed to load patient list:', response);
                throw new Error('Failed to load patient list');
            }
        };

        if (typeof frappe !== 'undefined' && frappe.call) {
            frappe.call({
                method: 'dentcharts.templates.pages.patient_dashboard.get_patient_list',
                args: { search_term: searchTerm, limit: 20 },
                callback: (response) => loadPatients(response.message),
                error: (error) => {
                    console.error('Frappe call failed:', error);
                    throw error;
                }
            });
        } else {
            fetch('/api/method/dentcharts.templates.pages.patient_dashboard.get_patient_list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': this.getCSRFToken()
                },
                body: JSON.stringify({ search_term: searchTerm, limit: 20 })
            })
            .then(response => response.json())
            .then(data => loadPatients(data.message))
            .catch(error => {
                console.error('Fetch failed:', error);
                throw error;
            });
        }
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
                    <div class="activity-patient">${activity.patient || 'Unknown Patient'}</div>
                    <div class="activity-details">
                        ${activity.status || 'Appointment'} - ${activity.practitioner || 'Unknown Doctor'}
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
        // Navigate to individual patient detail dashboard
        window.location.href = `/patient-detail/${patientId}`;
    },

    editPatient: function(patientId) {
        console.log('Editing patient:', patientId);
        // Navigate to dental patient form in edit mode
        window.location.href = `/app/dental-patient/${patientId}`;
    },

    viewAllPatients: function() {
        console.log('Viewing all patients');
        // Navigate to dental patients list
        window.location.href = '/app/dental-patient';
    },

    viewAllAppointments: function() {
        console.log('Viewing all appointments');
        // Navigate to dental appointments list
        window.location.href = '/app/dental-appointment';
    },

    viewPaymentReports: function() {
        console.log('Viewing payment reports');
        // Navigate to dental payment entries list
        window.location.href = '/app/dental-payment-entry';
    },

    // Quick actions
    createNewPatient: function() {
        console.log('Creating new patient');
        // Navigate to new dental patient form
        window.open('/app/dental-patient/new', '_blank');
    },

    scheduleAppointment: function() {
        console.log('Scheduling appointment');
        // Navigate to new dental appointment form  
        window.open('/app/dental-appointment/new', '_blank');
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
