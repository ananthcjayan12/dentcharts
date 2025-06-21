# Dental Clinic ERP System - Feature Reference Guide

## Overview
This document provides a comprehensive reference for building a dental clinic management system 


#### User Flow:
1. User enters credentials on login page
2. System validates credentials against backend
3. On success, user receives access/refresh tokens
4. User can switch between clinics if associated with multiple
5. Session maintained across browser sessions
6. Automatic token refresh handling

#### Implementation Details:
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

interface Clinic {
  id: number;
  name: string;
  role?: string;
  is_primary?: boolean;
}
```

### 2. Dashboard & Analytics

#### Features:
- Real-time statistics display
- Key performance indicators (KPIs)
- Today's appointments overview
- Revenue tracking
- Patient growth metrics
- Treatment completion rates

#### Dashboard Metrics:
- **Total Patients**: Count with monthly growth percentage
- **Today's Appointments**: Daily count with comparison to yesterday
- **Monthly Revenue**: Current month revenue with percentage change
- **Treatment Completion**: Completion rate with trend analysis

#### User Flow:
1. User logs in and lands on dashboard
2. System loads clinic-specific statistics
3. Real-time data updates for appointments
4. Interactive appointment cards with quick actions
5. Navigation to detailed sections via sidebar

### 3. Patient Management System

#### Features:
- Comprehensive patient profiles
- Advanced search and filtering
- Bulk import via CSV
- Patient history tracking
- Medical history management
- Contact information management

#### Patient Data Model:
```typescript
interface Patient {
  id: string;
  name: string;
  age?: number;
  gender?: 'M' | 'F' | 'O';
  phone?: string;
  email?: string;
  address?: string;
  chief_complaint?: string;
  medical_history?: string;
  drug_allergies?: string;
  previous_dental_work?: string;
  created_at: string;
  updated_at: string;
}
```

#### User Flows:

**Adding New Patient:**
1. Click "Add New Patient" button
2. Fill patient registration form with validation
3. Submit form with error handling
4. Redirect to patient list with success message

**Patient Search & Management:**
1. Enter search terms in search bar
2. System filters patients by name, email, or phone
3. Pagination for large patient lists
4. Click patient row to view details
5. Quick actions: View profile, Schedule appointment

**CSV Import:**
1. Navigate to import page
2. Download template CSV file
3. Upload populated CSV file
4. System validates and previews data
5. Confirm import with error reporting

### 4. Appointment Scheduling System

#### Features:
- Calendar-based scheduling
- Time slot management
- Dentist assignment
- Appointment status tracking
- Conflict detection
- Patient search integration

#### Appointment Data Model:
```typescript
interface Appointment {
  id: string;
  patient: Patient;
  dentist: Dentist;
  date: string;
  start_time: string;
  end_time: string;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  reason?: string;
  notes?: string;
}
```

#### User Flows:

**Scheduling New Appointment:**
1. Click "New Appointment" button
2. Search and select patient (or create new)
3. Select dentist from available staff
4. Choose date using calendar picker
5. Select from available time slots
6. Add appointment reason and notes
7. Confirm appointment with validation

**Managing Appointments:**
1. View appointments in list or calendar view
2. Filter by date, status, or dentist
3. Search by patient name
4. Quick status updates
5. Edit or cancel existing appointments

### 5. Dental Chart System (Core Feature)

#### Features:
- Interactive tooth chart with both permanent and primary teeth
- Visual condition tracking
- Procedure history
- Multi-surface condition mapping
- Color-coded condition indicators
- Detailed tooth information panels

#### Dental Chart Data Models:
```typescript
interface Tooth {
  id: number;
  number: string;
  universal_number: number;
  dentition_type: 'permanent' | 'primary';
  name: string;
  quadrant: string;
  conditions: ToothCondition[];
  procedures: ToothProcedure[];
}

interface ToothCondition {
  id: number;
  condition_name: string;
  condition_code: string;
  surface: string;
  notes?: string;
  severity?: 'mild' | 'moderate' | 'severe';
  created_at: string;
}

