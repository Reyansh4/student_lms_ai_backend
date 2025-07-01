#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.activity import Activity
from app.models.activity_category import ActivityCategory
from app.models.activity_sub_category import ActivitySubCategory
from sqlalchemy.orm import joinedload

def debug_database():
    db = SessionLocal()
    try:
        print("=== DATABASE DEBUG ===")
        
        # Check categories
        categories = db.query(ActivityCategory).all()
        print(f"Categories ({len(categories)}):")
        for cat in categories:
            print(f"  - {cat.name} (ID: {cat.id})")
        
        # Check subcategories
        subcategories = db.query(ActivitySubCategory).all()
        print(f"Subcategories ({len(subcategories)}):")
        for sub in subcategories:
            print(f"  - {sub.name} (ID: {sub.id})")
        
        # Check activities
        activities = db.query(Activity).options(
            joinedload(Activity.category),
            joinedload(Activity.sub_category)
        ).filter(Activity.is_active == True).all()
        
        print(f"Active Activities ({len(activities)}):")
        for act in activities:
            print(f"  - {act.name} (ID: {act.id})")
            print(f"    Category: {act.category.name if act.category else 'None'}")
            print(f"    SubCategory: {act.sub_category.name if act.sub_category else 'None'}")
            print(f"    Final Description: {act.final_description[:50]}...")
            print()
        
        if len(activities) == 0:
            print("WARNING: No active activities found in database!")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_database() 