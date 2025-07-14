/**
 * Dashboard Components
 * Enhanced components for the patient dashboard
 * Implements Phase 3 functionality with better UI/UX
 */

/**
 * Dashboard Cards Component
 * Enhanced card components with better styling and interactions
 */
class DashboardCards {
    constructor() {
        this.cards = {};
        this.init();
    }

    init() {
        this.createCards();
        this.setupCardInteractions();
    }

    createCards() {
        // Patients Card
        this.cards.patients = new PatientsCard();
        
        // Appointments Card
        this.cards.appointments = new AppointmentsCard();
        
        // Accounts Card
        this.cards.accounts = new AccountsCard();
        
        // Statistics Card
        this.cards.statistics = new StatisticsCard();
    }

    setupCardInteractions() {
        // Add hover effects and click handlers
        document.addEventListener('click', (e) => {
            if (e.target.closest('.dashboard-card')) {
                const card = e.target.closest('.dashboard-card');
                this.handleCardClick(card);
            }
        });
    }

    handleCardClick(card) {
        const cardType = card.dataset.type;
        
        // Add visual feedback
        card.classList.add('card-clicked');
        setTimeout(() => card.classList.remove('card-clicked'), 200);
        
        // Handle different card types
        switch (cardType) {
            case 'patients':
                this.showPatientModal();
                break;
            case 'appointments':
                this.showAppointmentModal();
                break;
            case 'accounts':
                this.showAccountsModal();
                break;
            case 'statistics':
                this.showStatisticsModal();
                break;
        }
    }

    showPatientModal() {
        const modal = `
            <div class="modal-overlay" id="patient-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Patient Management</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="quick-actions">
                            <button class="btn btn-primary" onclick="patientDashboard.createNewPatient()">
                                <i class="fas fa-plus"></i> New Patient
                            </button>
                            <button class="btn btn-secondary" onclick="patientDashboard.showPatientList()">
                                <i class="fas fa-list"></i> View All Patients
                            </button>
                        </div>
                        <div class="recent-patients">
                            <h4>Recent Patients</h4>
                            <div id="recent-patients-list">
                                <!-- Recent patients will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modal);
        this.loadRecentPatients();
    }

    async loadRecentPatients() {
        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.get_recent_patients',
                args: { limit: 5 }
            });

            const container = document.getElementById('recent-patients-list');
            if (container && response.message) {
                container.innerHTML = response.message.map(patient => `
                    <div class="recent-patient-item" onclick="patientDashboard.selectPatient('${patient.name}')">
                        <div class="patient-info">
                            <div class="patient-name">${patient.patient_name}</div>
                            <div class="patient-details">ID: ${patient.patient_id}</div>
                        </div>
                        <div class="patient-action">
                            <i class="fas fa-chevron-right"></i>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading recent patients:', error);
        }
    }
}

/**
 * Patients Card Component
 */
class PatientsCard {
    constructor() {
        this.container = null;
    }

    render(container, data) {
        this.container = container;
        this.data = data;
        
        container.innerHTML = `
            <div class="dashboard-card patients-card" data-type="patients">
                <div class="card-header">
                    <h3>Patients</h3>
                    <i class="fas fa-users"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.total_patients || 0}</div>
                    <div class="card-description">Total Patients</div>
                    <div class="card-trend">
                        <span class="trend-indicator ${data.patient_growth >= 0 ? 'positive' : 'negative'}">
                            <i class="fas fa-${data.patient_growth >= 0 ? 'arrow-up' : 'arrow-down'}"></i>
                            ${Math.abs(data.patient_growth || 0)}%
                        </span>
                        <span class="trend-label">vs last month</span>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.createNewPatient()">
                        <i class="fas fa-plus"></i> Add Patient
                    </button>
                </div>
            </div>
        `;
    }
}

/**
 * Appointments Card Component
 */
class AppointmentsCard {
    constructor() {
        this.container = null;
    }

    render(container, data) {
        this.container = container;
        this.data = data;
        
        container.innerHTML = `
            <div class="dashboard-card appointments-card" data-type="appointments">
                <div class="card-header">
                    <h3>Appointments</h3>
                    <i class="fas fa-calendar"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.today_appointments || 0}</div>
                    <div class="card-description">Today's Appointments</div>
                    <div class="appointment-status-summary">
                        <div class="status-item">
                            <span class="status-dot confirmed"></span>
                            <span class="status-count">${data.confirmed_appointments || 0}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-dot completed"></span>
                            <span class="status-count">${data.completed_appointments || 0}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-dot cancelled"></span>
                            <span class="status-count">${data.cancelled_appointments || 0}</span>
                        </div>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.createNewAppointment()">
                        <i class="fas fa-plus"></i> Schedule
                    </button>
                </div>
            </div>
        `;
    }
}

/**
 * Accounts Card Component
 */
class AccountsCard {
    constructor() {
        this.container = null;
    }

    render(container, data) {
        this.container = container;
        this.data = data;
        
        container.innerHTML = `
            <div class="dashboard-card accounts-card" data-type="accounts">
                <div class="card-header">
                    <h3>Accounts</h3>
                    <i class="fas fa-dollar-sign"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">$${data.total_outstanding || 0}</div>
                    <div class="card-description">Outstanding Balance</div>
                    <div class="financial-summary">
                        <div class="summary-item">
                            <span class="label">Today's Revenue:</span>
                            <span class="value">$${data.today_revenue || 0}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Pending Invoices:</span>
                            <span class="value">${data.pending_invoices || 0}</span>
                        </div>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.viewAccounts()">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        `;
    }
}

