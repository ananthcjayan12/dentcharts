import frappe
from frappe import _
from frappe.utils import nowdate, getdate, formatdate, format_datetime
from datetime import datetime, timedelta

def format_currency(amount):
    """Format currency amount"""
    try:
        if amount is None:
            return "$0.00"
        return f"${float(amount):.2f}"
    except Exception:
        return "$0.00"

def format_date(date_obj):
    """Format date for display"""
    try:
        if not date_obj:
            return ""
        if isinstance(date_obj, str):
            date_obj = getdate(date_obj)
        return formatdate(date_obj)
    except Exception:
        return ""

def format_datetime_for_display(datetime_obj):
    """Format datetime for display"""
    try:
        if not datetime_obj:
            return ""
        return format_datetime(datetime_obj)
    except Exception:
        return ""

def calculate_age_from_dob(date_of_birth):
    """Calculate age from date of birth"""
    try:
        if not date_of_birth:
            return None
        
        today = getdate()
        dob = getdate(date_of_birth)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return None

def get_patient_display_name(patient_id):
    """Get patient display name"""
    try:
        patient = frappe.get_doc("Dental Patient", patient_id)
        return patient.patient_name
    except Exception:
        return "Unknown Patient"

def get_doctor_display_name(doctor_id):
    """Get doctor display name"""
    try:
        if not doctor_id:
            return "Unknown Doctor"
        doctor = frappe.get_doc("Healthcare Practitioner", doctor_id)
        return doctor.name
    except Exception:
        return "Unknown Doctor"

def validate_patient_id(patient_id):
    """Validate patient ID exists"""
    try:
        if not patient_id:
            return False
        return frappe.db.exists("Dental Patient", patient_id)
    except Exception:
        return False

def get_patient_status(patient_id):
    """Get patient status"""
    try:
        patient = frappe.get_doc("Dental Patient", patient_id)
        if patient.docstatus == 2:
            return "Cancelled"
        elif patient.docstatus == 1:
            return "Active"
        else:
            return "Draft"
    except Exception:
        return "Unknown"

def get_appointment_status_color(status):
    """Get color for appointment status"""
    status_colors = {
        'Scheduled': 'blue',
        'Confirmed': 'green',
        'Completed': 'green',
        'Cancelled': 'red',
        'No Show': 'orange',
        'In Progress': 'yellow'
    }
    return status_colors.get(status, 'gray')

def get_condition_severity_color(severity):
    """Get color for condition severity"""
    severity_colors = {
        'Mild': 'green',
        'Moderate': 'yellow',
        'Severe': 'red',
        'Critical': 'red'
    }
    return severity_colors.get(severity, 'gray')

def get_procedure_status_color(status):
    """Get color for procedure status"""
    status_colors = {
        'Planned': 'blue',
        'In Progress': 'yellow',
        'Completed': 'green',
        'Cancelled': 'red'
    }
    return status_colors.get(status, 'gray')

def format_tooth_number(tooth_number):
    """Format tooth number for display"""
    try:
        if not tooth_number:
            return ""
        return f"Tooth {tooth_number}"
    except Exception:
        return ""

def get_dentition_description(dentition_type):
    """Get description for dentition type"""
    descriptions = {
        'Permanent': 'Adult teeth',
        'Primary': 'Baby teeth',
        'Mixed': 'Mixed dentition'
    }
    return descriptions.get(dentition_type, dentition_type)

def format_payment_method(method):
    """Format payment method for display"""
    try:
        if not method:
            return "Unknown"
        return method.replace('_', ' ').title()
    except Exception:
        return "Unknown"

def get_recent_dates(days=7):
    """Get list of recent dates"""
    try:
        dates = []
        today = getdate()
        for i in range(days):
            date = today - timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
        return dates
    except Exception:
        return []

def is_today(date_obj):
    """Check if date is today"""
    try:
        if not date_obj:
            return False
        today = getdate()
        check_date = getdate(date_obj)
        return today == check_date
    except Exception:
        return False

def is_future_date(date_obj):
    """Check if date is in the future"""
    try:
        if not date_obj:
            return False
        today = getdate()
        check_date = getdate(date_obj)
        return check_date > today
    except Exception:
        return False

def is_past_date(date_obj):
    """Check if date is in the past"""
    try:
        if not date_obj:
            return False
        today = getdate()
        check_date = getdate(date_obj)
        return check_date < today
    except Exception:
        return False

def get_date_difference(date1, date2):
    """Get difference between two dates in days"""
    try:
        if not date1 or not date2:
            return 0
        d1 = getdate(date1)
        d2 = getdate(date2)
        return abs((d2 - d1).days)
    except Exception:
        return 0

def format_duration(days):
    """Format duration for display"""
    try:
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except Exception:
        return "Unknown"

def sanitize_text(text):
    """Sanitize text for safe display"""
    try:
        if not text:
            return ""
        # Basic HTML escaping
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        return text.strip()
    except Exception:
        return ""

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    try:
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    except Exception:
        return ""

def format_phone_number(phone):
    """Format phone number for display"""
    try:
        if not phone:
            return ""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone
    except Exception:
        return phone

def validate_email(email):
    """Basic email validation"""
    try:
        if not email:
            return False
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    except Exception:
        return False

def get_file_extension(filename):
    """Get file extension from filename"""
    try:
        if not filename:
            return ""
        return filename.split('.')[-1].lower()
    except Exception:
        return ""

def is_image_file(filename):
    """Check if file is an image"""
    try:
        if not filename:
            return False
        ext = get_file_extension(filename)
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return ext in image_extensions
    except Exception:
        return False

def format_file_size(size_bytes):
    """Format file size for display"""
    try:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except Exception:
        return "Unknown"

def get_current_user_info():
    """Get current user information"""
    try:
        user = frappe.get_doc("User", frappe.session.user)
        return {
            "name": user.name,
            "full_name": user.full_name,
            "email": user.email,
            "image": user.user_image
        }
    except Exception:
        return {}

def log_activity(patient_id, activity_type, description, user=None):
    """Log activity for patient"""
    try:
        if not user:
            user = frappe.session.user
        
        activity = frappe.get_doc({
            "doctype": "Dental Chart Activity",
            "patient": patient_id,
            "activity_type": activity_type,
            "description": description,
            "owner": user
        })
        activity.insert(ignore_permissions=True)
        return True
    except Exception as e:
        frappe.log_error(f"Error logging activity: {str(e)}")
        return False

def get_cache_key(prefix, *args):
    """Generate cache key"""
    try:
        key_parts = [prefix] + [str(arg) for arg in args]
        return "_".join(key_parts)
    except Exception:
        return prefix

def clear_patient_cache(patient_id):
    """Clear cache for patient data"""
    try:
        # This is a simple cache clearing - in production you might use Redis
        cache_keys = [
            f"patient_data_{patient_id}",
            f"patient_summary_{patient_id}",
            f"patient_payments_{patient_id}",
            f"patient_appointments_{patient_id}"
        ]
        # In a real implementation, you would clear these from your cache
        return True
    except Exception:
        return False 