interface ToothProcedure {
  id: number;
  procedure_name: string;
  procedure_code: string;
  surface: string;
  date_performed: string;
  price: number;
  status: 'planned' | 'in_progress' | 'completed';
  performed_by: string;
}
```

#### User Flows:

**Adding Conditions to Teeth:**
1. Navigate to patient's dental chart
2. Click on specific tooth
3. Tooth detail panel opens
4. Select "Add Condition"
5. Choose from predefined conditions or create custom
6. Select affected tooth surfaces
7. Add severity and notes
8. Save condition with audit trail

**Recording Dental Procedures:**
1. Select tooth from interactive chart
2. Open procedure dialog
3. Choose procedure from categorized list
4. Set procedure details (date, price, status)
5. Add procedure notes
6. Save with practitioner information

**Chart History Tracking:**
1. View comprehensive history of all chart changes
2. Filter by date range, tooth, or action type
3. Detailed audit trail with user information
4. Exportable history reports

### 6. Payment Management System

#### Features:
- Payment tracking and recording
- Outstanding balance management
- Payment history
- Revenue analytics
- Date-based filtering
- Patient-specific payment views

#### Payment Data Model:
```typescript
interface Payment {
  id: string;
  patient: Patient;
  total_amount: number;
  amount_paid: number;
  balance: number;
  payment_date: string;
  payment_method: string;
  notes?: string;
  status: 'pending' | 'partial' | 'paid' | 'overdue';
}
```

#### User Flows:

**Recording Payments:**
1. Navigate to patient profile
2. Access payment section
3. Add new payment entry
4. Record payment amount and method
5. Update outstanding balance
6. Generate payment receipt

**Payment Analytics:**
1. View payment dashboard
2. Filter by date ranges
3. Export payment reports
4. Track revenue trends

### 7. Advanced Multi-Tooth Selection System

#### Multi-Select Features:
- **Interactive Selection**: Click on multiple teeth to select them simultaneously
- **Keyboard Shortcuts**: Use Ctrl/Cmd+Click for advanced selection modes
- **Visual Feedback**: Selected teeth are highlighted with distinct styling
- **Batch Operations**: Apply conditions or procedures to multiple teeth at once
- **Progress Tracking**: Real-time progress indication during bulk operations

#### Multi-Select User Flows:

**Selecting Multiple Teeth:**
1. Navigate to patient's dental chart
2. Click on first tooth to select
3. Hold Ctrl/Cmd and click additional teeth to add to selection
4. Selected teeth show visual indicators (badges, highlighting)
5. Selection counter shows number of selected teeth
6. Clear selection button available to reset

**Adding Conditions to Multiple Teeth:**
1. Select multiple teeth using click or Ctrl+click
2. Right-click on any selected tooth or use toolbar button
3. Choose "Add Condition to Selected Teeth"
4. Multi-select condition dialog opens showing:
   - List of selected teeth with badges
   - Dropdown for predefined conditions
   - Option to create custom conditions
   - Surface selection (all, occlusal, mesial, distal, etc.)
   - Severity selection (mild, moderate, severe)
   - Date picker for detection date
   - Notes field for additional information
5. System validates input and shows preview
6. Confirm to apply condition to all selected teeth
7. Progress indicator shows completion status
8. Success/failure report for each tooth

**Adding Procedures to Multiple Teeth:**
1. Select target teeth from interactive chart
2. Access multi-select procedure dialog
3. Dialog displays:
   - Selected teeth count and numbers
   - Procedure selection from categorized list
   - Surface specification options
   - Status selection (planned, in-progress, completed)
   - Date picker for procedure date
   - Price field (with default from procedure catalog)
   - Notes field for procedure details
4. System calculates total cost across all teeth
5. Batch processing with individual tooth validation
6. Detailed success/failure reporting

#### Multi-Select Data Models:
```typescript
interface MultiSelectConditionData {
  condition_id?: number;
  custom_name?: string;
  custom_code?: string;
  custom_description?: string;
  surface: string;
  notes?: string;
  severity?: 'mild' | 'moderate' | 'severe';
  date_detected?: string;
}

interface MultiSelectProcedureData {
  procedure_id: number;
  surface: string;
  notes?: string;
  date_performed: string;
  price?: number;
  status: 'planned' | 'in_progress' | 'completed';
}

