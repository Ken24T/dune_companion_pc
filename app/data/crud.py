import sqlite3
from datetime import datetime, timezone
from typing import Optional, List

from app.data.database import get_db_connection
from app.utils.logger import get_logger
from app.data.models import (
    Resource, CraftingRecipe, RecipeIngredient, SkillTreeNode, 
    BaseBlueprint, LoreEntry, UserSetting #, UserNote, AIChatHistory # Temporarily remove unused imports
)

logger = get_logger(__name__)

# --- Helper timestamp function ---
def get_current_utc_timestamp() -> str:
    """Generate a UTC timestamp string in the same format as the database default.
    
    Returns timestamp in format: 'YYYY-MM-DD HH:MM:SS.ffffff' (space-separated, UTC)
    This matches the database schema format: strftime('%Y-%m-%d %H:%M:%f', 'now', 'utc')
    """
    # Use UTC timezone and format to match database
    now_utc = datetime.now(timezone.utc)
    # Format to match database: '%Y-%m-%d %H:%M:%S.%f' (but use 6 digits for microseconds)
    return now_utc.strftime('%Y-%m-%d %H:%M:%S.%f')

# --- Helper to_dict functions ---
def _resource_to_dict(resource: Resource) -> dict:
    return {
        "id": resource.id,
        "name": resource.name,
        "description": resource.description,
        "rarity": resource.rarity,
        "category": resource.category,
        "source_locations": resource.source_locations,
        "icon_path": resource.icon_path,
        "discovered": resource.discovered,
        "created_at": resource.created_at,
        "updated_at": resource.updated_at,
    }

def _crafting_recipe_to_dict(recipe: CraftingRecipe) -> dict:
    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description,
        "output_item_name": recipe.output_item_name,
        "output_quantity": recipe.output_quantity,
        "crafting_time_seconds": recipe.crafting_time_seconds,
        "required_station": recipe.required_station,
        "skill_requirement": recipe.skill_requirement,
        "icon_path": recipe.icon_path,
        "discovered": recipe.discovered,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
        # Ingredients are handled separately if needed in a full representation
    }

def _skill_tree_node_to_dict(node: SkillTreeNode) -> dict:
    return {
        "id": node.id,
        "name": node.name,
        "description": node.description,
        "skill_tree_name": node.skill_tree_name,
        "parent_node_id": node.parent_node_id,
        "unlock_cost": node.unlock_cost,
        "effects": node.effects,
        "icon_path": node.icon_path,
        "unlocked": node.unlocked,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
    }

def _base_blueprint_to_dict(base_blueprint: BaseBlueprint) -> dict:
    return {
        "id": base_blueprint.id,
        "name": base_blueprint.name,
        "description": base_blueprint.description,
        "category": base_blueprint.category,
        "thumbnail_path": base_blueprint.thumbnail_path,
        "created_at": base_blueprint.created_at,
        "updated_at": base_blueprint.updated_at,
    }

def _lore_entry_to_dict(lore_entry: LoreEntry) -> dict:
    return {
        "id": lore_entry.id,
        "title": lore_entry.title,
        "content_markdown": lore_entry.content_markdown,
        "category": lore_entry.category,
        "tags": lore_entry.tags,
        "created_at": lore_entry.created_at,
        "updated_at": lore_entry.updated_at,
    }

def _user_setting_to_dict(user_setting: UserSetting) -> dict:
    return {
        "id": user_setting.id,
        "setting_key": user_setting.setting_key,
        "setting_value": user_setting.setting_value,
        "created_at": user_setting.created_at,
        "updated_at": user_setting.updated_at,
    }

