#!/usr/bin/env python3
"""
Database seeding script with faker data for all models
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from faker import Faker
from app.db.session import SessionLocal
from app.models import *
from app.core.security import get_password_hash

# Initialize faker
fake = Faker()

def create_sample_data():
    """Create sample data for all models"""
    db = SessionLocal()
    
    try:
        print("🌱 Starting database seeding...")
        
        # 1. Create Users
        print("👥 Creating users...")
        users = []
        for i in range(10):
            user = User(
                id=uuid.uuid4(),
                name=fake.name(),
                email=fake.email(),
                password=get_password_hash("password123"),
                phone=fake.phone_number(),
                city=fake.city(),
                country=fake.country(),
                prime_member=fake.boolean(chance_of_getting_true=30),
                is_active=True,
                is_available=True,
                created_at=fake.date_time_this_year(),
                updated_at=datetime.now()
            )
            users.append(user)
            db.add(user)
        
        db.commit()
        print(f"✅ Created {len(users)} users")
        
        # 2. Create Roles
        print("🔐 Creating roles...")
        roles = []
        role_names = ["Student", "Teacher", "Admin", "Moderator"]
        for name in role_names:
            role = Role(
                id=uuid.uuid4(),
                name=name,
                description=fake.text(max_nb_chars=100),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            roles.append(role)
            db.add(role)
        
        db.commit()
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
            permission = Permission(
                id=uuid.uuid4(),
                name=name,
                description=fake.text(max_nb_chars=100),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            permissions.append(permission)
            db.add(permission)
        
        db.commit()
        print(f"✅ Created {len(permissions)} permissions")
        
        # 4. Create Role-Permission relationships
        print("🔗 Creating role-permission relationships...")
        for role in roles:
            if role.name == "Admin":
                # Admin gets all permissions
                for permission in permissions:
                    role_perm = RolePermission(
                        id=uuid.uuid4(),
                        role_id=role.id,
                        permission_id=permission.id,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(role_perm)
            elif role.name == "Teacher":
                # Teacher gets activity and grading permissions
                teacher_perms = [p for p in permissions if "activity" in p.name or "grade" in p.name]
                for permission in teacher_perms:
                    role_perm = RolePermission(
                        id=uuid.uuid4(),
                        role_id=role.id,
                        permission_id=permission.id,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(role_perm)
            else:
                # Student gets basic read permissions
                student_perms = [p for p in permissions if "read" in p.name]
                for permission in student_perms[:5]:  # Limit to 5 permissions
                    role_perm = RolePermission(
                        id=uuid.uuid4(),
                        role_id=role.id,
                        permission_id=permission.id,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(role_perm)
        
        db.commit()
        print("✅ Created role-permission relationships")
        
        # 5. Assign roles to users
        print("👤 Assigning roles to users...")
        for i, user in enumerate(users):
            if i == 0:
                # First user is admin
                role = next(r for r in roles if r.name == "Admin")
            elif i < 3:
                # Next 2 users are teachers
                role = next(r for r in roles if r.name == "Teacher")
            else:
                # Rest are students
                role = next(r for r in roles if r.name == "Student")
            
            user_role = UserRole(
                id=uuid.uuid4(),
                user_id=user.id,
                role_id=role.id,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user_role)
        
        db.commit()
        print("✅ Assigned roles to users")
        
        # 6. Create Activity Categories
        print("📚 Creating activity categories...")
        categories = []
        category_names = ["Mathematics", "Science", "Language Arts", "History", "Computer Science"]
        for name in category_names:
            category = ActivityCategory(
                id=uuid.uuid4(),
                name=name,
                description=fake.text(max_nb_chars=200),
                created_at=datetime.utcnow()
            )
            categories.append(category)
            db.add(category)
        
        db.commit()
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
        
        for category in categories:
            for sub_name in sub_category_data[category.name]:
                sub_category = ActivitySubCategory(
                    id=uuid.uuid4(),
                    category_id=category.id,
                    name=sub_name,
                    description=fake.text(max_nb_chars=200),
                    created_at=datetime.utcnow()
                )
                sub_categories.append(sub_category)
                db.add(sub_category)
        
        db.commit()
        print(f"✅ Created {len(sub_categories)} activity sub-categories")
        
        # 8. Create Activity Templates
        print("📋 Creating activity templates...")
        templates = []
        for i in range(15):
            category = fake.random_element(categories)
            sub_categories_for_category = [sc for sc in sub_categories if sc.category_id == category.id]
            if sub_categories_for_category:
                sub_category = fake.random_element(sub_categories_for_category)
                
                template = ActivityTemplate(
                    id=uuid.uuid4(),
                    name=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=300),
                    category_id=category.id,
                    sub_category_id=sub_category.id,
                    difficulty_level=fake.random_element(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
                    access_type=fake.random_element(["PRIVATE", "GLOBAL"]),
                    final_description=fake.text(max_nb_chars=500)
                )
                templates.append(template)
                db.add(template)
        
        db.commit()
        print(f"✅ Created {len(templates)} activity templates")
        
        # 9. Create Activities
        print("🎯 Creating activities...")
        activities = []
        for i in range(25):
            category = fake.random_element(categories)
            sub_categories_for_category = [sc for sc in sub_categories if sc.category_id == category.id]
            if sub_categories_for_category:
                sub_category = fake.random_element(sub_categories_for_category)
                creator = fake.random_element(users)
                
                activity = Activity(
                    id=uuid.uuid4(),
                    name=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=400),
                    category_id=category.id,
                    sub_category_id=sub_category.id,
                    difficulty_level=fake.random_element(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
                    access_type=fake.random_element(["PRIVATE", "GLOBAL"]),
                    created_by=creator.id,
                    ai_guide=fake.boolean(chance_of_getting_true=70),
                    is_active=True,
                    created_at=fake.date_time_this_year(),
                    updated_at=datetime.utcnow(),
                    final_description=fake.text(max_nb_chars=600),
                    clarification_questions={"questions": [fake.text(max_nb_chars=100) for _ in range(3)]}
                )
                activities.append(activity)
                db.add(activity)
        
        db.commit()
        print(f"✅ Created {len(activities)} activities")
        
        # 10. Create Activity Questions
        print("❓ Creating activity questions...")
        questions = []
        for activity in activities:
            for i in range(fake.random_int(1, 5)):
                question = ActivityQuestion(
                    id=uuid.uuid4(),
                    activity_id=activity.id,
                    question_text=fake.text(max_nb_chars=200),
                    solution_steps=fake.text(max_nb_chars=300),
                    answer=fake.text(max_nb_chars=100),
                    ai_hint=fake.text(max_nb_chars=150),
                    created_at=datetime.utcnow()
                )
                questions.append(question)
                db.add(question)
        
        db.commit()
        print(f"✅ Created {len(questions)} activity questions")
        
        # 11. Create Activity Documents
        print("📄 Creating activity documents...")
        documents = []
        for activity in activities:
            for i in range(fake.random_int(0, 3)):
                document = ActivityDocument(
                    id=uuid.uuid4(),
                    activity_id=activity.id,
                    file_name=f"{fake.word()}_{fake.word()}.{fake.random_element(['pdf', 'docx', 'txt'])}",
                    file_type=fake.random_element(["PDF", "TEXT", "TEXTBOX", "IMAGE"]),
                    description=fake.text(max_nb_chars=150),
                    file_metadata={"size": fake.random_int(1000, 10000000), "format": "document"},
                    created_at=datetime.utcnow()
                )
                documents.append(document)
                db.add(document)
        
        db.commit()
        print(f"✅ Created {len(documents)} activity documents")
        
        # 12. Create Activity Sessions
        print("📝 Creating activity sessions...")
        sessions = []
        for activity in activities:
            for i in range(fake.random_int(1, 3)):
                user = fake.random_element(users)
                session = ActivitySession(
                    id=uuid.uuid4(),
                    activity_id=activity.id,
                    user_id=user.id,
                    status=fake.random_element(["IN_PROGRESS", "COMPLETED", "GRADED"]),
                    started_at=fake.date_time_this_year(),
                    completed_at=fake.date_time_this_year() if fake.boolean(chance_of_getting_true=60) else None,
                    graded_at=fake.date_time_this_year() if fake.boolean(chance_of_getting_true=40) else None,
                    graded_by=fake.random_element(users).id if fake.boolean(chance_of_getting_true=40) else None,
                    feedback=fake.text(max_nb_chars=200) if fake.boolean(chance_of_getting_true=50) else None
                )
                sessions.append(session)
                db.add(session)
        
        db.commit()
        print(f"✅ Created {len(sessions)} activity sessions")
        
        # 13. Create Conversations
        print("💬 Creating conversations...")
        conversations = []
        for i in range(20):
            user = fake.random_element(users)
            activity = fake.random_element(activities) if fake.boolean(chance_of_getting_true=70) else None
            
            conversation = Conversation(
                id=uuid.uuid4(),
                session_id=f"session_{fake.uuid4().hex[:8]}",
                user_id=user.id,
                title=fake.catch_phrase(),
                conversation_type=fake.random_element(["activity_help", "general", "feedback"]),
                activity_id=activity.id if activity else None,
                status=fake.random_element(["active", "closed", "archived"]),
                created_at=fake.date_time_this_year(),
                updated_at=datetime.utcnow()
            )
            conversations.append(conversation)
            db.add(conversation)
        
        db.commit()
        print(f"✅ Created {len(conversations)} conversations")
        
        # 14. Create Chat Messages
        print("💭 Creating chat messages...")
        messages = []
        for conversation in conversations:
            for i in range(fake.random_int(2, 8)):
                message = ChatMessage(
                    id=uuid.uuid4(),
                    conversation_id=conversation.id,
                    session_id=conversation.session_id,
                    activity_id=conversation.activity_id,
                    user_id=conversation.user_id,
                    role=fake.random_element(["user", "assistant", "system"]),
                    content=fake.text(max_nb_chars=200),
                    intent=fake.random_element(["question", "answer", "clarification", "feedback"]),
                    topic=fake.word(),
                    message_metadata={"timestamp": datetime.utcnow().isoformat()},
                    created_at=fake.date_time_this_year()
                )
                messages.append(message)
                db.add(message)
        
        db.commit()
        print(f"✅ Created {len(messages)} chat messages")
        
        # 15. Create Activity Chats
        print("🎯 Creating activity chats...")
        activity_chats = []
        for activity in activities:
            if fake.boolean(chance_of_getting_true=60):
                conversation = fake.random_element(conversations)
                chat = ActivityChat(
                    id=uuid.uuid4(),
                    conversation_id=conversation.id,
                    activity_id=activity.id,
                    chat_type=fake.random_element(["help", "discussion", "feedback"]),
                    status=fake.random_element(["active", "closed"]),
                    created_at=datetime.utcnow()
                )
                activity_chats.append(chat)
                db.add(chat)
        
        db.commit()
        print(f"✅ Created {len(activity_chats)} activity chats")
        
        # 16. Create AI Responses
        print("🤖 Creating AI responses...")
        ai_responses = []
        for user in users:
            for i in range(fake.random_int(0, 3)):
                ai_response = AIResponse(
                    id=uuid.uuid4(),
                    student_id=user.id,
                    question=fake.text(max_nb_chars=150),
                    response={"answer": fake.text(max_nb_chars=300), "confidence": fake.random_float(0.7, 1.0)},
                    status=fake.random_element(["Pending", "Approved"]),
                    created_at=fake.date_time_this_year()
                )
                ai_responses.append(ai_response)
                db.add(ai_response)
        
        db.commit()
        print(f"✅ Created {len(ai_responses)} AI responses")
        
        # 17. Create Activity AI Responses
        print("🎯 Creating activity AI responses...")
        activity_ai_responses = []
        for session in sessions:
            if fake.boolean(chance_of_getting_true=70):
                question = fake.random_element(questions)
                ai_response = ActivityAIResponse(
                    id=uuid.uuid4(),
                    session_id=session.id,
                    user_id=session.user_id,
                    question_id=question.id,
                    ai_response=fake.text(max_nb_chars=400),
                    created_at=datetime.utcnow()
                )
                activity_ai_responses.append(ai_response)
                db.add(ai_response)
        
        db.commit()
        print(f"✅ Created {len(activity_ai_responses)} activity AI responses")
        
        print("\n🎉 Database seeding completed successfully!")
        print(f"📊 Summary of created data:")
        print(f"   👥 Users: {len(users)}")
        print(f"   🔐 Roles: {len(roles)}")
        print(f"   🔑 Permissions: {len(permissions)}")
        print(f"   📚 Categories: {len(categories)}")
        print(f"   📖 Sub-categories: {len(sub_categories)}")
        print(f"   📋 Templates: {len(templates)}")
        print(f"   🎯 Activities: {len(activities)}")
        print(f"   ❓ Questions: {len(questions)}")
        print(f"   📄 Documents: {len(documents)}")
        print(f"   📝 Sessions: {len(sessions)}")
        print(f"   💬 Conversations: {len(conversations)}")
        print(f"   💭 Messages: {len(messages)}")
        print(f"   🎯 Activity Chats: {len(activity_chats)}")
        print(f"   🤖 AI Responses: {len(ai_responses)}")
        print(f"   🎯 Activity AI Responses: {len(activity_ai_responses)}")
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
