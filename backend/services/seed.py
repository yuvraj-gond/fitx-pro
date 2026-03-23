# =============================================================================
# backend/services/seed.py
# Seeds the food database table on first run
# =============================================================================

from sqlalchemy.orm import Session
from ..models.database import Food, SessionLocal

FOODS = [
    ("Chicken Breast",165,31,0,3.6,"Protein"),
    ("Eggs",155,13,1.1,11,"Protein"),
    ("Tuna (canned)",116,26,0,1,"Protein"),
    ("Salmon",208,20,0,13,"Protein"),
    ("Beef (lean)",250,26,0,17,"Protein"),
    ("Turkey Breast",135,30,0,1,"Protein"),
    ("Greek Yogurt",59,10,3.6,0.4,"Dairy"),
    ("Cottage Cheese",98,11,3.4,4.3,"Dairy"),
    ("Milk (whole)",61,3.2,4.8,3.3,"Dairy"),
    ("Whey Protein Powder",400,80,5,5,"Supplement"),
    ("Protein Bar",350,20,40,10,"Supplement"),
    ("Brown Rice",216,5,45,1.8,"Carbs"),
    ("White Rice",206,4.3,45,0.4,"Carbs"),
    ("Oats",389,17,66,7,"Carbs"),
    ("Sweet Potato",86,1.6,20,0.1,"Carbs"),
    ("Quinoa",222,8,39,4,"Carbs"),
    ("Whole Wheat Bread",247,13,41,4.2,"Carbs"),
    ("Pasta",371,13,74,1.5,"Carbs"),
    ("Banana",89,1.1,23,0.3,"Fruit"),
    ("Apple",52,0.3,14,0.2,"Fruit"),
    ("Orange",47,0.9,12,0.1,"Fruit"),
    ("Blueberries",57,0.7,14,0.3,"Fruit"),
    ("Broccoli",34,2.8,7,0.4,"Vegetable"),
    ("Spinach",23,2.9,3.6,0.4,"Vegetable"),
    ("Kale",49,4.3,9,0.9,"Vegetable"),
    ("Carrot",41,0.9,10,0.2,"Vegetable"),
    ("Avocado",160,2,9,15,"Healthy Fats"),
    ("Almonds",579,21,22,50,"Healthy Fats"),
    ("Peanut Butter",588,25,20,50,"Healthy Fats"),
    ("Olive Oil",884,0,0,100,"Healthy Fats"),
    ("Lentils",116,9,20,0.4,"Legumes"),
    ("Black Beans",132,8.9,24,0.5,"Legumes"),
    ("Chickpeas",164,8.9,27,2.6,"Legumes"),
    ("Pizza",266,11,33,10,"Fast Food"),
    ("Burger",295,17,24,14,"Fast Food"),
    ("French Fries",312,3.4,41,15,"Fast Food"),
    ("Dark Chocolate",546,5,60,31,"Snack"),
    ("Orange Juice",45,0.7,10,0.2,"Beverage"),
    ("Coffee (black)",2,0.3,0,0,"Beverage"),
]


def seed_foods(db: Session):
    if db.query(Food).count() > 0:
        return  # Already seeded
    for name, cal, prot, carb, fat, cat in FOODS:
        db.add(Food(
            name=name, calories_per_100g=cal, protein_per_100g=prot,
            carbs_per_100g=carb, fat_per_100g=fat, category=cat,
        ))
    db.commit()
    print("✅ Food database seeded.")
