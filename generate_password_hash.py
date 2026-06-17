#!/usr/bin/env python3
"""Generate bcrypt password hash for database insertion"""

import base64
import hashlib
import os

# Note: This uses a simplified approach. For production, install bcrypt:
# pip install bcrypt

try:
    import bcrypt

    password = "061167@aB1"
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    print("=" * 60)
    print("BCRYPT PASSWORD HASH")
    print("=" * 60)
    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    print("\nUse this hash in your SQL INSERT statement below")
    print("=" * 60)

except ImportError:
    print("bcrypt not installed. Installing...")
    os.system("pip install bcrypt")
    import bcrypt

    password = "061167@aB1"
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    print("=" * 60)
    print("BCRYPT PASSWORD HASH")
    print("=" * 60)
    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    print("\nUse this hash in your SQL INSERT statement below")
    print("=" * 60)