interface BatchOperationResult {
  success: Tooth[];
  failed: { tooth: Tooth; error: string }[];
}
```

### 8. Patient History Book System

#### Comprehensive History Features:
- **Timeline View**: Chronological display of all dental activities
- **Narrative Format**: Human-readable descriptions of all changes
- **Bulk Operation Grouping**: Related multi-tooth operations grouped together
- **Advanced Filtering**: Filter by date, tooth number, action type, practitioner
- **Search Functionality**: Full-text search across all history entries
- **Export Capabilities**: Generate reports in various formats

#### Patient History Book User Flows:

**Accessing Patient History:**
1. Navigate to patient's dental chart
2. Click on "History Book" tab or button
3. System loads comprehensive patient history
4. Default view shows timeline with recent entries first

**Timeline View Navigation:**
1. History organized by date in expandable cards
2. Each day shows summary statistics:
   - Number of conditions added
   - Number of procedures performed
   - Number of notes added
   - Number of updates made
3. Click to expand/collapse daily entries
4. Each entry shows:
   - Timestamp and practitioner
   - Detailed description in narrative format
   - Tooth numbers affected
   - Before/after comparisons where applicable

**Advanced Filtering:**
1. **Time Range Filters**:
   - Last week, month, 3 months, 6 months
   - Custom date range picker
   - All-time view option
2. **Category Filters**:
   - Conditions only
   - Procedures only
   - Notes and updates
   - All activities
3. **Tooth-Specific Filtering**:
   - Single tooth number
   - Multiple tooth selection
   - Quadrant-based filtering
4. **Practitioner Filter**:
   - Filter by specific dentist or hygienist
   - Show only own entries

**Bulk Operation Tracking:**
1. System detects and groups related operations
2. Multi-tooth procedures shown as single entry
3. Expandable to show individual tooth details
4. Progress tracking for incomplete bulk operations
5. Error reporting for failed operations

**Search and Export:**
1. Full-text search across all history entries
2. Search includes:
   - Condition names and codes
   - Procedure descriptions
   - Practitioner notes
   - Tooth numbers
3. Export options:
   - PDF treatment history report
   - CSV data export
   - Insurance claim documentation

#### History Data Structure:
```typescript
interface ChartHistoryEntry {
  id: number;
  date: string;
  user: string;
  action: 'add_condition' | 'add_procedure' | 'update_condition' | 'delete_condition';
  tooth_number: string;
  details: {
    condition_name?: string;
    procedure_name?: string;
    surface?: string;
    notes?: string;
    before_value?: any;
    after_value?: any;
  };
  isBulkOperation?: boolean;
  bulkTeeth?: string[];
}

interface TimelineEntry {
  date: string;
  entries: ChartHistoryEntry[];
  dayStats: {
    conditions: number;
    procedures: number;
    notes: number;
    updates: number;
  };
}
```

### 9. Comprehensive Payment Management System

#### Payment System Features:
- **Multi-Item Billing**: Support for multiple services per payment
- **Balance Tracking**: Automatic calculation of outstanding amounts
- **Payment Methods**: Multiple payment options (cash, card, insurance, etc.)
- **Partial Payments**: Support for installment payments
- **Payment History**: Complete audit trail of all transactions
- **Analytics Dashboard**: Revenue tracking and payment analytics

#### Payment Management User Flows:

**Recording New Payment:**
1. Navigate to patient profile
2. Access "Payments" section
3. Click "Add New Payment" button
4. Payment form opens with sections:
   - **Patient Information**: Auto-populated patient details
   - **Payment Items**: Add multiple billable items
     - Service description
     - Individual item costs
     - Treatment codes (if applicable)
   - **Payment Details**:
     - Total amount calculation (auto-calculated)
     - Amount actually paid (can be partial)
     - Payment method selection
     - Payment date picker
     - Notes and comments
5. System calculates remaining balance automatically
6. Submit payment with validation
7. Generate payment receipt
8. Update patient balance

**Balance Payment Flow:**
1. System identifies patients with outstanding balances
2. Balance payment shortcut available from patient list
3. Pre-populated balance payment form:
   - Shows current outstanding amount
   - Single-item payment for balance
   - Payment method selection
   - Confirmation of amount
4. Process balance payment
5. Update account status to "Paid in Full"

**Payment History Management:**
1. **Payment List View**:
   - Chronological list of all payments
   - Filter by date range, payment method, amount
   - Search by patient name or payment ID
   - Export payment reports
2. **Payment Summary Cards**:
   - Total billed amount
   - Total paid amount
   - Outstanding balance
   - Last payment date
3. **Payment Details**:
   - Individual payment breakdown
   - Item-wise billing details
   - Payment method information
   - Associated appointment details

**Payment Analytics Dashboard:**
1. **Revenue Tracking**:
   - Daily, weekly, monthly revenue charts
   - Payment method distribution
   - Average payment amounts
   - Revenue trends over time
2. **Outstanding Balances**:
   - Patients with overdue payments
   - Aging reports (30, 60, 90+ days)
   - Collection priority lists
3. **Payment Method Analysis**:
   - Cash vs. card payment ratios
   - Insurance payment tracking
   - Payment processing fees

#### Payment Data Models:
```typescript
interface Payment {
  id: string;
  patient: Patient;
  total_amount: number;
  amount_paid: number;
  balance: number;
  payment_date: string;
  payment_method: 'cash' | 'credit_card' | 'debit_card' | 'insurance' | 'bank_transfer';
  notes?: string;
  status: 'paid' | 'partial' | 'pending' | 'overdue';
  payment_items: PaymentItem[];
}

interface PaymentItem {
  description: string;
  amount: number;
  treatment_id?: string;
  procedure_code?: string;
}