# --- CRUD for Resource ---
def create_resource(
    db_path: str, 
    name: str, 
    description: Optional[str] = None, 
    rarity: Optional[str] = None, 
    category: Optional[str] = None, 
    source_locations: Optional[str] = None, 
    icon_path: Optional[str] = None, 
    discovered: int = 0
) -> Optional[Resource]:
    logger.info(f"Attempting to create resource with name: {name}")
    conn = get_db_connection(db_path)
    if conn is None:
        logger.error("Failed to create database connection.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM resource WHERE name = ?", (name,))
        if cursor.fetchone():
            logger.warning(f"Resource with name '{name}' already exists.")
            return None
        
        current_time = get_current_utc_timestamp()
        cursor.execute(
            '''INSERT INTO resource (name, description, rarity, category, source_locations, icon_path, discovered, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, description, rarity, category, source_locations, icon_path, discovered, current_time, current_time)
        )
        conn.commit()
        resource_id = cursor.lastrowid
        logger.info(f"Resource created with ID: {resource_id}, Name: {name}")
        return Resource(id=resource_id, name=name, description=description, rarity=rarity, category=category, source_locations=source_locations, icon_path=icon_path, discovered=discovered, created_at=current_time, updated_at=current_time)
    except sqlite3.Error as e:
        logger.error(f"Error creating resource: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_resource_by_id(db_path: str, resource_id: int) -> Optional[Resource]:
    logger.debug(f"Fetching resource with ID: {resource_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, rarity, category, source_locations, icon_path, discovered, created_at, updated_at FROM resource WHERE id = ?", (resource_id,))
        row = cursor.fetchone()
        if row:
            return Resource(id=row[0], name=row[1], description=row[2], rarity=row[3], category=row[4], source_locations=row[5], icon_path=row[6], discovered=row[7], created_at=row[8], updated_at=row[9])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching resource by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_resource_by_name(db_path: str, name: str) -> Optional[Resource]:
    logger.debug(f"Fetching resource with name: {name}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, rarity, category, source_locations, icon_path, discovered, created_at, updated_at FROM resource WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return Resource(id=row[0], name=row[1], description=row[2], rarity=row[3], category=row[4], source_locations=row[5], icon_path=row[6], discovered=row[7], created_at=row[8], updated_at=row[9])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching resource by name: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_resources(db_path: str) -> List[Resource]:
    logger.debug("Fetching all resources")
    conn = get_db_connection(db_path) 
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, rarity, category, source_locations, icon_path, discovered, created_at, updated_at FROM resource ORDER BY name ASC")
        rows = cursor.fetchall()
        return [Resource(id=row[0], name=row[1], description=row[2], rarity=row[3], category=row[4], source_locations=row[5], icon_path=row[6], discovered=row[7], created_at=row[8], updated_at=row[9]) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error fetching all resources: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_resource(
    db_path: str, 
    resource_id: int, 
    name: Optional[str] = None,
    description: Optional[str] = None, 
    rarity: Optional[str] = None, 
    category: Optional[str] = None, 
    source_locations: Optional[str] = None, 
    icon_path: Optional[str] = None,
    discovered: Optional[int] = None
) -> Optional[Resource]:
    logger.info(f"Attempting to update resource with ID: {resource_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    
    fields_to_update = []
    params = []

    if name is not None:
        # Check for name uniqueness if it's being changed
        current_resource = get_resource_by_id(db_path, resource_id) # This will open a new connection, consider passing conn or fetching first
        if current_resource and current_resource.name != name:
            existing_resource = get_resource_by_name(db_path, name) # Same here
            if existing_resource and existing_resource.id != resource_id:
                logger.warning(f"Cannot update resource ID {resource_id}: another resource with name '{name}' already exists (ID: {existing_resource.id}).")
                return None # Or handle as an error / return current state
        fields_to_update.append("name = ?")
        params.append(name)
        
    if description is not None:
        fields_to_update.append("description = ?")
        params.append(description)
    if rarity is not None:
        fields_to_update.append("rarity = ?")
        params.append(rarity)
    if category is not None:
        fields_to_update.append("category = ?")
        params.append(category)
    if source_locations is not None:
        fields_to_update.append("source_locations = ?")
        params.append(source_locations)
    if icon_path is not None:
        fields_to_update.append("icon_path = ?")
        params.append(icon_path)
    if discovered is not None:
        fields_to_update.append("discovered = ?")
        params.append(discovered)

    if not fields_to_update:
        logger.info("No fields provided to update for resource.")
        # Return current state of the resource if no updates are made        return get_resource_by_id(db_path, resource_id)

    current_time = get_current_utc_timestamp()
    fields_to_update.append("updated_at = ?")
    params.append(current_time)
    params.append(resource_id) # For the WHERE clause

    sql = f"UPDATE resource SET {', '.join(fields_to_update)} WHERE id = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Resource with ID {resource_id} not found for update.")
            return None
        logger.info(f"Resource with ID {resource_id} updated successfully.")
        return get_resource_by_id(db_path, resource_id) # Fetch and return the updated resource
    except sqlite3.Error as e:
        # Specific check for unique constraint on name, though the above check should prevent it
        if "UNIQUE constraint failed: resource.name" in str(e):
            logger.warning(f"Failed to update resource ID {resource_id}: name conflict. {e}")
            # Potentially return the resource's state before attempting the conflicting update
            # For now, let's return None as the update operation failed.
            return None 
        logger.error(f"Error updating resource: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_resource(db_path: str, resource_id: int) -> bool:
    logger.info(f"Attempting to delete resource with ID: {resource_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resource WHERE id = ?", (resource_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Resource with ID {resource_id} deleted successfully.")
            return True
        logger.warning(f"Resource with ID {resource_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting resource: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- CRUD for CraftingRecipe ---
def create_crafting_recipe(
    db_path: str,
    name: str,
    output_item_name: str,
    output_quantity: int = 1,
    description: Optional[str] = None,
    crafting_time_seconds: Optional[int] = None,
    required_station: Optional[str] = None,
    skill_requirement: Optional[str] = None,
    icon_path: Optional[str] = None,
    discovered: int = 0,
    ingredients: Optional[List[RecipeIngredient]] = None # List of RecipeIngredient data (not necessarily model instances yet)
) -> Optional[CraftingRecipe]:
    logger.info(f"Attempting to create crafting recipe: {name}")
    conn = get_db_connection(db_path)
    if conn is None:
        logger.error("Failed to get DB connection for creating crafting recipe.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM crafting_recipe WHERE name = ?", (name,))
        if cursor.fetchone():
            logger.warning(f"Crafting recipe with name '{name}' already exists.")
            return None

        current_time = get_current_utc_timestamp()
        cursor.execute(
            '''INSERT INTO crafting_recipe 
               (name, description, output_item_name, output_quantity, crafting_time_seconds, 
                required_station, skill_requirement, icon_path, discovered, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, description, output_item_name, output_quantity, crafting_time_seconds,
             required_station, skill_requirement, icon_path, discovered, current_time, current_time)
        )
        recipe_id = cursor.lastrowid
        if recipe_id is None: # Should not happen if insert is successful
            conn.rollback()
            logger.error("Failed to get lastrowid for new crafting recipe.")
            return None

        # Handle ingredients
        recipe_ingredients_models = []
        if ingredients:
            for ing_data in ingredients:
                # Assuming ing_data contains resource_id and quantity
                # We don't create RecipeIngredient model instances here directly for insertion
                # as the table schema is simple.
                cursor.execute(
                    "INSERT INTO recipe_ingredient (recipe_id, resource_id, quantity) VALUES (?, ?, ?)",
                    (recipe_id, ing_data.resource_id, ing_data.quantity)
                )
                # For returning the full CraftingRecipe object, we can create the model instances
                recipe_ingredients_models.append(
                    RecipeIngredient(
                        recipe_id=recipe_id, 
                        resource_id=ing_data.resource_id, 
                        quantity=ing_data.quantity
                        # resource_name will be populated by the get methods
                    )
                )
        
        conn.commit()
        logger.info(f"Crafting recipe '{name}' created with ID: {recipe_id}")
        return CraftingRecipe(
            id=recipe_id, name=name, description=description, output_item_name=output_item_name,
            output_quantity=output_quantity, crafting_time_seconds=crafting_time_seconds,
            required_station=required_station, skill_requirement=skill_requirement,
            icon_path=icon_path, discovered=discovered, ingredients=recipe_ingredients_models,
            created_at=current_time, updated_at=current_time
        )
    except sqlite3.Error as e:
        logger.error(f"Error creating crafting recipe '{name}': {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def get_crafting_recipe_by_id(db_path: str, recipe_id: int) -> Optional[CraftingRecipe]:
    logger.debug(f"Fetching crafting recipe with ID: {recipe_id}")
    conn = get_db_connection(db_path)
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, output_item_name, output_quantity, crafting_time_seconds, "
            "required_station, skill_requirement, icon_path, discovered, created_at, updated_at "
            "FROM crafting_recipe WHERE id = ?", (recipe_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        # Fetch ingredients
        cursor.execute(
            "SELECT ri.id, ri.recipe_id, ri.resource_id, ri.quantity, r.name "
            "FROM recipe_ingredient ri JOIN resource r ON ri.resource_id = r.id "
            "WHERE ri.recipe_id = ?", (recipe_id,)
        )
        ingredients_rows = cursor.fetchall()
        ingredients_list = [
            RecipeIngredient(id=ing_row[0], recipe_id=ing_row[1], resource_id=ing_row[2], quantity=ing_row[3], resource_name=ing_row[4])
            for ing_row in ingredients_rows
        ]
        
        return CraftingRecipe(
            id=row[0], name=row[1], description=row[2], output_item_name=row[3], output_quantity=row[4],
            crafting_time_seconds=row[5], required_station=row[6], skill_requirement=row[7],
            icon_path=row[8], discovered=row[9], created_at=row[10], updated_at=row[11],
            ingredients=ingredients_list
        )
    except sqlite3.Error as e:
        logger.error(f"Error fetching crafting recipe by ID {recipe_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_crafting_recipe_by_name(db_path: str, name: str) -> Optional[CraftingRecipe]:
    logger.debug(f"Fetching crafting recipe with name: {name}")
    conn = get_db_connection(db_path)
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM crafting_recipe WHERE name = ?", (name,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        # If found, delegate to get_crafting_recipe_by_id to fetch full details including ingredients
        return get_crafting_recipe_by_id(db_path, row[0])
    except sqlite3.Error as e:
        logger.error(f"Error fetching crafting recipe by name '{name}': {e}")
        return None
    finally:
        if conn: # Connection might be closed by get_crafting_recipe_by_id if called
            conn.close()


def get_all_crafting_recipes(db_path: str) -> List[CraftingRecipe]:
    logger.debug("Fetching all crafting recipes")
    conn = get_db_connection(db_path)
    if conn is None:
        return []
    recipes_list = []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, output_item_name, output_quantity, crafting_time_seconds, "
            "required_station, skill_requirement, icon_path, discovered, created_at, updated_at "
            "FROM crafting_recipe ORDER BY name ASC"
        )
        recipe_rows = cursor.fetchall()
        
        for row in recipe_rows:
            recipe_id = row[0]
            # Fetch ingredients for each recipe
            cursor.execute(
                "SELECT ri.id, ri.recipe_id, ri.resource_id, ri.quantity, r.name "
                "FROM recipe_ingredient ri JOIN resource r ON ri.resource_id = r.id "
                "WHERE ri.recipe_id = ?", (recipe_id,)
            )
            ingredients_rows = cursor.fetchall()
            ingredients_list = [
                RecipeIngredient(id=ing_row[0], recipe_id=ing_row[1], resource_id=ing_row[2], quantity=ing_row[3], resource_name=ing_row[4])
                for ing_row in ingredients_rows
            ]
            recipes_list.append(CraftingRecipe(
                id=row[0], name=row[1], description=row[2], output_item_name=row[3], output_quantity=row[4],
                crafting_time_seconds=row[5], required_station=row[6], skill_requirement=row[7],
                icon_path=row[8], discovered=row[9], created_at=row[10], updated_at=row[11],
                ingredients=ingredients_list
            ))
        return recipes_list
    except sqlite3.Error as e:
        logger.error(f"Error fetching all crafting recipes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_crafting_recipe(
    db_path: str,
    recipe_id: int,
    name: Optional[str] = None,
    output_item_name: Optional[str] = None,
    output_quantity: Optional[int] = None,
    description: Optional[str] = None,
    crafting_time_seconds: Optional[int] = None,
    required_station: Optional[str] = None,
    skill_requirement: Optional[str] = None,
    icon_path: Optional[str] = None,
    discovered: Optional[int] = None,
    ingredients: Optional[List[RecipeIngredient]] = None # Pass full new list of ingredients
) -> Optional[CraftingRecipe]:
    logger.info(f"Attempting to update crafting recipe ID: {recipe_id}")
    conn = get_db_connection(db_path)
    if conn is None:
        return None

    fields_to_update = []
    params = []

    if name is not None:
        # Check for name uniqueness if it's being changed
        current_recipe = get_crafting_recipe_by_id(db_path, recipe_id) # Opens new connection
        if current_recipe and current_recipe.name != name:
            existing_recipe = get_crafting_recipe_by_name(db_path, name) # Opens new connection
            if existing_recipe and existing_recipe.id != recipe_id:
                logger.warning(f"Cannot update recipe ID {recipe_id}: another recipe with name '{name}' already exists (ID: {existing_recipe.id}).")
                return None
        fields_to_update.append("name = ?")
        params.append(name)
    
    if output_item_name is not None:
        fields_to_update.append("output_item_name = ?")
        params.append(output_item_name)
    if output_quantity is not None:
        fields_to_update.append("output_quantity = ?")
        params.append(output_quantity)
    if description is not None:
        fields_to_update.append("description = ?")
        params.append(description)
    if crafting_time_seconds is not None:
        fields_to_update.append("crafting_time_seconds = ?")
        params.append(crafting_time_seconds)
    if required_station is not None:
        fields_to_update.append("required_station = ?")
        params.append(required_station)
    if skill_requirement is not None:
        fields_to_update.append("skill_requirement = ?")
        params.append(skill_requirement)
    if icon_path is not None:
        fields_to_update.append("icon_path = ?")
        params.append(icon_path)
    if discovered is not None:
        fields_to_update.append("discovered = ?")
        params.append(discovered)

    try:
        cursor = conn.cursor()
          # Update main recipe fields if any
        if fields_to_update:
            current_time = get_current_utc_timestamp()
            fields_to_update.append("updated_at = ?")
            params.append(current_time)
            
            update_sql = f"UPDATE crafting_recipe SET {', '.join(fields_to_update)} WHERE id = ?"
            params.append(recipe_id)
            cursor.execute(update_sql, tuple(params))
            if cursor.rowcount == 0 and not ingredients: # if no ingredients to update and main update failed
                 # Check if the recipe actually exists before declaring "not found"
                check_exists = get_crafting_recipe_by_id(db_path, recipe_id) # Opens new connection
                if not check_exists:
                    logger.warning(f"Crafting recipe with ID {recipe_id} not found for update.")
                    return None
        
        # Handle ingredients update: delete old, insert new
        # This is a common strategy. More complex diffing is possible but adds complexity.
        if ingredients is not None: # If ingredients list is provided (even if empty)
            cursor.execute("DELETE FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
            for ing_data in ingredients:
                cursor.execute(
                    "INSERT INTO recipe_ingredient (recipe_id, resource_id, quantity) VALUES (?, ?, ?)",
                    (recipe_id, ing_data.resource_id, ing_data.quantity)
                )            # If only ingredients were updated, ensure updated_at is also set for the main recipe
            if not fields_to_update:
                 cursor.execute("UPDATE crafting_recipe SET updated_at = ? WHERE id = ?", (get_current_utc_timestamp(), recipe_id))


        conn.commit()
        logger.info(f"Crafting recipe ID {recipe_id} updated successfully.")
        # Fetch and return the updated recipe, including new ingredients
        # This re-opens a connection, which is fine for this structure.
        return get_crafting_recipe_by_id(db_path, recipe_id) 

    except sqlite3.Error as e:
        logger.error(f"Error updating crafting recipe ID {recipe_id}: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def delete_crafting_recipe(db_path: str, recipe_id: int) -> bool:
    logger.info(f"Attempting to delete crafting recipe ID: {recipe_id}")
    conn = get_db_connection(db_path)
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        # Ingredients are deleted by CASCADE constraint in DB schema
        cursor.execute("DELETE FROM crafting_recipe WHERE id = ?", (recipe_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Crafting recipe ID {recipe_id} and its ingredients deleted successfully.")
            return True
        logger.warning(f"Crafting recipe ID {recipe_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting crafting recipe ID {recipe_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# --- CRUD for BaseBlueprint ---
def create_base_blueprint(
    db_path: str, 
    name: str, 
    description: Optional[str] = None, 
    category: Optional[str] = None, 
    thumbnail_path: Optional[str] = None
) -> Optional[BaseBlueprint]:
    logger.info(f"Attempting to create base blueprint with name: {name}")
    conn = get_db_connection(db_path)
    if conn is None:
        logger.error("Failed to create database connection.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM base_blueprints WHERE name = ?", (name,))
        if cursor.fetchone():
            logger.warning(f"Base blueprint with name '{name}' already exists.")
            return None
        
        current_time = get_current_utc_timestamp()
        cursor.execute(
            '''INSERT INTO base_blueprints (name, description, category, thumbnail_path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (name, description, category, thumbnail_path, current_time, current_time)
        )
        conn.commit()
        blueprint_id = cursor.lastrowid
        logger.info(f"Base blueprint created with ID: {blueprint_id}, Name: {name}")
        return BaseBlueprint(id=blueprint_id, name=name, description=description, category=category, thumbnail_path=thumbnail_path, created_at=current_time, updated_at=current_time)
    except sqlite3.Error as e:
        logger.error(f"Error creating base blueprint: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_base_blueprint_by_id(db_path: str, blueprint_id: int) -> Optional[BaseBlueprint]:
    logger.debug(f"Fetching base blueprint with ID: {blueprint_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, category, thumbnail_path, created_at, updated_at FROM base_blueprints WHERE id = ?", (blueprint_id,))
        row = cursor.fetchone()
        if row:
            return BaseBlueprint(id=row[0], name=row[1], description=row[2], category=row[3], thumbnail_path=row[4], created_at=row[5], updated_at=row[6])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching base blueprint by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_base_blueprint_by_name(db_path: str, name: str) -> Optional[BaseBlueprint]:
    logger.debug(f"Fetching base blueprint with name: {name}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, category, thumbnail_path, created_at, updated_at FROM base_blueprints WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return BaseBlueprint(id=row[0], name=row[1], description=row[2], category=row[3], thumbnail_path=row[4], created_at=row[5], updated_at=row[6])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching base blueprint by name: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_base_blueprints(db_path: str) -> List[BaseBlueprint]:
    logger.debug("Fetching all base blueprints")
    conn = get_db_connection(db_path) 
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, category, thumbnail_path, created_at, updated_at FROM base_blueprints")
        rows = cursor.fetchall()
        return [BaseBlueprint(id=row[0], name=row[1], description=row[2], category=row[3], thumbnail_path=row[4], created_at=row[5], updated_at=row[6]) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error fetching all base blueprints: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_base_blueprint(
    db_path: str, 
    blueprint_id: int, 
    name: Optional[str] = None,
    description: Optional[str] = None, 
    category: Optional[str] = None, 
    thumbnail_path: Optional[str] = None
) -> Optional[BaseBlueprint]:
    logger.info(f"Attempting to update base blueprint with ID: {blueprint_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    
    fields_to_update = []
    params = []

    if name is not None:
        current_bp = get_base_blueprint_by_id(db_path, blueprint_id)
        if current_bp and current_bp.name != name:
            existing_bp = get_base_blueprint_by_name(db_path, name)
            if existing_bp:
                logger.warning(f"Cannot update base blueprint ID {blueprint_id}: another blueprint with name '{name}' already exists (ID: {existing_bp.id}).")
                return None
        fields_to_update.append("name = ?")
        params.append(name)
        
    if description is not None:
        fields_to_update.append("description = ?")
        params.append(description)
    if category is not None:
        fields_to_update.append("category = ?")
        params.append(category)
    if thumbnail_path is not None:
        fields_to_update.append("thumbnail_path = ?")
        params.append(thumbnail_path)

    if not fields_to_update:
        logger.info("No fields provided to update for base blueprint.")
        return get_base_blueprint_by_id(db_path, blueprint_id)

    current_time = get_current_utc_timestamp()
    fields_to_update.append("updated_at = ?")
    params.append(current_time)
    params.append(blueprint_id)

    sql = f"UPDATE base_blueprints SET {', '.join(fields_to_update)} WHERE id = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Base blueprint with ID {blueprint_id} not found for update.")
            return None
        logger.info(f"Base blueprint with ID {blueprint_id} updated successfully.")
        return get_base_blueprint_by_id(db_path, blueprint_id)
    except sqlite3.Error as e:
        logger.error(f"Error updating base blueprint: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_base_blueprint(db_path: str, blueprint_id: int) -> bool:
    logger.info(f"Attempting to delete base blueprint with ID: {blueprint_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM base_blueprints WHERE id = ?", (blueprint_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Base blueprint with ID {blueprint_id} deleted successfully.")
            return True
        logger.warning(f"Base blueprint with ID {blueprint_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting base blueprint: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- CRUD for LoreEntry ---
def create_lore_entry(
    db_path: str, 
    title: str, 
    content_markdown: Optional[str] = None, 
    category: Optional[str] = None, 
    tags: Optional[str] = None # JSON string
) -> Optional[LoreEntry]:
    logger.info(f"Attempting to create lore entry with title: {title}")
    conn = get_db_connection(db_path)
    if conn is None:
        logger.error("Failed to create database connection.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM lore_entries WHERE title = ?", (title,))
        if cursor.fetchone():
            logger.warning(f"Lore entry with title '{title}' already exists.")
            return None
        
        current_time = get_current_utc_timestamp()
        cursor.execute(
            '''INSERT INTO lore_entries (title, content_markdown, category, tags, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (title, content_markdown, category, tags, current_time, current_time)
        )
        conn.commit()
        entry_id = cursor.lastrowid
        logger.info(f"Lore entry created with ID: {entry_id}, Title: {title}")
        return LoreEntry(id=entry_id, title=title, content_markdown=content_markdown, category=category, tags=tags, created_at=current_time, updated_at=current_time)
    except sqlite3.Error as e:
        logger.error(f"Error creating lore entry: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_lore_entry_by_id(db_path: str, entry_id: int) -> Optional[LoreEntry]:
    logger.debug(f"Fetching lore entry with ID: {entry_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content_markdown, category, tags, created_at, updated_at FROM lore_entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        if row:
            return LoreEntry(id=row[0], title=row[1], content_markdown=row[2], category=row[3], tags=row[4], created_at=row[5], updated_at=row[6])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching lore entry by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_lore_entry_by_title(db_path: str, title: str) -> Optional[LoreEntry]:
    logger.debug(f"Fetching lore entry with title: {title}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content_markdown, category, tags, created_at, updated_at FROM lore_entries WHERE title = ?", (title,))
        row = cursor.fetchone()
        if row:
            return LoreEntry(id=row[0], title=row[1], content_markdown=row[2], category=row[3], tags=row[4], created_at=row[5], updated_at=row[6])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching lore entry by title: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_lore_entries(db_path: str) -> List[LoreEntry]:
    logger.debug("Fetching all lore entries")
    conn = get_db_connection(db_path) 
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content_markdown, category, tags, created_at, updated_at FROM lore_entries")
        rows = cursor.fetchall()
        return [LoreEntry(id=row[0], title=row[1], content_markdown=row[2], category=row[3], tags=row[4], created_at=row[5], updated_at=row[6]) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error fetching all lore entries: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_lore_entry(
    db_path: str, 
    entry_id: int, 
    title: Optional[str] = None,
    content_markdown: Optional[str] = None, 
    category: Optional[str] = None, 
    tags: Optional[str] = None # JSON string
) -> Optional[LoreEntry]:
    logger.info(f"Attempting to update lore entry with ID: {entry_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return None
    
    fields_to_update = []
    params = []

    if title is not None:
        current_entry = get_lore_entry_by_id(db_path, entry_id)
        if current_entry and current_entry.title != title:
            existing_entry = get_lore_entry_by_title(db_path, title)
            if existing_entry:
                logger.warning(f"Cannot update lore entry ID {entry_id}: another entry with title '{title}' already exists (ID: {existing_entry.id}).")
                return None
        fields_to_update.append("title = ?")
        params.append(title)
        
    if content_markdown is not None:
        fields_to_update.append("content_markdown = ?")
        params.append(content_markdown)
    if category is not None:
        fields_to_update.append("category = ?")
        params.append(category)
    if tags is not None:
        fields_to_update.append("tags = ?")
        params.append(tags)

    if not fields_to_update:
        logger.info("No fields provided to update for lore entry.")
        return get_lore_entry_by_id(db_path, entry_id)

    current_time = get_current_utc_timestamp()
    fields_to_update.append("updated_at = ?")
    params.append(current_time)
    params.append(entry_id)

    sql = f"UPDATE lore_entries SET {', '.join(fields_to_update)} WHERE id = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Lore entry with ID {entry_id} not found for update.")
            return None
        logger.info(f"Lore entry with ID {entry_id} updated successfully.")
        return get_lore_entry_by_id(db_path, entry_id)
    except sqlite3.Error as e:
        logger.error(f"Error updating lore entry: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_lore_entry(db_path: str, entry_id: int) -> bool:
    logger.info(f"Attempting to delete lore entry with ID: {entry_id}")
    conn = get_db_connection(db_path) 
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lore_entries WHERE id = ?", (entry_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Lore entry with ID {entry_id} deleted successfully.")
            return True
        logger.warning(f"Lore entry with ID {entry_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting lore entry: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- CRUD for UserSetting ---
def create_user_setting(db_path: str, setting_key: str, setting_value: Optional[str] = None) -> Optional[UserSetting]:
    logger.info(f"Attempting to create user setting with key: {setting_key}")
    conn = get_db_connection(db_path)
    if conn is None:
        logger.error("Failed to create database connection.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_settings WHERE setting_key = ?", (setting_key,))
        if cursor.fetchone():
            logger.warning(f"User setting with key '{setting_key}' already exists.")
            return None
        
        current_time = get_current_utc_timestamp()
        cursor.execute(
            '''INSERT INTO user_settings (setting_key, setting_value, created_at, updated_at)
               VALUES (?, ?, ?, ?)''',
            (setting_key, setting_value, current_time, current_time)
        )
        conn.commit()
        setting_id = cursor.lastrowid
        logger.info(f"User setting created with ID: {setting_id}, Key: {setting_key}")
        return UserSetting(id=setting_id, setting_key=setting_key, setting_value=setting_value, created_at=current_time, updated_at=current_time)
    except sqlite3.Error as e:
        logger.error(f"Error creating user setting: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_setting_by_id(db_path: str, setting_id: int) -> Optional[UserSetting]:
    logger.debug(f"Fetching user setting with ID: {setting_id}")
    conn = get_db_connection(db_path)
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, setting_key, setting_value, created_at, updated_at FROM user_settings WHERE id = ?", (setting_id,))
        row = cursor.fetchone()
        if row:
            return UserSetting(id=row[0], setting_key=row[1], setting_value=row[2], created_at=row[3], updated_at=row[4])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching user setting by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_setting_by_key(db_path: str, setting_key: str) -> Optional[UserSetting]:
    logger.debug(f"Fetching user setting with key: {setting_key}")
    conn = get_db_connection(db_path)
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, setting_key, setting_value, created_at, updated_at FROM user_settings WHERE setting_key = ?", (setting_key,))
        row = cursor.fetchone()
        if row:
            return UserSetting(id=row[0], setting_key=row[1], setting_value=row[2], created_at=row[3], updated_at=row[4])
        return None
    except sqlite3.Error as e:
        logger.error(f"Error fetching user setting by key: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_user_settings(db_path: str) -> List[UserSetting]:
    logger.debug("Fetching all user settings")
    conn = get_db_connection(db_path)
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, setting_key, setting_value, created_at, updated_at FROM user_settings")
        rows = cursor.fetchall()
        return [UserSetting(id=row[0], setting_key=row[1], setting_value=row[2], created_at=row[3], updated_at=row[4]) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error fetching all user settings: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_user_setting(db_path: str, setting_id: int, setting_key: Optional[str] = None, setting_value: Optional[str] = None) -> Optional[UserSetting]:
    logger.info(f"Attempting to update user setting with ID: {setting_id}")
    conn = get_db_connection(db_path)
    if conn is None:
        return None
    
    fields_to_update = []
    params = []

    if setting_key is not None:
        current_setting = get_user_setting_by_id(db_path, setting_id)
        if current_setting and current_setting.setting_key != setting_key:
            existing_setting = get_user_setting_by_key(db_path, setting_key)
            if existing_setting and existing_setting.id != setting_id: # Check if the found key belongs to a different setting
                logger.warning(f"Cannot update user setting ID {setting_id}: another setting with key '{setting_key}' already exists (ID: {existing_setting.id}).")
                return None
        fields_to_update.append("setting_key = ?")
        params.append(setting_key)
        
    # Allow setting_value to be None or an empty string
    if setting_value is not None: 
        fields_to_update.append("setting_value = ?")
        params.append(setting_value)

    if not fields_to_update:
        logger.info("No fields provided to update for user setting.")
        # If only setting_value was passed as None explicitly, and it was the only field, this check is important.
        # However, if the intent is to set a field to NULL, the current logic might need adjustment.
        # For now, if no *other* fields are updated, we return the current state.
        # If setting_value is explicitly set to None and it's the *only* thing, it should be updated.
        # This case is tricky. Let's assume for now that if only setting_value=None is passed, it's an intended update.
        # The current logic: if `params` is empty (no fields to update), it returns current. 
        # If `setting_value` is `None` and it's the only update, `fields_to_update` will contain `setting_value = ?`
        # and `params` will contain `None`. This seems correct.
        existing_setting = get_user_setting_by_id(db_path, setting_id)
        if existing_setting and len(fields_to_update) == 0 : # only if truly no fields were specified for update
             return existing_setting
        # If fields_to_update is not empty, proceed with the update.

    current_time = get_current_utc_timestamp()
    fields_to_update.append("updated_at = ?")
    params.append(current_time)
    params.append(setting_id)

    sql = f"UPDATE user_settings SET {', '.join(fields_to_update)} WHERE id = ?"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            # This could happen if the ID doesn't exist, or if the values provided are the same as existing ones (no actual update by DB)
            # For robustness, we should fetch to confirm. If it doesn't exist, then None is correct.
            # If it exists but wasn't updated because values were same, returning the fetched object is fine.
            logger.warning(f"User setting with ID {setting_id} not found or no changes made during update.")
            # Check if it exists, if not, then it's a true 'not found'
            check_exists = get_user_setting_by_id(db_path, setting_id)
            return check_exists # This will be None if not found, or the object if found (even if not changed by this op)
        logger.info(f"User setting with ID {setting_id} updated successfully.")
        return get_user_setting_by_id(db_path, setting_id)
    except sqlite3.Error as e:
        logger.error(f"Error updating user setting: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_user_setting(db_path: str, setting_id: int) -> bool:
    logger.info(f"Attempting to delete user setting with ID: {setting_id}")
    conn = get_db_connection(db_path)
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_settings WHERE id = ?", (setting_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"User setting with ID {setting_id} deleted successfully.")
            return True
        logger.warning(f"User setting with ID {setting_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting user setting: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- CRUD for UserNote (Placeholder) ---
# ...

# --- CRUD for AIChatHistory (Placeholder) ---
# ...

logger.info("CRUD functions defined.")
