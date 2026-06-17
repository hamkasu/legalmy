# Superadmin User Setup Guide

This document explains how to create a superadmin user for LegalMY.

## Quick Setup (Railway Environment)

### Option 1: Using Flask CLI (Recommended)

Once your app is deployed on Railway, connect to the app's shell and run:

```bash
flask create-admin --email "hamka.suleiman@calmic.com.my" --password "061167@aB1" --full-name "Hamka Suleiman"
```

### Option 2: Using Python Script in Railway Shell

```bash
python create_admin.py
```

## Manual Setup in Production

If you need to create the user directly in your PostgreSQL database:

### Step 1: Generate Password Hash

You'll need to generate a bcrypt hash for the password. In a Python environment with bcrypt installed:

```python
import bcrypt
password = "061167@aB1"
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hash)
```

### Step 2: Execute SQL

Connect to your PostgreSQL database and run:

```sql
INSERT INTO users (
    email,
    full_name,
    password_hash,
    role,
    is_active,
    is_verified,
    preferences,
    created_at
) VALUES (
    'hamka.suleiman@calmic.com.my',
    'Hamka Suleiman',
    '<YOUR_BCRYPT_HASH_HERE>',
    'admin',
    true,
    true,
    '{}',
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    role = 'admin',
    is_active = true,
    is_verified = true,
    password_hash = '<YOUR_BCRYPT_HASH_HERE>';
```

Replace `<YOUR_BCRYPT_HASH_HERE>` with the hash generated in Step 1.

## Verify Admin User

Once created, you can verify the admin user was created by checking:

1. Log in with:
   - Email: `hamka.suleiman@calmic.com.my`
   - Password: `061167@aB1`

2. Visit `/admin` to access the admin panel

3. Verify user role in database:
   ```sql
   SELECT id, email, full_name, role, is_active, is_verified FROM users WHERE email = 'hamka.suleiman@calmic.com.my';
   ```

## Available Files

- `app/__init__.py` - Contains the `create-admin` Flask CLI command
- `create_admin.py` - Standalone Python script (requires Flask app context)
- `setup_admin.py` - Alternative setup script (requires dependencies)
- `create_admin.sql` - SQL template (requires password hash)
