# 🗄️ Database Scripts

This directory contains utility scripts for database management and user operations.

## 📋 Available Scripts

### **User Management**
- **`create_new_user.py`** - Create new user accounts
- **`reset_password.py`** - Reset user passwords
- **`decode_jwt.py`** - Decode JWT tokens for debugging

### **Database Operations**
- **`seed_database.py`** - Populate database with initial data
- **`simple_seed.py`** - Simplified database seeding
- **`debug_db.py`** - Database debugging and inspection

## 🚀 Usage

### **Creating Users**
```bash
cd scripts/database
python create_new_user.py
```

### **Seeding Database**
```bash
cd scripts/database
python seed_database.py
# or
python simple_seed.py
```

### **Password Reset**
```bash
cd scripts/database
python reset_password.py
```

### **Debugging**
```bash
cd scripts/database
python debug_db.py
python decode_jwt.py
```

## ⚠️ Important Notes

- **Backup your database** before running seeding scripts
- **Test in development** environment first
- **Check environment variables** are properly set
- **Ensure backend is running** for database operations

## 🔧 Prerequisites

- Database connection configured
- Backend application running
- Required environment variables set
- Python dependencies installed

---

**🗄️ Use these scripts for database management and user operations!**
