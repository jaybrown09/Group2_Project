import sqlite3
import json
from datetime import datetime, date
import os
import bcrypt

#helper functions
def get_db_connection():
    conn = sqlite3.connect('data/recipes.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def convert_unit(quantity, from_unit, to_system="metric"):
    """
    Convert a unit to the target system (metric or imperial).
    Only converts if the unit belongs to the opposite system.
    """
    if from_unit is None:
        return quantity, ""

    unit = from_unit.lower().strip()
    qty = float(quantity)

    # Normalize common variations
    unit_map = {
        # Weight
        'lb': 'lbs', 'lbs': 'lbs', 'pound': 'lbs', 'pounds': 'lbs',
        'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
        'g': 'g', 'gram': 'g', 'grams': 'g',
        'kg': 'kg', 'kilo': 'kg', 'kilogram': 'kg',

        # Volume
        'cup': 'cups', 'cups': 'cups',
        'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
        'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
        'fl oz': 'fl oz', 'fluid ounce': 'fl oz', 'fluid ounces': 'fl oz',
        'pt': 'pint', 'pint': 'pint', 'pints': 'pint',
        'qt': 'quart', 'quart': 'quart', 'quarts': 'quart',
        'gal': 'gallon', 'gallon': 'gallon', 'gallons': 'gallon',
        'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml',
        'l': 'l', 'liter': 'l', 'liters': 'l',
    }

    normalized = unit_map.get(unit, unit)

    # Define which units belong to which system
    imperial_units = {'lbs', 'oz', 'cups', 'tbsp', 'tsp', 'fl oz', 'pint', 'quart', 'gallon'}
    metric_units = {'kg', 'g', 'ml', 'l'}

    # If converting to metric and unit is already metric, return as-is
    if to_system == "metric" and normalized in metric_units:
        return qty, from_unit
    
    # If converting to imperial and unit is already imperial, return as-is
    if to_system == "imperial" and normalized in imperial_units:
        return qty, from_unit

    # Define conversions
    if to_system == "metric":
        conversions = {
            # Imperial to Metric - Weight
            'lbs': (qty * 0.453592, 'kg'),
            'oz': (qty * 28.3495, 'g'),
            # Imperial to Metric - Volume
            'cups': (qty * 236.588, 'ml'),
            'tbsp': (qty * 14.7868, 'ml'),
            'tsp': (qty * 4.92892, 'ml'),
            'fl oz': (qty * 29.5735, 'ml'),
            'pint': (qty * 473.176, 'ml'),
            'quart': (qty * 946.353, 'ml'),
            'gallon': (qty * 3785.41, 'ml'),
        }
    else:  # to_system == "imperial"
        conversions = {
            # Metric to Imperial - Weight
            'kg': (qty * 2.20462, 'lbs'),
            'g': (qty * 0.035274, 'oz'),
            # Metric to Imperial - Volume
            'ml': (qty * 0.00422675, 'cups'),
            'l': (qty * 0.264172, 'gallon'),
        }

    if normalized in conversions:
        new_qty, new_unit = conversions[normalized]
        # Round sensibly
        if new_qty >= 100:
            new_qty = round(new_qty, 1)
        elif new_qty >= 10:
            new_qty = round(new_qty, 2)
        else:
            new_qty = round(new_qty, 3)
        return new_qty, new_unit

    # No conversion available (unit not recognized or not in target system)
    return qty, from_unit


# Creates SQLite Database
def init_DB():
    os.makedirs('data', exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        theme TEXT DEFAULT 'light',
        units TEXT DEFAULT 'imperial',
        landing_page TEXT DEFAULT 'dashboard'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        image_path TEXT,
        is_public BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
        """)
    
    # Ingredients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        quantity REAL,
        unit TEXT,
        name TEXT NOT NULL,
        order_index INTEGER DEFAULT 0,
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_recipes (
        user_id INTEGER,
        recipe_id INTEGER,
        PRIMARY KEY (user_id, recipe_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
);
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pantry (
        pantry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT,
        expiration_date DATE NOT NULL,
        low_threshold REAL DEFAULT 1.0,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shopping_list (
        list_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        quantity REAL,
        unit TEXT,
        is_checked BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_plan (
        plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        recipe_id INTEGER,
        meal_type TEXT NOT NULL DEFAULT 'Dinner',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
);
    """)
    
    # Add landing_page column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN landing_page TEXT DEFAULT 'dashboard'")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    conn.commit()
    
    conn.close()

# user functions
def create_user(username, password):
    if not username or not username.strip():
        return {"error": "Username cannot be empty"}
    
    if len(username) < 3:
        return {"error": "Username must be at least 3 characters"}
    
    if len(username) > 50:
        return {"error": "Username must be less than 50 characters"}

    if not password:
        return {"error": "Password cannot be empty"}
    
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters"}
    
    conn = get_db_connection()
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute("""
            INSERT INTO users(username, password)
            VALUES(?, ?)
        """, (username, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        #username already exists
        conn.close()
        return "Username Already Exists"
    finally:
        conn.close()

    return user_id

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id, username, password
    FROM users
    WHERE username = ?""",(username,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None #username not found
    
    stored_user_id = row[0]
    stored_password = row[2]

    if bcrypt.checkpw(password.encode(), stored_password.encode()):
        return stored_user_id
    else:
        return None

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, theme, units, landing_page
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    user = {
        'user_id': row[0],
        'username': row[1],
        'theme': row[2],
        'units': row[3],
        'landing_page': row[4] if row[4] else 'dashboard'
    }

    return user

def change_username(user_id, current_password, new_username):
    if not new_username or not new_username.strip():
        return {"error": "New username cannot be empty"}
    
    if len(new_username) < 3:
        return {"error": "Username must be at least 3 characters"}
    
    if len(new_username) > 50:
        return {"error": "Username must be less than 50 characters"}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First verify the current password
    cursor.execute("""
        SELECT password FROM users WHERE user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        return {"error": "User not found"}
    
    stored_password = row[0]
    
    if not bcrypt.checkpw(current_password.encode(), stored_password.encode()):
        conn.close()
        return {"error": "Current password is incorrect"}
    
    # Check if new username already exists
    cursor.execute("""
        SELECT user_id FROM users WHERE username = ? AND user_id != ?
    """, (new_username, user_id))
    
    if cursor.fetchone() is not None:
        conn.close()
        return {"error": "Username already taken"}
    
    # Update the username
    try:
        cursor.execute("""
            UPDATE users SET username = ? WHERE user_id = ?
        """, (new_username, user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "Username already taken"}
    finally:
        conn.close()
    
    return user_id


def change_password(user_id, current_password, new_password):
    if not new_password:
        return {"error": "New password cannot be empty"}
    
    if len(new_password) < 8:
        return {"error": "New password must be at least 8 characters"}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First verify the current password
    cursor.execute("""
        SELECT password FROM users WHERE user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        return {"error": "User not found"}
    
    stored_password = row[0]
    
    if not bcrypt.checkpw(current_password.encode(), stored_password.encode()):
        conn.close()
        return {"error": "Current password is incorrect"}
    
    # Hash and update the new password
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute("""
        UPDATE users SET password = ? WHERE user_id = ?
    """, (hashed_password, user_id))
    
    conn.commit()
    conn.close()
    
    return user_id

#recipe functions
def create_recipe(user_id, title, ingredients, instructions, image_path, is_public):
    if not title or not title.strip():
        return {"error": "Title cannot be empty"}
    
    if not ingredients:
        return {"error": "Ingredients cannot be empty"}
    
    if not instructions or not instructions.strip():
        return {"error": "Instructions cannot be empty"}

    conn = get_db_connection()
    cursor = conn.cursor()

    # Handle both string and list formats for ingredients
    if isinstance(ingredients, list):
        # New structured format - convert to JSON string for storage
        ingredients_json = json.dumps(ingredients)
    else:
        # Legacy string format
        ingredients_json = ingredients

    cursor.execute("""
        INSERT INTO recipes (user_id, title, ingredients, instructions, image_path, is_public)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, title, ingredients_json, instructions, image_path, is_public))

    conn.commit()
    
    recipe_id = cursor.lastrowid

    conn.close()

    return recipe_id

def get_recipe(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT recipe_id, user_id, title, ingredients, instructions, image_path, is_public, created_at
        FROM recipes
        WHERE recipe_id = ?
    """, (recipe_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    recipe = {
        'recipe_id': row[0],
        'user_id': row[1],
        'title': row[2],
        'ingredients': row[3],
        'instructions': row[4],
        'image_path': row[5],
        'is_public': bool(row[6]),
        'created_at': row[7]
    }

    return recipe

def get_user_cookbook(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT recipe_id, title, ingredients, instructions, image_path, is_public, created_at
        FROM recipes
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    
    conn.close()
    
    recipes = []
    for row in rows:
        recipes.append({
            'recipe_id': row[0],
            'title': row[1],
            'ingredients': row[2],
            'instructions': row[3],
            'image_path': row[4],
            'is_public': bool(row[5]),
            'created_at': row[6]
        })
    
    return recipes

def update_user_recipes(recipe_id, title, ingredients, instructions, image_path, is_public):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Handle both string and list formats for ingredients
        if isinstance(ingredients, list):
            # New structured format - convert to JSON string for storage in recipes table
            ingredients_json = json.dumps(ingredients)
        else:
            # Legacy string format
            ingredients_json = ingredients
        
        # Update the recipe in recipes table
        cursor.execute("""
            UPDATE recipes
            SET title = ?, 
                ingredients = ?, 
                instructions = ?, 
                image_path = ?, 
                is_public = ?
            WHERE recipe_id = ?
        """, (title, ingredients_json, instructions, image_path, is_public, recipe_id))
        
        # If ingredients is a structured list, also update the recipe_ingredients table
        if isinstance(ingredients, list):
            # Delete existing structured ingredients
            cursor.execute("""
                DELETE FROM recipe_ingredients 
                WHERE recipe_id = ?
            """, (recipe_id,))
            
            # Insert new structured ingredients
            for idx, ing in enumerate(ingredients):
                cursor.execute("""
                    INSERT INTO recipe_ingredients (recipe_id, quantity, unit, name, order_index)
                    VALUES (?, ?, ?, ?, ?)
                """, (recipe_id, ing.get('quantity'), ing.get('unit'), ing.get('name'), idx))
        
        conn.commit()
        conn.close()
        
        return recipe_id
        
    except Exception as e:
        print(f"Error updating recipe: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return None

def delete_recipe(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM recipes
        WHERE recipe_id = ?
    """, (recipe_id,))
    
    conn.commit()

    conn.close()

    return "Recipe Successfully Deleted"

def delete_user_recipe(recipe_id, user_id=None):
    """
    Delete a recipe from the database.
    If user_id is provided, only delete if the recipe belongs to that user.
    Returns success message or error dict.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # If user_id is provided, verify ownership before deleting
        if user_id is not None:
            cursor.execute("""
                SELECT recipe_id FROM recipes
                WHERE recipe_id = ? AND user_id = ?
            """, (recipe_id, user_id))
            
            if cursor.fetchone() is None:
                conn.close()
                return {"error": "Recipe not found or you don't have permission to delete it"}
        
        # Delete the recipe (CASCADE will handle related tables)
        cursor.execute("""
            DELETE FROM recipes
            WHERE recipe_id = ?
        """, (recipe_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"error": "Recipe not found"}
        
        conn.commit()
        conn.close()
        
        return "Recipe Successfully Deleted"
        
    except Exception as e:
        conn.close()
        return {"error": f"Failed to delete recipe: {str(e)}"}

def get_all_public_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.recipe_id, r.user_id, r.title, r.ingredients, r.instructions, 
               r.image_path, r.is_public, r.created_at, u.username
        FROM recipes r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.is_public = 1
        ORDER BY r.created_at DESC
    """)
    
    rows = cursor.fetchall()
    
    conn.close()
    
    recipes = []
    for row in rows:
        recipes.append({
            'recipe_id': row[0],
            'user_id': row[1],
            'title': row[2],
            'ingredients': row[3],
            'instructions': row[4],
            'image_path': row[5],
            'is_public': bool(row[6]),
            'created_at': row[7],
            'username': row[8]
        })
    
    return recipes

def get_random_public_recipe():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get today's date as a seed
    today = date.today()
    seed = int(today.strftime('%Y%m%d'))
    
    cursor.execute("""
        SELECT r.recipe_id, r.user_id, r.title, r.ingredients, r.instructions, 
               r.image_path, r.is_public, r.created_at, u.username
        FROM recipes r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.is_public = 1
        ORDER BY (r.recipe_id * ?) % 1000000
        LIMIT 1
    """, (seed,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    recipe = {
        'recipe_id': row[0],
        'user_id': row[1],
        'title': row[2],
        'ingredients': row[3],
        'instructions': row[4],
        'image_path': row[5],
        'is_public': bool(row[6]),
        'created_at': row[7],
        'username': row[8]
    }
    
    return recipe

def save_public_recipe(user_id, recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO saved_recipes (user_id, recipe_id)
            VALUES (?, ?)
        """, (user_id, recipe_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "Recipe already saved"}
    finally:
        conn.close()
    
    return "Recipe saved successfully"

def unsave_public_recipe(user_id, recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM saved_recipes
        WHERE user_id = ? AND recipe_id = ?
    """, (user_id, recipe_id))
    
    conn.commit()
    conn.close()
    
    return "Recipe unsaved successfully"

def get_saved_public_recipes(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.recipe_id, r.user_id, r.title, r.ingredients, r.instructions, 
               r.image_path, r.is_public, r.created_at, u.username
        FROM recipes r
        JOIN saved_recipes sr ON r.recipe_id = sr.recipe_id
        JOIN users u ON r.user_id = u.user_id
        WHERE sr.user_id = ?
        ORDER BY r.created_at DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    
    conn.close()
    
    recipes = []
    for row in rows:
        recipes.append({
            'recipe_id': row[0],
            'user_id': row[1],
            'title': row[2],
            'ingredients': row[3],
            'instructions': row[4],
            'image_path': row[5],
            'is_public': bool(row[6]),
            'created_at': row[7],
            'username': row[8]
        })
    
    return recipes

def is_recipe_saved(user_id, recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 1 FROM saved_recipes
        WHERE user_id = ? AND recipe_id = ?
    """, (user_id, recipe_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def get_recipe_ingredients(recipe_id, target_units=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ingredient_id, quantity, unit, name, order_index
        FROM recipe_ingredients
        WHERE recipe_id = ?
        ORDER BY order_index
    """, (recipe_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    ingredients = []
    for row in rows:
        quantity = row[1]
        unit = row[2]
        
        # Convert units if target system specified
        if target_units and quantity is not None:
            quantity, unit = convert_unit(quantity, unit, target_units)
        
        ingredients.append({
            'ingredient_id': row[0],
            'quantity': quantity,
            'unit': unit,
            'name': row[3],
            'order_index': row[4]
        })
    
    return ingredients

#pantry functions
def create_pantry_item(user_id, name, quantity, unit, expiration_date, low_threshold):
    if not name or not name.strip():
        return {"error": "Item name cannot be empty"}
    
    try:
        quantity = float(quantity)
        if quantity <= 0:
            return {"error": "Quantity must be greater than 0"}
    except (ValueError, TypeError):
        return {"error": "Quantity must be a valid number"}

    try:
        datetime.strptime(expiration_date, '%Y-%m-%d')
    except ValueError:
        return {"error": "Expiration date must be in YYYY-MM-DD format"}

    if low_threshold is not None:
        try:
            low_threshold = float(low_threshold)
            if low_threshold < 0:
                return {"error": "Low threshold cannot be negative"}
        except (ValueError, TypeError):
            return {"error": "Low threshold must be a valid number"}
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pantry (user_id, name, quantity, unit, expiration_date, low_threshold)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, name, quantity, unit, expiration_date, low_threshold))

    conn.commit()
    
    pantry_id = cursor.lastrowid

    conn.close()

    return pantry_id

def get_user_pantry(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT pantry_id, name, quantity, unit, expiration_date, low_threshold
        FROM pantry
        WHERE user_id = ?
        ORDER BY expiration_date ASC
    """, (user_id,))
    
    rows = cursor.fetchall()
    
    conn.close()
    
    pantry = []
    for row in rows:
        pantry.append({
            'pantry_id': row[0],
            'name': row[1],
            'quantity': row[2],
            'unit': row[3],
            'expiration_date': row[4],
            'low_threshold': row[5]
        })
    
    return pantry

def delete_pantry_item(pantry_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM pantry
        WHERE pantry_id = ?
    """, (pantry_id,))
    
    conn.commit()

    conn.close()

    return "Item Successfully Removed"

def update_pantry_item(pantry_id, name, quantity, unit, expiration_date, low_threshold):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE pantry
        SET name = ?, 
            quantity = ?, 
            unit = ?, 
            expiration_date = ?, 
            low_threshold = ?
        WHERE pantry_id = ?
    """, (name, quantity, unit, expiration_date, low_threshold, pantry_id))

    conn.commit()

    conn.close()

    return pantry_id

#shopping list functions
def create_shopping_list_item(user_id, name, quantity, unit, is_checked):
    if not name or not name.strip():
        return {"error": "Item name cannot be empty"}

    if quantity is not None:
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return {"error": "Quantity must be greater than 0"}
        except (ValueError, TypeError):
            return {"error": "Quantity must be a valid number"}

    if unit is not None and not isinstance(unit, str):
        return {"error": "Unit must be a string"}

    if not isinstance(is_checked, bool):
        return {"error": "is_checked must be True or False"}
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO shopping_list (user_id, name, quantity, unit, is_checked)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, quantity, unit, is_checked))

    conn.commit()
    
    list_id = cursor.lastrowid
    
    conn.close()
    
    return list_id

def get_user_shopping_list(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT list_id, name, quantity, unit, is_checked
        FROM shopping_list
        WHERE user_id = ?
    """, (user_id,))
    
    rows = cursor.fetchall()
    
    conn.close()
    
    shopping_list = []
    for row in rows:
        shopping_list.append({
            'list_id': row[0],
            'name': row[1],
            'quantity': row[2],
            'unit': row[3],
            'is_checked': bool(row[4])
        })
    
    return shopping_list

def delete_shopping_list_item(list_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM shopping_list
        WHERE list_id = ?
    """, (list_id,))
    
    conn.commit()

    conn.close()

    return "Item Successfully Removed"

def update_shopping_list_item(list_id, name, quantity, unit, is_checked):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE shopping_list
        SET name = ?, 
            quantity = ?, 
            unit = ?, 
            is_checked = ?
        WHERE list_id = ?
    """, (name, quantity, unit, is_checked, list_id))

    conn.commit()

    conn.close()

    return list_id

#meal plan functions
def create_meal_plan(user_id, date, recipe_id, meal_type):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return {"error": "Date must be in YYYY-MM-DD format"}

    valid_meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    if meal_type not in valid_meal_types:
        return {"error": f"Meal type must be one of: {', '.join(valid_meal_types)}"}
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT recipe_id FROM recipes 
        WHERE recipe_id = ? AND (user_id = ? OR is_public = 1)
    """, (recipe_id, user_id))
    
    if cursor.fetchone() is None:
        conn.close()
        return {"error": "Recipe not found or not accessible"}
    
    cursor.execute("""
        INSERT INTO meal_plan (user_id, date, recipe_id, meal_type)
        VALUES (?, ?, ?, ?)
    """, (user_id, date, recipe_id, meal_type))
    
    conn.commit()
    
    plan_id = cursor.lastrowid
    
    conn.close()
    
    return plan_id

def get_user_meal_plan(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT plan_id, date, recipe_id, meal_type
        FROM meal_plan
        WHERE user_id = ?
    """, (user_id,))
    
    rows = cursor.fetchall()
    
    conn.close()
    
    meal_plan = []
    for row in rows:
        meal_plan.append({
            'plan_id': row[0],
            'date': row[1],
            'recipe_id': row[2],
            'meal_type': row[3]
        })
    
    return meal_plan

def delete_recipe_from_meal_plan(plan_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM meal_plan
        WHERE plan_id = ?
    """, (plan_id,))
    
    conn.commit()

    conn.close()

    return "Recipe Successfully Removed"

def update_meal_plan(plan_id, date, recipe_id, meal_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meal_plan
        SET date = ?, 
            recipe_id = ?, 
            meal_type = ?
        WHERE plan_id = ?
    """, (date, recipe_id, meal_type, plan_id))

    conn.commit()

    conn.close()

    return plan_id

#settings page functions
def get_user_settings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT theme, units, landing_page
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None

    return {
        'theme': row[0],
        'units': row[1],
        'landing_page': row[2] if row[2] else 'dashboard'
    }

def update_user_settings(user_id, theme, landing_page='dashboard'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users
        SET theme = ?, landing_page = ?
        WHERE user_id = ?
    """, (theme, landing_page, user_id))
    
    conn.commit()
    conn.close()
    
    return user_id

def reset_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM recipes WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM saved_recipes WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM pantry WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM shopping_list WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM meal_plan WHERE user_id = ?", (user_id,))

        cursor.execute("""
            UPDATE users
            SET theme = 'light', landing_page = 'dashboard'
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
    finally:
        conn.close()

    return "User data has been reset"