interface PaymentSummary {
  total_billed: number;
  total_paid: number;
  balance_due: number;
  last_payment_date?: string;
}
```

### 10. Advanced Chart History & Audit Features

#### Comprehensive Audit System:
- **Complete Change Tracking**: Every modification recorded with timestamp
- **User Attribution**: Track which practitioner made each change
- **Before/After Comparisons**: Show exact changes made
- **Bulk Operation Grouping**: Related changes grouped for clarity
- **Regulatory Compliance**: Audit trail meets healthcare documentation requirements

#### Advanced History Features:
- **Intelligent Grouping**: Related operations automatically grouped
- **Narrative Descriptions**: Changes described in plain English
- **Visual Diff Display**: Side-by-side comparison of changes
- **Restoration Tracking**: Ability to see restoration of deleted items
- **Progress Tracking**: Monitor treatment plan completion

## User Interface Components

### 1. Responsive Layout System
- **Sidebar Navigation**: Collapsible sidebar with role-based menu items
- **Header**: User profile, clinic selector, notifications
- **Main Content**: Responsive grid layouts
- **Mobile Optimization**: Touch-friendly interfaces

### 2. Reusable UI Components
- **Forms**: Validated forms with error handling
- **Tables**: Sortable, filterable data tables
- **Modals**: Contextual dialogs for actions
- **Date Pickers**: Advanced date selection
- **Search**: Real-time search functionality

### 3. Dental-Specific Components
- **Interactive Tooth Chart**: SVG-based tooth visualization
- **Condition Indicators**: Color-coded visual markers
- **Procedure Timeline**: Chronological procedure display
- **Treatment Plans**: Visual treatment planning interface

## Data Management & API Integration

### 1. Service Layer Architecture
```typescript
// Patient Service
patientService.getPatients(clinicId, page, search, limit)
patientService.createPatient(clinicId, patientData)
patientService.updatePatient(clinicId, patientId, updateData)

// Dental Chart Service
dentalChartService.getPatientDentalChart(clinicId, patientId)
dentalChartService.addToothCondition(clinicId, patientId, toothNumber, conditionData)
dentalChartService.addToothProcedure(clinicId, patientId, toothNumber, procedureData)

// Appointment Service
appointmentService.getAppointments(clinicId, page, filters, limit)
appointmentService.createAppointment(clinicId, appointmentData)
appointmentService.getAvailableTimeSlots(clinicId, date, dentistId)
```

### 2. State Management Patterns
- **Context API**: Global state (auth, clinic selection)
- **Local State**: Component-specific state
- **Form State**: React Hook Form for complex forms
- **API State**: Loading, error, and data states

## Security & Compliance

### 1. Authentication Security
- JWT token management
- Automatic token refresh
- Secure cookie storage
- Session timeout handling

### 2. Data Privacy
- Clinic-based data isolation
- Role-based access control
- Audit logging
- HIPAA compliance considerations

### 3. Input Validation
- Client-side validation with Zod
- Server-side validation
- XSS protection
- SQL injection prevention

## Mobile Responsiveness

### 1. Responsive Design Patterns
- Mobile-first CSS approach
- Touch-friendly interfaces
- Optimized chart interactions
- Collapsible navigation

### 2. Performance Optimizations
- Code splitting
- Lazy loading
- Image optimization
- Caching strategies

## Implementation Recommendations for ERPNext

### 1. Module Structure
```
dental_management/
├── patient_management/
├── appointment_scheduling/
├── dental_charting/
├── payment_tracking/
├── reporting_analytics/
└── clinic_administration/
```

### 2. DocType Recommendations

**Patient DocType:**
- Personal information fields
- Medical history tracking
- Contact information
- Insurance details
- Treatment preferences

**Appointment DocType:**
- Patient link
- Practitioner assignment
- Date/time scheduling
- Status workflow
- Treatment notes

**Dental Chart DocType:**
- Patient relationship
- Tooth-specific data
- Condition tracking
- Procedure history
- Multi-surface mapping

**Payment DocType:**
- Patient billing
- Treatment costing
- Payment tracking
- Insurance claims
- Outstanding balances

### 3. Workflow Configurations
- Appointment status workflows
- Treatment approval processes
- Payment collection procedures
- Patient communication flows

### 4. Report Templates
- Patient treatment history
- Revenue analytics
- Appointment scheduling reports
- Outstanding payments
- Treatment completion rates

## Best Practices & Standards

### 1. Code Organization
- Feature-based directory structure
- Reusable component library
- Service layer abstraction
- Type-safe interfaces

### 2. User Experience
- Intuitive navigation patterns
- Consistent visual design
- Helpful error messages
- Loading state indicators

### 3. Performance
- Efficient data fetching
- Optimized re-renders
- Proper caching strategies
- Image optimization

### 4. Accessibility
- WCAG compliance
- Keyboard navigation
- Screen reader support
- Color contrast standards

## Deployment & Maintenance

### 1. Development Workflow
- Git-based version control
- Feature branch strategy
- Code review processes
- Automated testing

### 2. Production Considerations
- Environment configuration
- Database optimization
- Backup strategies
- Monitoring and logging

