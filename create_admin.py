#!/usr/bin/env python
"""Script to create a superadmin user"""

import os
import sys
from app import create_app, db
from app.models.user import User, UserRole

def create_admin_user(email, password, full_name="Administrator"):
    """Create a superadmin user"""
    app = create_app()

    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f'Error: User with email {email} already exists')
            return False

        # Create new admin user
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

        print(f'✓ Admin user created successfully!')
        print(f'  Email: {email}')
        print(f'  Name: {full_name}')
        print(f'  Role: ADMIN')
        return True

if __name__ == '__main__':
    email = "hamka.suleiman@calmic.com.my"
    password = "061167@aB1"
    full_name = "Hamka Suleiman"

    success = create_admin_user(email, password, full_name)
    sys.exit(0 if success else 1)
