#!/usr/bin/env python
"""Direct script to create superadmin user using Flask app context"""

import os
import sys

# Add the app directory to the path
sys.path.insert(0, '/home/user/legalmy')

# Set minimal environment
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('FLASK_APP', 'app:create_app')
os.environ.setdefault('SECRET_KEY', 'dev-key-for-setup')

try:
    from app import create_app, db
    from app.models.user import User, UserRole
    import bcrypt

    print("Initializing Flask app...")
    app = create_app('development')

    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        email = "hamka.suleiman@calmic.com.my"
        password = "061167@aB1"
        full_name = "Hamka Suleiman"

        # Check if user exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"User {email} already exists. Updating...")
            existing.role = UserRole.ADMIN
            existing.is_active = True
            existing.is_verified = True
            existing.set_password(password)
            db.session.commit()
            print(f"✓ Updated existing user to admin")
        else:
            print(f"Creating new admin user: {email}")
            user = User(
                email=email,
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"✓ Admin user created successfully!")

        print(f"  Email: {email}")
        print(f"  Name: {full_name}")
        print(f"  Role: ADMIN")
        print(f"  Status: Active & Verified")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