/**
 * Statistics Card Component
 */
class StatisticsCard {
    constructor() {
        this.container = null;
    }

    render(container, data) {
        this.container = container;
        this.data = data;
        
        container.innerHTML = `
            <div class="dashboard-card stats-card" data-type="stats">
                <div class="card-header">
                    <h3>Statistics</h3>
                    <i class="fas fa-chart-bar"></i>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.completed_treatments || 0}</div>
                    <div class="card-description">Completed Treatments</div>
                    <div class="stats-summary">
                        <div class="stat-item">
                            <span class="stat-label">Active Patients:</span>
                            <span class="stat-value">${data.active_patients || 0}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Avg Treatment Cost:</span>
                            <span class="stat-value">$${data.avg_treatment_cost || 0}</span>
                        </div>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary" onclick="patientDashboard.viewStatistics()">
                        <i class="fas fa-chart-bar"></i> View Report
                    </button>
                </div>
            </div>
        `;
    }
}

/**
 * Enhanced Patient Search Component
 */
class EnhancedPatientSearch {
    constructor() {
        this.searchTimeout = null;
        this.currentQuery = '';
        this.searchResults = [];
        this.init();
    }

    init() {
        this.setupSearchInput();
        this.setupFilters();
        this.setupSearchResults();
    }

    setupSearchInput() {
        const searchInput = document.getElementById('patient-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }

    setupFilters() {
        // Add filter buttons for patient status, age range, etc.
        const filterContainer = document.getElementById('search-filters');
        if (filterContainer) {
            filterContainer.innerHTML = `
                <div class="filter-group">
                    <label>Status:</label>
                    <select id="status-filter">
                        <option value="">All</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Age Range:</label>
                    <select id="age-filter">
                        <option value="">All Ages</option>
                        <option value="0-18">0-18</option>
                        <option value="19-30">19-30</option>
                        <option value="31-50">31-50</option>
                        <option value="51+">51+</option>
                    </select>
                </div>
                <button class="btn btn-secondary" onclick="enhancedPatientSearch.clearFilters()">
                    Clear Filters
                </button>
            `;
        }
    }

    setupSearchResults() {
        const resultsContainer = document.getElementById('patient-search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="search-results-header">
                    <h4>Search Results</h4>
                    <div class="results-count">0 patients found</div>
                </div>
                <div class="search-results-list">
                    <!-- Results will be populated here -->
                </div>
            `;
        }
    }

    handleSearchInput(query) {
        this.currentQuery = query;
        clearTimeout(this.searchTimeout);
        
        if (query.length < 2) {
            this.clearResults();
            return;
        }

        this.searchTimeout = setTimeout(() => {
            this.performSearch();
        }, 300);
    }

    async performSearch() {
        try {
            const filters = this.getActiveFilters();
            
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.search_patients',
                args: { 
                    query: this.currentQuery,
                    filters: filters
                }
            });

            if (response.message) {
                this.searchResults = response.message;
                this.renderSearchResults();
            }
        } catch (error) {
            console.error('Error performing search:', error);
            this.showSearchError();
        }
    }

    getActiveFilters() {
        const statusFilter = document.getElementById('status-filter');
        const ageFilter = document.getElementById('age-filter');
        
        return {
            status: statusFilter ? statusFilter.value : '',
            age_range: ageFilter ? ageFilter.value : ''
        };
    }

    renderSearchResults() {
        const resultsList = document.querySelector('.search-results-list');
        const resultsCount = document.querySelector('.results-count');
        
        if (resultsList && resultsCount) {
            resultsCount.textContent = `${this.searchResults.length} patients found`;
            
            resultsList.innerHTML = this.searchResults.map(patient => `
                <div class="search-result-item" onclick="patientDashboard.selectPatient('${patient.name}')">
                    <div class="patient-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="patient-info">
                        <div class="patient-name">${patient.patient_name}</div>
                        <div class="patient-details">
                            <span class="patient-id">ID: ${patient.patient_id}</span>
                            <span class="patient-age">Age: ${patient.age}</span>
                            <span class="patient-sex">${patient.sex}</span>
                        </div>
                        <div class="patient-status ${patient.status.toLowerCase()}">
                            ${patient.status}
                        </div>
                    </div>
                    <div class="patient-actions">
                        <button class="btn btn-sm btn-primary" onclick="patientDashboard.selectPatient('${patient.name}')">
                            Select
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="patientDashboard.editPatient('${patient.name}')">
                            Edit
                        </button>
                    </div>
                </div>
            `).join('');
        }
    }

    clearResults() {
        const resultsList = document.querySelector('.search-results-list');
        const resultsCount = document.querySelector('.results-count');
        
        if (resultsList) resultsList.innerHTML = '';
        if (resultsCount) resultsCount.textContent = '0 patients found';
    }

    clearFilters() {
        const statusFilter = document.getElementById('status-filter');
        const ageFilter = document.getElementById('age-filter');
        
        if (statusFilter) statusFilter.value = '';
        if (ageFilter) ageFilter.value = '';
        
        this.performSearch();
    }

    showSearchError() {
        const resultsList = document.querySelector('.search-results-list');
        if (resultsList) {
            resultsList.innerHTML = `
                <div class="search-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Error loading search results. Please try again.</span>
                </div>
            `;
        }
    }
}

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardCards = new DashboardCards();
    window.enhancedPatientSearch = new EnhancedPatientSearch();
});

// Export components for global access
window.DashboardCards = DashboardCards;
window.EnhancedPatientSearch = EnhancedPatientSearch; 