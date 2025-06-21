# Dental Clinic ERP - Quick Start Guide

## 🚀 Ready to Start? Follow These Steps!

### Prerequisites Check
- [x] Frappe Framework installed
- [x] `dentcharts` app created
- [x] Healthcare module installed  
- [x] Site created and app installed

### 📋 Today's Tasks (Phase 1 Start)

## Step 1: Enable Developer Mode (5 minutes)

```bash
# Navigate to your bench directory
cd /path/to/your/frappe-bench

# Enable developer mode
bench set-config -g developer_mode true

# Restart bench
bench restart
```

**Verify:** Go to Desk → Settings → System Settings, you should see "Developer Mode" enabled.

## Step 2: Explore Healthcare Module (15 minutes)

Let's see what we can leverage from the existing Healthcare module:

```bash
# Check installed apps
bench --site [your-site] list-apps

# Browse Healthcare DocTypes
```

**In Desk:**
1. Go to DocType List
2. Filter by module "Healthcare"
3. Note key DocTypes:
   - Patient
   - Healthcare Practitioner  
   - Appointment
   - Patient Medical Record

## Step 3: Create Additional Modules (10 minutes)

**In Desk:**
1. Go to **Module Def** (search in awesome bar)
2. Create these new modules:

### Module 1: Patient Management
- **Module Name:** Patient Management
- **App Name:** dentcharts

### Module 2: Dental Charting  
- **Module Name:** Dental Charting
- **App Name:** dentcharts

### Module 3: Appointment Scheduling
- **Module Name:** Appointment Scheduling  
- **App Name:** dentcharts

### Module 4: Payment Management
- **Module Name:** Payment Management
- **App Name:** dentcharts

### Module 5: Reports & Analytics
- **Module Name:** Reports & Analytics
- **App Name:** dentcharts

## Step 4: Update modules.txt (5 minutes)

Edit the file: `dentcharts/modules.txt`

**Before:**
```
Dentcharts
```

**After:**
```
Dentcharts
Patient Management
Dental Charting  
Appointment Scheduling
Payment Management
Reports & Analytics
```

## Step 5: Commit Your Changes (5 minutes)

```bash
cd apps/dentcharts

# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Phase 1: Add modules and enable developer mode"
```

## 🎯 What's Next? (Phase 1 Completion)

### Tomorrow's Tasks:
1. **Explore Healthcare DocTypes deeper**
   - Study Patient DocType structure
   - Understand Healthcare Practitioner fields
   - Review Appointment DocType

2. **Plan DocType Integration**
   - Map Healthcare fields to dental needs
   - Identify extension points
   - Plan new fields needed

3. **Start Documentation**
   - Document current Healthcare module structure
   - Plan dental-specific requirements
   - Create field mapping document

## 📚 Quick Reference Commands

### Useful Bench Commands
```bash
# Start bench
bench start

# Install app on site  
bench --site [site-name] install-app dentcharts

# Console access
bench --site [site-name] console

# Clear cache
bench --site [site-name] clear-cache

# Database console
bench --site [site-name] mariadb
```

### Useful Desk Navigation
- **DocType List:** Search "DocType" in awesome bar
- **Module List:** Search "Module" in awesome bar  
- **User List:** Search "User" in awesome bar
- **Settings:** Click settings gear icon

## 🔍 Healthcare Module Exploration Checklist

### Key DocTypes to Study:
- [ ] **Patient** - Base patient information
- [ ] **Healthcare Practitioner** - Doctor/dentist profiles
- [ ] **Appointment** - Appointment scheduling
- [ ] **Patient Medical Record** - Medical history
- [ ] **Healthcare Service Unit** - Rooms/equipment
- [ ] **Medical Code Standard** - Coding systems

### Questions to Answer:
- [ ] What fields does Patient DocType have?
- [ ] How are appointments scheduled?
- [ ] What's the practitioner workflow?
- [ ] How are medical records structured?
- [ ] What permissions exist?

## 🎯 Success Criteria for Phase 1

**You'll know Phase 1 is complete when:**
- [ ] Developer mode is enabled
- [ ] All 5 new modules are created
- [ ] modules.txt is updated
- [ ] Changes are committed to git
- [ ] Healthcare module structure is documented
- [ ] Ready to start creating DocTypes

## 🆘 Troubleshooting

### Common Issues:

**Developer mode not working?**
```bash
bench set-config -g developer_mode true
bench restart
# Clear browser cache
```

**Module creation fails?**
- Check if you're logged in as Administrator
- Verify app is installed on site
- Clear cache and try again

**Can't see changes?**
```bash
bench --site [site-name] clear-cache
# Refresh browser page
```

## 📞 Need Help?

- **Frappe Documentation:** https://docs.frappe.io/
- **Healthcare Module:** https://github.com/frappe/healthcare  
- **Community Forum:** https://discuss.frappe.io/

---

## ⏰ Time Estimate: 45 minutes total

**Phase 1 should take about 45 minutes to complete. Ready to start building your dental clinic ERP system!**

**Next:** After completing Phase 1, move to Phase 2 in the main development guide to start creating your first DocTypes.

---

**Good luck! 🚀** 