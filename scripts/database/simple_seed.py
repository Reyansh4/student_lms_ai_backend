#!/usr/bin/env python3
"""
Simple database seeding script without complex imports
"""

import psycopg2
import uuid
from datetime import datetime
import random

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'student_lms_ai',
    'user': 'postgres',
    'password': 'reyansh4',
    'port': 5432
}

def create_sample_data():
    """Create sample data for all models"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🌱 Starting database seeding...")
        
        # 1. Create Users
        print("👥 Creating users...")
        users = []
        user_names = [
            "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis", "David Wilson",
            "Lisa Anderson", "Robert Taylor", "Jennifer Martinez", "William Garcia", "Maria Rodriguez"
        ]
        
        for i, name in enumerate(user_names):
            user_id = str(uuid.uuid4())
            email = f"user{i+1}@example.com"
            password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QJ8QJ8"  # password123
            
            cursor.execute("""
                INSERT INTO users (id, name, email, password, phone, city, country, 
                                prime_member, is_active, is_available, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id, name, email, password_hash, 
                f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                random.choice(["USA", "Canada", "UK", "Australia", "Germany"]),
                random.choice([True, False]), True, True,
                datetime.utcnow(), datetime.utcnow()
            ))
            users.append(user_id)
        
        print(f"✅ Created {len(users)} users")
        
        # 2. Create Roles
        print("🔐 Creating roles...")
        roles = []
        role_names = ["Student", "Teacher", "Admin", "Moderator"]
        
        for name in role_names:
            role_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO roles (id, name, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                role_id, name, f"Role for {name.lower()}s", True,
                datetime.utcnow(), datetime.utcnow()
            ))
            roles.append(role_id)
        
        print(f"✅ Created {len(roles)} roles")
        
        # 3. Create Permissions
        print("🔑 Creating permissions...")
        permissions = []
        permission_names = [
            "read_activities", "create_activities", "update_activities", "delete_activities",
            "read_users", "create_users", "update_users", "delete_users",
            "read_roles", "create_roles", "update_roles", "delete_roles",
            "grade_activities", "manage_system"
        ]
        
        for name in permission_names:
            permission_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO permissions (id, name, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                permission_id, name, f"Permission to {name.replace('_', ' ')}", True,
                datetime.utcnow(), datetime.utcnow()
            ))
            permissions.append(permission_id)
        
        print(f"✅ Created {len(permissions)} permissions")
        
        # 4. Create Role-Permission relationships
        print("🔗 Creating role-permission relationships...")
        for i, role_id in enumerate(roles):
            if i == 0:  # Admin gets all permissions
                for permission_id in permissions:
                    cursor.execute("""
                        INSERT INTO role_permissions (id, role_id, permission_id, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), role_id, permission_id, True,
                        datetime.utcnow(), datetime.utcnow()
                    ))
            elif i == 1:  # Teacher gets activity and grading permissions
                teacher_perms = [p for p in permissions if "activity" in p or "grade" in p]
                for permission_id in teacher_perms:
                    cursor.execute("""
                        INSERT INTO role_permissions (id, role_id, permission_id, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), role_id, permission_id, True,
                        datetime.utcnow(), datetime.utcnow()
                    ))
            else:  # Student gets basic read permissions
                student_perms = [p for p in permissions if "read" in p][:5]
                for permission_id in student_perms:
                    cursor.execute("""
                        INSERT INTO role_permissions (id, role_id, permission_id, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), role_id, permission_id, True,
                        datetime.utcnow(), datetime.utcnow()
                    ))
        
        print("✅ Created role-permission relationships")
        
        # 5. Assign roles to users
        print("👤 Assigning roles to users...")
        for i, user_id in enumerate(users):
            if i == 0:
                role_id = roles[2]  # Admin
            elif i < 3:
                role_id = roles[1]  # Teacher
            else:
                role_id = roles[0]  # Student
            
            cursor.execute("""
                INSERT INTO user_roles (id, user_id, role_id, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), user_id, role_id, True,
                datetime.now(), datetime.now()
            ))
        
        print("✅ Assigned roles to users")
        
        # 6. Create Activity Categories
        print("📚 Creating activity categories...")
        categories = []
        category_names = ["Mathematics", "Science", "Language Arts", "History", "Computer Science"]
        
        for name in category_names:
            category_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO activity_categories (id, name, description, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                category_id, name, f"Category for {name.lower()} activities", datetime.utcnow()
            ))
            categories.append(category_id)
        
        print(f"✅ Created {len(categories)} activity categories")
        
        # 7. Create Activity Sub-Categories
        print("📖 Creating activity sub-categories...")
        sub_categories = []
        sub_category_data = {
            "Mathematics": ["Algebra", "Geometry", "Calculus", "Statistics"],
            "Science": ["Physics", "Chemistry", "Biology", "Astronomy"],
            "Language Arts": ["Grammar", "Literature", "Writing", "Vocabulary"],
            "History": ["Ancient History", "Modern History", "World History", "American History"],
            "Computer Science": ["Programming", "Data Structures", "Algorithms", "Web Development"]
        }
        
        for i, category_id in enumerate(categories):
            category_name = category_names[i]
            for sub_name in sub_category_data[category_name]:
                sub_category_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO activity_sub_categories (id, category_id, name, description, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    sub_category_id, category_id, sub_name, f"Sub-category for {sub_name.lower()}", datetime.utcnow()
                ))
                sub_categories.append(sub_category_id)
        
        print(f"✅ Created {len(sub_categories)} activity sub-categories")
        
        # 8. Create Activities
        print("🎯 Creating activities...")
        activities = []
        activity_names = [
            "Introduction to Algebra", "Basic Physics Concepts", "English Grammar Fundamentals",
            "World War II History", "Python Programming Basics", "Advanced Calculus",
            "Organic Chemistry", "Creative Writing Workshop", "Ancient Civilizations",
            "Data Structures and Algorithms", "Statistics for Beginners", "Chemistry Lab Safety",
            "Literature Analysis", "Modern World History", "Web Development Fundamentals",
            "Linear Algebra", "Quantum Physics", "Public Speaking", "American Revolution",
            "Machine Learning Basics", "Differential Equations", "Biochemistry",
            "Poetry Writing", "Cold War History", "Software Engineering"
        ]
        
        for i, name in enumerate(activity_names):
            activity_id = str(uuid.uuid4())
            category_id = random.choice(categories)
            # Find sub-categories for this category
            category_index = categories.index(category_id)
            category_name = category_names[category_index]
            available_sub_categories = [sc for sc in sub_categories if sc in [sc for sc in sub_categories if sc in sub_categories]]
            
            if available_sub_categories:
                sub_category_id = random.choice(available_sub_categories)
            else:
                sub_category_id = random.choice(sub_categories)
            
            creator_id = random.choice(users)
            
            cursor.execute("""
                INSERT INTO activity (id, name, description, category_id, sub_category_id,
                                   difficulty_level, access_type, created_by, ai_guide, is_active,
                                   created_at, updated_at, final_description, clarification_questions)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                activity_id, name, f"Description for {name}", category_id, sub_category_id,
                random.choice(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
                random.choice(["PRIVATE", "GLOBAL"]), creator_id,
                random.choice([True, False]), True,
                datetime.utcnow(), datetime.utcnow(),
                f"Final description for {name}",
                '{"questions": ["Question 1", "Question 2", "Question 3"]}'
            ))
            activities.append(activity_id)
        
        print(f"✅ Created {len(activities)} activities")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Database seeding completed successfully!")
        print(f"📊 Summary of created data:")
        print(f"   👥 Users: {len(users)}")
        print(f"   🔐 Roles: {len(roles)}")
        print(f"   🔑 Permissions: {len(permissions)}")
        print(f"   📚 Categories: {len(categories)}")
        print(f"   📖 Sub-categories: {len(sub_categories)}")
        print(f"   🎯 Activities: {len(activities)}")
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_sample_data()
