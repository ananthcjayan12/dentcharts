/**
 * Chart Integration
 * Integrates existing dental chart functionality with enhanced UI
 * Implements Phase 4 functionality for seamless chart integration
 */

/**
 * Enhanced Dental Chart Wrapper
 * Wraps existing chart functionality with better positioning and styling
 */
class EnhancedDentalChartWrapper {
    constructor() {
        this.container = null;
        this.patientId = null;
        this.chartInstance = null;
        this.isInitialized = false;
        this.init();
    }

    init() {
        this.setupChartContainer();
        this.setupChartControls();
        this.setupChartEvents();
    }

    setupChartContainer() {
        // Create enhanced chart container with better styling
        const chartContainer = document.getElementById('dental-chart-container');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="chart-wrapper">
                    <div class="chart-header">
                        <h3>Dental Chart</h3>
                        <div class="chart-controls">
                            <button class="btn btn-sm btn-primary" id="save-chart-btn">
                                <i class="fas fa-save"></i> Save Changes
                            </button>
                            <button class="btn btn-sm btn-secondary" id="reset-chart-btn">
                                <i class="fas fa-undo"></i> Reset
                            </button>
                            <button class="btn btn-sm btn-outline" id="print-chart-btn">
                                <i class="fas fa-print"></i> Print
                            </button>
                        </div>
                    </div>
                    <div class="chart-content">
                        <div class="chart-toolbar">
                            <div class="tool-group">
                                <label>Dentition Type:</label>
                                <select id="dentition-type">
                                    <option value="permanent">Permanent</option>
                                    <option value="primary">Primary</option>
                                    <option value="mixed">Mixed</option>
                                </select>
                            </div>
                            <div class="tool-group">
                                <label>View:</label>
                                <select id="chart-view">
                                    <option value="full">Full Chart</option>
                                    <option value="upper">Upper Only</option>
                                    <option value="lower">Lower Only</option>
                                </select>
                            </div>
                            <div class="tool-group">
                                <button class="btn btn-sm btn-info" id="zoom-in-btn">
                                    <i class="fas fa-search-plus"></i>
                                </button>
                                <button class="btn btn-sm btn-info" id="zoom-out-btn">
                                    <i class="fas fa-search-minus"></i>
                                </button>
                                <button class="btn btn-sm btn-info" id="reset-zoom-btn">
                                    <i class="fas fa-expand"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-main">
                            <div id="dental-chart-visual" class="chart-visual">
                                <!-- Existing chart will be loaded here -->
                            </div>
                            <div class="chart-sidebar">
                                <div class="chart-info">
                                    <h4>Selected Tooth</h4>
                                    <div id="tooth-info">
                                        <p>Click on a tooth to view details</p>
                                    </div>
                                </div>
                                <div class="chart-actions">
                                    <h4>Quick Actions</h4>
                                    <div class="action-buttons">
                                        <button class="btn btn-sm btn-primary" id="add-condition-btn">
                                            <i class="fas fa-plus"></i> Add Condition
                                        </button>
                                        <button class="btn btn-sm btn-primary" id="add-procedure-btn">
                                            <i class="fas fa-stethoscope"></i> Add Procedure
                                        </button>
                                        <button class="btn btn-sm btn-secondary" id="add-note-btn">
                                            <i class="fas fa-sticky-note"></i> Add Note
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    setupChartControls() {
        // Setup control event listeners
        const saveBtn = document.getElementById('save-chart-btn');
        const resetBtn = document.getElementById('reset-chart-btn');
        const printBtn = document.getElementById('print-chart-btn');
        const dentitionSelect = document.getElementById('dentition-type');
        const viewSelect = document.getElementById('chart-view');
        const zoomInBtn = document.getElementById('zoom-in-btn');
        const zoomOutBtn = document.getElementById('zoom-out-btn');
        const resetZoomBtn = document.getElementById('reset-zoom-btn');

        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveChartChanges());
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetChart());
        }

        if (printBtn) {
            printBtn.addEventListener('click', () => this.printChart());
        }

        if (dentitionSelect) {
            dentitionSelect.addEventListener('change', (e) => {
                this.changeDentitionType(e.target.value);
            });
        }

        if (viewSelect) {
            viewSelect.addEventListener('change', (e) => {
                this.changeChartView(e.target.value);
            });
        }

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.zoomIn());
        }

        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.zoomOut());
        }

        if (resetZoomBtn) {
            resetZoomBtn.addEventListener('click', () => this.resetZoom());
        }
    }

    setupChartEvents() {
        // Setup chart interaction events
        document.addEventListener('click', (e) => {
            if (e.target.closest('.tooth')) {
                this.handleToothClick(e.target.closest('.tooth'));
            }
        });

        // Setup action button events
        const addConditionBtn = document.getElementById('add-condition-btn');
        const addProcedureBtn = document.getElementById('add-procedure-btn');
        const addNoteBtn = document.getElementById('add-note-btn');

        if (addConditionBtn) {
            addConditionBtn.addEventListener('click', () => this.addCondition());
        }

        if (addProcedureBtn) {
            addProcedureBtn.addEventListener('click', () => this.addProcedure());
        }

        if (addNoteBtn) {
            addNoteBtn.addEventListener('click', () => this.addNote());
        }
    }

    loadChart(patientId) {
        this.patientId = patientId;
        
        if (!this.isInitialized) {
            this.initializeChart();
        } else {
            this.updateChartData();
        }
    }

    initializeChart() {
        try {
            const chartVisual = document.getElementById('dental-chart-visual');
            if (!chartVisual) {
                console.error('Chart visual container not found');
                return;
            }

            // Check if existing chart functionality is available
            if (typeof create_interactive_dental_chart !== 'undefined') {
                // Initialize existing chart
                this.chartInstance = create_interactive_dental_chart(this.patientId);
                this.isInitialized = true;
                
                // Apply enhanced styling
                this.applyEnhancedStyling();
                
                // Setup chart data sync
                this.setupDataSync();
                
                console.log('Dental chart initialized successfully');
            } else {
                console.warn('Dental chart functionality not available');
                this.showChartError('Dental chart functionality not available');
            }
        } catch (error) {
            console.error('Error initializing dental chart:', error);
            this.showChartError('Failed to initialize dental chart');
        }
    }

    applyEnhancedStyling() {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            // Add enhanced styling classes
            chartContainer.classList.add('enhanced-chart');
            
            // Apply responsive styling
            this.applyResponsiveStyling();
            
            // Apply accessibility improvements
            this.applyAccessibilityImprovements();
        }
    }

    applyResponsiveStyling() {
        // Add responsive chart styling
        const style = document.createElement('style');
        style.textContent = `
            .enhanced-chart {
                max-width: 100%;
                height: auto;
                overflow: hidden;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .chart-wrapper {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.1);
                margin: 20px 0;
            }
            
            .chart-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid #e0e0e0;
                background: #f8f9fa;
                border-radius: 8px 8px 0 0;
            }
            
            .chart-controls {
                display: flex;
                gap: 10px;
            }
            
            .chart-content {
                padding: 20px;
            }
            
            .chart-toolbar {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
                flex-wrap: wrap;
            }
            
            .tool-group {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .chart-main {
                display: grid;
                grid-template-columns: 1fr 300px;
                gap: 20px;
                min-height: 500px;
            }
            
            .chart-visual {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .chart-sidebar {
                background: #f8f9fa;
                border-radius: 6px;
                padding: 20px;
            }
            
            .chart-info h4,
            .chart-actions h4 {
                margin-bottom: 15px;
                color: #333;
                font-size: 16px;
            }
            
            .action-buttons {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            @media (max-width: 768px) {
                .chart-main {
                    grid-template-columns: 1fr;
                }
                
                .chart-toolbar {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .tool-group {
                    justify-content: space-between;
                }
            }
        `;
        document.head.appendChild(style);
    }

    applyAccessibilityImprovements() {
        // Add ARIA labels and keyboard navigation
        const chartElements = document.querySelectorAll('.tooth');
        chartElements.forEach((tooth, index) => {
            tooth.setAttribute('tabindex', '0');
            tooth.setAttribute('role', 'button');
            tooth.setAttribute('aria-label', `Tooth ${index + 1}`);
            
            tooth.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.handleToothClick(tooth);
                }
            });
        });
    }

    setupDataSync() {
        // Setup real-time data synchronization
        if (this.chartInstance && typeof this.chartInstance.onDataChange === 'function') {
            this.chartInstance.onDataChange((data) => {
                this.updateChartDisplay(data);
            });
        }
    }

    updateChartData() {
        if (this.chartInstance && typeof this.chartInstance.updateData === 'function') {
            this.chartInstance.updateData(this.patientId);
        }
    }

    handleToothClick(toothElement) {
        const toothNumber = toothElement.dataset.toothNumber;
        if (toothNumber) {
            this.showToothInfo(toothNumber);
            this.highlightTooth(toothElement);
        }
    }

    showToothInfo(toothNumber) {
        const toothInfo = document.getElementById('tooth-info');
        if (toothInfo) {
            // Load tooth information from existing data
            this.loadToothData(toothNumber).then(data => {
                toothInfo.innerHTML = `
                    <div class="tooth-details">
                        <h5>Tooth ${toothNumber}</h5>
                        <div class="tooth-conditions">
                            <strong>Conditions:</strong>
                            <ul>
                                ${data.conditions ? data.conditions.map(cond => 
                                    `<li>${cond.condition} (${cond.severity})</li>`
                                ).join('') : '<li>No conditions</li>'}
                            </ul>
                        </div>
                        <div class="tooth-procedures">
                            <strong>Procedures:</strong>
                            <ul>
                                ${data.procedures ? data.procedures.map(proc => 
                                    `<li>${proc.procedure} (${proc.status}) - $${proc.cost}</li>`
                                ).join('') : '<li>No procedures</li>'}
                            </ul>
                        </div>
                        <div class="tooth-notes">
                            <strong>Notes:</strong>
                            <p>${data.notes || 'No notes'}</p>
                        </div>
                    </div>
                `;
            });
        }
    }

    async loadToothData(toothNumber) {
        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.get_tooth_data',
                args: { 
                    patient_id: this.patientId,
                    tooth_number: toothNumber
                }
            });

            return response.message || { conditions: [], procedures: [], notes: '' };
        } catch (error) {
            console.error('Error loading tooth data:', error);
            return { conditions: [], procedures: [], notes: '' };
        }
    }

    highlightTooth(toothElement) {
        // Remove previous highlights
        document.querySelectorAll('.tooth').forEach(tooth => {
            tooth.classList.remove('selected');
        });
        
        // Add highlight to selected tooth
        toothElement.classList.add('selected');
    }

    saveChartChanges() {
        try {
            if (this.chartInstance && typeof this.chartInstance.save === 'function') {
                this.chartInstance.save();
                this.showSuccess('Chart changes saved successfully');
            } else {
                // Fallback to manual save
                this.manualSave();
            }
        } catch (error) {
            console.error('Error saving chart changes:', error);
            this.showError('Failed to save chart changes');
        }
    }

    async manualSave() {
        try {
            const chartData = this.getChartData();
            
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.save_chart_data',
                args: {
                    patient_id: this.patientId,
                    chart_data: chartData
                }
            });

            if (response.message) {
                this.showSuccess('Chart changes saved successfully');
            }
        } catch (error) {
            console.error('Error saving chart data:', error);
            this.showError('Failed to save chart data');
        }
    }

    getChartData() {
        // Extract chart data from DOM or chart instance
        const chartData = {
            patient_id: this.patientId,
            teeth_data: {},
            last_updated: new Date().toISOString()
        };

        // Get data from each tooth element
        document.querySelectorAll('.tooth').forEach(tooth => {
            const toothNumber = tooth.dataset.toothNumber;
            if (toothNumber) {
                chartData.teeth_data[toothNumber] = {
                    conditions: tooth.dataset.conditions ? JSON.parse(tooth.dataset.conditions) : [],
                    procedures: tooth.dataset.procedures ? JSON.parse(tooth.dataset.procedures) : [],
                    notes: tooth.dataset.notes || ''
                };
            }
        });

        return chartData;
    }

    resetChart() {
        if (confirm('Are you sure you want to reset the chart? This will clear all changes.')) {
            try {
                if (this.chartInstance && typeof this.chartInstance.reset === 'function') {
                    this.chartInstance.reset();
                } else {
                    this.manualReset();
                }
                this.showSuccess('Chart reset successfully');
            } catch (error) {
                console.error('Error resetting chart:', error);
                this.showError('Failed to reset chart');
            }
        }
    }

    async manualReset() {
        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.reset_chart_data',
                args: { patient_id: this.patientId }
            });

            if (response.message) {
                this.loadChart(this.patientId);
            }
        } catch (error) {
            console.error('Error resetting chart data:', error);
            this.showError('Failed to reset chart data');
        }
    }

    printChart() {
        const printWindow = window.open('', '_blank');
        const chartContainer = document.getElementById('dental-chart-visual');
        
        if (printWindow && chartContainer) {
            printWindow.document.write(`
                <html>
                    <head>
                        <title>Dental Chart - Patient ${this.patientId}</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 20px; }
                            .chart-header { text-align: center; margin-bottom: 20px; }
                            .chart-content { margin: 20px 0; }
                            @media print { 
                                body { margin: 0; }
                                .chart-content { page-break-inside: avoid; }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="chart-header">
                            <h1>Dental Chart</h1>
                            <h2>Patient ID: ${this.patientId}</h2>
                            <p>Date: ${new Date().toLocaleDateString()}</p>
                        </div>
                        <div class="chart-content">
                            ${chartContainer.innerHTML}
                        </div>
                    </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        }
    }

    changeDentitionType(type) {
        try {
            if (this.chartInstance && typeof this.chartInstance.setDentitionType === 'function') {
                this.chartInstance.setDentitionType(type);
            } else {
                // Update chart display manually
                this.updateDentitionDisplay(type);
            }
        } catch (error) {
            console.error('Error changing dentition type:', error);
        }
    }

    updateDentitionDisplay(type) {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            chartContainer.dataset.dentitionType = type;
            // Apply visual changes based on dentition type
            this.applyDentitionStyling(type);
        }
    }

    applyDentitionStyling(type) {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            // Remove existing dentition classes
            chartContainer.classList.remove('permanent', 'primary', 'mixed');
            // Add new dentition class
            chartContainer.classList.add(type);
        }
    }

    changeChartView(view) {
        try {
            if (this.chartInstance && typeof this.chartInstance.setView === 'function') {
                this.chartInstance.setView(view);
            } else {
                // Update chart display manually
                this.updateChartView(view);
            }
        } catch (error) {
            console.error('Error changing chart view:', error);
        }
    }

    updateChartView(view) {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            chartContainer.dataset.view = view;
            // Apply visual changes based on view
            this.applyViewStyling(view);
        }
    }

    applyViewStyling(view) {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            // Remove existing view classes
            chartContainer.classList.remove('full', 'upper', 'lower');
            // Add new view class
            chartContainer.classList.add(view);
        }
    }

    zoomIn() {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            const currentScale = parseFloat(chartContainer.style.transform.replace('scale(', '').replace(')', '')) || 1;
            chartContainer.style.transform = `scale(${Math.min(currentScale * 1.2, 3)})`;
        }
    }

    zoomOut() {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            const currentScale = parseFloat(chartContainer.style.transform.replace('scale(', '').replace(')', '')) || 1;
            chartContainer.style.transform = `scale(${Math.max(currentScale / 1.2, 0.5)})`;
        }
    }

    resetZoom() {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            chartContainer.style.transform = 'scale(1)';
        }
    }

    addCondition() {
        this.showConditionModal();
    }

    addProcedure() {
        this.showProcedureModal();
    }

    addNote() {
        this.showNoteModal();
    }

    showConditionModal() {
        const modal = `
            <div class="modal-overlay" id="condition-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Add Condition</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <form id="condition-form">
                            <div class="form-group">
                                <label>Condition Type:</label>
                                <select id="condition-type" required>
                                    <option value="">Select Condition</option>
                                    <option value="caries">Caries</option>
                                    <option value="fracture">Fracture</option>
                                    <option value="mobility">Mobility</option>
                                    <option value="sensitivity">Sensitivity</option>
                                    <option value="discoloration">Discoloration</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Severity:</label>
                                <select id="condition-severity" required>
                                    <option value="">Select Severity</option>
                                    <option value="mild">Mild</option>
                                    <option value="moderate">Moderate</option>
                                    <option value="severe">Severe</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Notes:</label>
                                <textarea id="condition-notes" rows="3"></textarea>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">Add Condition</button>
                                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modal);
        
        // Setup form submission
        const form = document.getElementById('condition-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitCondition();
            });
        }
    }

    showProcedureModal() {
        const modal = `
            <div class="modal-overlay" id="procedure-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Add Procedure</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <form id="procedure-form">
                            <div class="form-group">
                                <label>Procedure Type:</label>
                                <select id="procedure-type" required>
                                    <option value="">Select Procedure</option>
                                    <option value="filling">Filling</option>
                                    <option value="extraction">Extraction</option>
                                    <option value="root_canal">Root Canal</option>
                                    <option value="crown">Crown</option>
                                    <option value="cleaning">Cleaning</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Status:</label>
                                <select id="procedure-status" required>
                                    <option value="">Select Status</option>
                                    <option value="planned">Planned</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Cost:</label>
                                <input type="number" id="procedure-cost" min="0" step="0.01" required>
                            </div>
                            <div class="form-group">
                                <label>Notes:</label>
                                <textarea id="procedure-notes" rows="3"></textarea>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">Add Procedure</button>
                                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modal);
        
        // Setup form submission
        const form = document.getElementById('procedure-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitProcedure();
            });
        }
    }

    showNoteModal() {
        const modal = `
            <div class="modal-overlay" id="note-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Add Note</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <form id="note-form">
                            <div class="form-group">
                                <label>Note:</label>
                                <textarea id="note-content" rows="5" required></textarea>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">Add Note</button>
                                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modal);
        
        // Setup form submission
        const form = document.getElementById('note-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitNote();
            });
        }
    }

    async submitCondition() {
        const conditionType = document.getElementById('condition-type').value;
        const severity = document.getElementById('condition-severity').value;
        const notes = document.getElementById('condition-notes').value;

        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.add_tooth_condition',
                args: {
                    patient_id: this.patientId,
                    tooth_number: this.getSelectedTooth(),
                    condition_type: conditionType,
                    severity: severity,
                    notes: notes
                }
            });

            if (response.message) {
                this.showSuccess('Condition added successfully');
                document.getElementById('condition-modal').remove();
                this.updateChartDisplay();
            }
        } catch (error) {
            console.error('Error adding condition:', error);
            this.showError('Failed to add condition');
        }
    }

    async submitProcedure() {
        const procedureType = document.getElementById('procedure-type').value;
        const status = document.getElementById('procedure-status').value;
        const cost = document.getElementById('procedure-cost').value;
        const notes = document.getElementById('procedure-notes').value;

        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.add_tooth_procedure',
                args: {
                    patient_id: this.patientId,
                    tooth_number: this.getSelectedTooth(),
                    procedure_type: procedureType,
                    status: status,
                    cost: cost,
                    notes: notes
                }
            });

            if (response.message) {
                this.showSuccess('Procedure added successfully');
                document.getElementById('procedure-modal').remove();
                this.updateChartDisplay();
            }
        } catch (error) {
            console.error('Error adding procedure:', error);
            this.showError('Failed to add procedure');
        }
    }

    async submitNote() {
        const noteContent = document.getElementById('note-content').value;

        try {
            const response = await frappe.call({
                method: 'dentcharts.patient_dashboard.add_tooth_note',
                args: {
                    patient_id: this.patientId,
                    tooth_number: this.getSelectedTooth(),
                    note: noteContent
                }
            });

            if (response.message) {
                this.showSuccess('Note added successfully');
                document.getElementById('note-modal').remove();
                this.updateChartDisplay();
            }
        } catch (error) {
            console.error('Error adding note:', error);
            this.showError('Failed to add note');
        }
    }

    getSelectedTooth() {
        const selectedTooth = document.querySelector('.tooth.selected');
        return selectedTooth ? selectedTooth.dataset.toothNumber : null;
    }

    updateChartDisplay(data = null) {
        // Update chart display with new data
        if (data) {
            this.renderChartData(data);
        } else {
            // Refresh chart data
            this.loadChart(this.patientId);
        }
    }

    renderChartData(data) {
        // Render chart data updates
        if (data.teeth_data) {
            Object.entries(data.teeth_data).forEach(([toothNumber, toothData]) => {
                const toothElement = document.querySelector(`[data-tooth-number="${toothNumber}"]`);
                if (toothElement) {
                    this.updateToothDisplay(toothElement, toothData);
                }
            });
        }
    }

    updateToothDisplay(toothElement, toothData) {
        // Update tooth visual display based on conditions and procedures
        toothElement.dataset.conditions = JSON.stringify(toothData.conditions || []);
        toothElement.dataset.procedures = JSON.stringify(toothData.procedures || []);
        toothElement.dataset.notes = toothData.notes || '';
        
        // Apply visual indicators
        this.applyToothVisualIndicators(toothElement, toothData);
    }

    applyToothVisualIndicators(toothElement, toothData) {
        // Remove existing indicators
        toothElement.classList.remove('has-condition', 'has-procedure', 'has-note');
        
        // Add indicators based on data
        if (toothData.conditions && toothData.conditions.length > 0) {
            toothElement.classList.add('has-condition');
        }
        
        if (toothData.procedures && toothData.procedures.length > 0) {
            toothElement.classList.add('has-procedure');
        }
        
        if (toothData.notes) {
            toothElement.classList.add('has-note');
        }
    }

    showChartError(message) {
        const chartContainer = document.getElementById('dental-chart-visual');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="enhancedChartWrapper.loadChart('${this.patientId}')">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    showSuccess(message) {
        frappe.show_alert(message, 3);
    }

    showError(message) {
        frappe.show_alert(message, 5);
    }
}

// Initialize chart integration when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedChartWrapper = new EnhancedDentalChartWrapper();
});

// Export for global access
window.EnhancedDentalChartWrapper = EnhancedDentalChartWrapper; 