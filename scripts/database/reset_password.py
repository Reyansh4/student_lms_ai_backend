#!/usr/bin/env python3
"""
Reset user password script
"""

import psycopg2
from passlib.hash import bcrypt

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'student_lms_ai',
    'user': 'postgres',
    'password': 'reyansh4',
    'port': 5432
}

def reset_user_password():
    """Reset user1@example.com password to 'password123'"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔐 Resetting user password...")
        
        # Generate new password hash
        new_password = "password123"
        password_hash = bcrypt.hash(new_password)
        
        print(f"New password: {new_password}")
        print(f"New hash: {password_hash[:50]}...")
        
        # Update user password
        cursor.execute("""
            UPDATE users 
            SET password = %s 
            WHERE email = 'user1@example.com'
        """, (password_hash,))
        
        # Check if user was updated
        if cursor.rowcount > 0:
            print("✅ Password updated successfully!")
            
            # Verify the user exists
            cursor.execute("SELECT id, email, name FROM users WHERE email = 'user1@example.com'")
            user = cursor.fetchone()
            if user:
                print(f"User ID: {user[0]}")
                print(f"Email: {user[1]}")
                print(f"Name: {user[2]}")
        else:
            print("❌ User not found!")
            
        # Commit changes
        conn.commit()
        
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
    reset_user_password()
