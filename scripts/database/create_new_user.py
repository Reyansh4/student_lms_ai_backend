#!/usr/bin/env python3
"""
Create new user script
"""

import psycopg2
from passlib.hash import bcrypt
import uuid
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'student_lms_ai',
    'user': 'postgres',
    'password': 'reyansh4',
    'port': 5432
}

def create_new_user():
    """Create a new user with working credentials"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("👤 Creating new user...")
        
        # User data
        user_id = str(uuid.uuid4())
        email = "student@example.com"
        name = "Test Student"
        password = "password123"
        password_hash = bcrypt.hash(password)
        current_time = datetime.now()
        
        print(f"User ID: {user_id}")
        print(f"Email: {email}")
        print(f"Name: {name}")
        print(f"Password: {password}")
        print(f"Hash: {password_hash[:50]}...")
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (id, email, name, password, phone, city, country, 
                             prime_member, is_active, is_available, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, email, name, password_hash, "", "", "", 
            False, True, True, current_time, current_time
        ))
        
        print("✅ User created successfully!")
        
        # Verify user was created
        cursor.execute("SELECT id, email, name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            print(f"Verified user: {user[1]} ({user[2]})")
        
        # Commit changes
        conn.commit()
        
        print("\n🎉 New user credentials:")
        print(f"Email: {email}")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_new_user()
