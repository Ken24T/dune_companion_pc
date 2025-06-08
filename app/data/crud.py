import sqlite3
from typing import List, Optional

from app.data.models import Resource, CraftingRecipe, RecipeIngredient, SkillTreeNode # Added SkillTreeNode
from app.data.database import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Helper to convert model to dict for insertion/update, excluding None values and 'id'
def _resource_to_dict(resource: Resource, for_update: bool = False) -> dict:
    data = resource.__dict__.copy()
    data.pop('id', None) # Remove id if present, as it's auto-increment or for WHERE clause
    
    if for_update:
        # For updates, only include fields from `resource` (the update_data object)
        # if their values are different from the default values of a new Resource instance.
        # This prevents unintentionally overwriting fields with their defaults if they
        # weren't explicitly provided in the `Resource(...)` call for `update_data`.
        default_instance = resource.__class__() # Creates a default instance (e.g., Resource())
        update_dict = {}
        for field_name, current_value in data.items():
            # Ensure field_name is a valid field of the dataclass
            if field_name not in resource.__class__.__dataclass_fields__:
                continue

            default_value = getattr(default_instance, field_name)
            if current_value != default_value:
                update_dict[field_name] = current_value
        return update_dict
    else: # For create
        return {k: v for k, v in data.items() if v is not None}

def create_resource(resource: Resource, db_path: Optional[str] = None) -> Optional[int]:
    """Creates a new resource in the database.
    Args:
        resource (Resource): The Resource object to create.
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        Optional[int]: The ID of the newly created resource, or None if creation failed.
    """
    # Use for_update=False for create_resource
    data = _resource_to_dict(resource, for_update=False)
    if not data.get('name'): # Name is a required field
        logger.error("Resource name is required for creation.")
        return None

    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        placeholders = ':' + ', :'.join(data.keys())
        sql = f'INSERT INTO resource ({columns}) VALUES ({placeholders})'
        
        cursor.execute(sql, data)
        conn.commit()
        new_id = cursor.lastrowid
        logger.info(f"Resource '{resource.name}' created with ID: {new_id} in DB: {db_path if db_path else 'default'}")
        return new_id
    except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations (e.g., name)
        logger.error(f"Failed to create resource '{resource.name}' due to integrity error (e.g., duplicate name): {e}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while creating resource '{resource.name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_resource_by_id(resource_id: int, db_path: Optional[str] = None) -> Optional[Resource]:
    """Retrieves a resource by its ID.
    Args:
        resource_id (int): The ID of the resource to retrieve.
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        Optional[Resource]: The Resource object if found, else None.
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resource WHERE id = ?", (resource_id,))
        row = cursor.fetchone()
        if row:
            logger.debug(f"Resource with ID {resource_id} found.")
            return Resource(**dict(row))
        logger.debug(f"Resource with ID {resource_id} not found.")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching resource ID {resource_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_resource_by_name(name: str, db_path: Optional[str] = None) -> Optional[Resource]:
    """Retrieves a resource by its name.
    Args:
        name (str): The name of the resource to retrieve.
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        Optional[Resource]: The Resource object if found, else None.
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resource WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            logger.debug(f"Resource with name '{name}' found.")
            return Resource(**dict(row))
        logger.debug(f"Resource with name '{name}' not found.")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching resource name '{name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_resources(db_path: Optional[str] = None) -> List[Resource]:
    """Retrieves all resources from the database.
    Args:
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        List[Resource]: A list of all Resource objects.
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resource ORDER BY name")
        rows = cursor.fetchall()
        resources = [Resource(**dict(row)) for row in rows]
        logger.debug(f"Retrieved {len(resources)} resources.")
        return resources
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching all resources: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_resource(resource_id: int, update_data: Resource, db_path: Optional[str] = None) -> bool:
    """Updates an existing resource in the database.
    Args:
        resource_id (int): The ID of the resource to update.
        update_data (Resource): A Resource object containing the fields to update.
                                Only non-None fields from this object will be used for update.
                                The `name` field, if provided in `update_data`, will be updated.
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        bool: True if update was successful, False otherwise.
    """
    # Use for_update=True to get a dict of fields explicitly set in update_data
    data_to_update = _resource_to_dict(update_data, for_update=True)
    
    # If name is part of the update_data and is None, this would be an issue if name is required.
    # However, _resource_to_dict with for_update=True will only include non-None fields.
    # So, if update_data.name is None, it won't be in data_to_update.
    # If update_data.name is a string, it will be included.

    if not data_to_update: # No actual fields to update (e.g., Resource() was passed)
        logger.warning(f"No updatable fields provided for resource ID {resource_id}.")
        return False

    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = :{key}" for key in data_to_update.keys()])
        sql = f"UPDATE resource SET {set_clause} WHERE id = :id"
        
        data_to_update['id'] = resource_id # Add id for the WHERE clause
        
        cursor.execute(sql, data_to_update)
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Resource ID {resource_id} updated successfully.")
            return True
        logger.warning(f"Resource ID {resource_id} not found or no changes made during update.")
        return False
    except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations (e.g., name)
        logger.error(f"Failed to update resource ID {resource_id} due to integrity error: {e}")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error while updating resource ID {resource_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_resource(resource_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes a resource from the database by its ID.
    Args:
        resource_id (int): The ID of the resource to delete.
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resource WHERE id = ?", (resource_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Resource ID {resource_id} deleted successfully.")
            return True
        logger.warning(f"Resource ID {resource_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error while deleting resource ID {resource_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

logger.info("CRUD functions for Resource defined.")

# --- CRUD Operations for CraftingRecipe ---

def _crafting_recipe_to_dict(recipe: CraftingRecipe, for_update: bool = False) -> dict:
    data = recipe.__dict__.copy()
    data.pop('id', None)
    data.pop('ingredients', None) # Ingredients are handled separately

    if for_update:
        default_instance = recipe.__class__()
        update_dict = {}
        for field_name, current_value in data.items():
            if field_name not in recipe.__class__.__dataclass_fields__:
                continue
            default_value = getattr(default_instance, field_name)
            if current_value != default_value:
                update_dict[field_name] = current_value
        return update_dict
    else: # For create
        return {k: v for k, v in data.items() if v is not None}

def create_crafting_recipe(recipe: CraftingRecipe, db_path: Optional[str] = None) -> Optional[int]:
    """Creates a new crafting recipe and its ingredients in the database.
    Args:
        recipe (CraftingRecipe): The CraftingRecipe object to create.
        db_path (Optional[str]): Path to the database file for testing.
    Returns:
        Optional[int]: The ID of the newly created recipe, or None if creation failed.
    """
    recipe_data = _crafting_recipe_to_dict(recipe, for_update=False)
    if not recipe_data.get('name') or not recipe_data.get('output_item_name'):
        logger.error("Recipe name and output_item_name are required for creation.")
        return None

    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        conn.execute("BEGIN") # Start transaction

        # Create the main recipe entry
        columns = ', '.join(recipe_data.keys())
        placeholders = ':' + ', :'.join(recipe_data.keys())
        sql_recipe = f'INSERT INTO crafting_recipe ({columns}) VALUES ({placeholders})'
        
        cursor.execute(sql_recipe, recipe_data)
        recipe_id = cursor.lastrowid
        if not recipe_id:
            conn.rollback()
            logger.error(f"Failed to get lastrowid for recipe '{recipe.name}'.")
            return None

        # Create recipe ingredients
        if recipe.ingredients:
            for ingredient_data_model in recipe.ingredients:
                # Ensure ingredient_data_model is a RecipeIngredient instance
                if not isinstance(ingredient_data_model, RecipeIngredient):
                    logger.error(f"Invalid ingredient data for recipe '{recipe.name}'. Expected RecipeIngredient model.")
                    conn.rollback()
                    return None

                # We expect resource_id and quantity to be set on the RecipeIngredient model.
                # The 'recipe_id' is the one we just obtained.
                if ingredient_data_model.resource_id == 0 or ingredient_data_model.quantity == 0:
                     logger.error(f"Invalid ingredient data for recipe '{recipe.name}': resource_id or quantity missing.")
                     conn.rollback()
                     return None

                ingredient_sql_data = {
                    'recipe_id': recipe_id,
                    'resource_id': ingredient_data_model.resource_id,
                    'quantity': ingredient_data_model.quantity
                }
                
                ing_columns = ', '.join(ingredient_sql_data.keys())
                ing_placeholders = ':' + ', :'.join(ingredient_sql_data.keys())
                sql_ingredient = f'INSERT INTO recipe_ingredient ({ing_columns}) VALUES ({ing_placeholders})'
                cursor.execute(sql_ingredient, ingredient_sql_data)
        
        conn.commit() # Commit transaction
        logger.info(f"CraftingRecipe '{recipe.name}' created with ID: {recipe_id} in DB: {db_path if db_path else 'default'}")
        return recipe_id
    except sqlite3.IntegrityError as e:
        if conn: 
            conn.rollback()
        logger.error(f"Failed to create recipe '{recipe.name}' due to integrity error (e.g., duplicate name or FK constraint): {e}")
        return None
    except sqlite3.Error as e:
        if conn: 
            conn.rollback()
        logger.error(f"Database error while creating recipe '{recipe.name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

logger.info("CRUD functions for CraftingRecipe partially defined.")

def get_crafting_recipe_by_id(recipe_id: int, db_path: Optional[str] = None) -> Optional[CraftingRecipe]:
    """Retrieves a crafting recipe by its ID, including its ingredients."""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        # Fetch the main recipe
        cursor.execute("SELECT * FROM crafting_recipe WHERE id = ?", (recipe_id,))
        recipe_row = cursor.fetchone()
        if not recipe_row:
            logger.debug(f"CraftingRecipe with ID {recipe_id} not found.")
            return None

        recipe_dict = dict(recipe_row)
        # Placeholder for ingredients, will be populated next
        recipe_dict['ingredients'] = [] 
        recipe = CraftingRecipe(**recipe_dict)

        # Fetch ingredients for the recipe
        # Joining with resource table to get resource_name for convenience
        cursor.execute("""
            SELECT ri.id, ri.recipe_id, ri.resource_id, ri.quantity, r.name as resource_name
            FROM recipe_ingredient ri
            JOIN resource r ON ri.resource_id = r.id
            WHERE ri.recipe_id = ?
        """, (recipe_id,))
        ingredient_rows = cursor.fetchall()
        
        for ing_row in ingredient_rows:
            recipe.ingredients.append(RecipeIngredient(**dict(ing_row)))
        
        logger.debug(f"CraftingRecipe with ID {recipe_id} and {len(recipe.ingredients)} ingredients found.")
        return recipe
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching recipe ID {recipe_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_crafting_recipe_by_name(name: str, db_path: Optional[str] = None) -> Optional[CraftingRecipe]:
    """Retrieves a crafting recipe by its name, including its ingredients."""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        # Fetch the main recipe by name
        cursor.execute("SELECT * FROM crafting_recipe WHERE name = ?", (name,))
        recipe_row = cursor.fetchone()
        if not recipe_row:
            logger.debug(f"CraftingRecipe with name '{name}' not found.")
            return None

        recipe_dict = dict(recipe_row)
        recipe_id = recipe_dict['id'] # Get ID for fetching ingredients
        recipe_dict['ingredients'] = []
        recipe = CraftingRecipe(**recipe_dict)

        # Fetch ingredients for the recipe
        cursor.execute("""
            SELECT ri.id, ri.recipe_id, ri.resource_id, ri.quantity, r.name as resource_name
            FROM recipe_ingredient ri
            JOIN resource r ON ri.resource_id = r.id
            WHERE ri.recipe_id = ?
        """, (recipe_id,))
        ingredient_rows = cursor.fetchall()
        
        for ing_row in ingredient_rows:
            recipe.ingredients.append(RecipeIngredient(**dict(ing_row)))

        logger.debug(f"CraftingRecipe with name '{name}' and {len(recipe.ingredients)} ingredients found.")
        return recipe
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching recipe name '{name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_crafting_recipes(db_path: Optional[str] = None) -> List[CraftingRecipe]:
    """Retrieves all crafting recipes, including their ingredients."""
    conn = None
    recipes_map = {} # Using a map to efficiently add ingredients to their recipes
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        # Fetch all main recipes
        cursor.execute("SELECT * FROM crafting_recipe ORDER BY name")
        recipe_rows = cursor.fetchall()

        for recipe_row in recipe_rows:
            recipe_dict = dict(recipe_row)
            recipe_id = recipe_dict['id']
            recipe_dict['ingredients'] = []
            recipes_map[recipe_id] = CraftingRecipe(**recipe_dict)

        # Fetch all ingredients and map them to their recipes
        # Ordering by recipe_id can sometimes be beneficial for processing if needed, but not strictly here
        cursor.execute("""
            SELECT ri.id, ri.recipe_id, ri.resource_id, ri.quantity, r.name as resource_name
            FROM recipe_ingredient ri
            JOIN resource r ON ri.resource_id = r.id
            ORDER BY ri.recipe_id
        """)
        ingredient_rows = cursor.fetchall()

        for ing_row_dict in ingredient_rows:
            ing_data = dict(ing_row_dict)
            recipe_id_for_ingredient = ing_data['recipe_id']
            if recipe_id_for_ingredient in recipes_map:
                recipes_map[recipe_id_for_ingredient].ingredients.append(RecipeIngredient(**ing_data))
            else:
                logger.warning(f"Found ingredient for non-fetched or non-existent recipe ID {recipe_id_for_ingredient}. Skipping.")

        final_recipes_list = list(recipes_map.values())
        logger.debug(f"Retrieved {len(final_recipes_list)} crafting recipes.")
        return final_recipes_list
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching all crafting recipes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_crafting_recipe(recipe_id: int, update_data: CraftingRecipe, db_path: Optional[str] = None) -> bool:
    """Updates an existing crafting recipe and its ingredients in the database.

    This function handles updates to the main recipe fields and manages changes
    to its ingredients list by deleting all existing ingredients and then
    inserting the new list of ingredients from update_data.ingredients.

    Args:
        recipe_id (int): The ID of the crafting_recipe to update.
        update_data (CraftingRecipe): A CraftingRecipe object containing the fields to update.
                                    Scalar fields are updated if they differ from defaults.
                                    The `ingredients` list in this object will replace all
                                    existing ingredients for the recipe.
        db_path (Optional[str]): Path to the database file for testing.

    Returns:
        bool: True if update was successful, False otherwise.
    """
    recipe_fields_to_update = _crafting_recipe_to_dict(update_data, for_update=True)
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # First, check if the recipe exists
        cursor.execute("SELECT 1 FROM crafting_recipe WHERE id = ?", (recipe_id,))
        recipe_exists = cursor.fetchone() is not None

        if not recipe_exists:
            logger.warning(f"CraftingRecipe ID {recipe_id} not found. Update failed because recipe does not exist.")
            return False

        conn.execute("BEGIN")  # Start transaction

        if recipe_fields_to_update:
            set_clause = ", ".join([f"{key} = :{key}" for key in recipe_fields_to_update.keys()])
            sql_update_recipe = f"UPDATE crafting_recipe SET {set_clause} WHERE id = :id"
            current_update_data = recipe_fields_to_update.copy()
            current_update_data['id'] = recipe_id
            cursor.execute(sql_update_recipe, current_update_data)

        # Update ingredients: delete existing, then insert new ones
        cursor.execute("DELETE FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
        deleted_ingredients_count = cursor.rowcount
        logger.debug(f"Deleted {deleted_ingredients_count} old ingredients for recipe ID {recipe_id}")

        new_ingredients_inserted_count = 0
        if update_data.ingredients:
            for ingredient_model in update_data.ingredients:
                if not isinstance(ingredient_model, RecipeIngredient) or \
                   ingredient_model.resource_id == 0 or ingredient_model.quantity == 0:
                    logger.error(f"Invalid ingredient data for recipe ID {recipe_id}. Rolling back.")
                    conn.rollback()
                    return False
                
                ingredient_sql_data = {
                    'recipe_id': recipe_id,
                    'resource_id': ingredient_model.resource_id,
                    'quantity': ingredient_model.quantity
                }
                ing_columns = ', '.join(ingredient_sql_data.keys())
                ing_placeholders = ':' + ', :'.join(ingredient_sql_data.keys())
                sql_ingredient = f'INSERT INTO recipe_ingredient ({ing_columns}) VALUES ({ing_placeholders})'
                cursor.execute(sql_ingredient, ingredient_sql_data)
                new_ingredients_inserted_count += 1
        
        # If no actual changes were made to an existing recipe, we might consider it not a "successful update"
        # For now, if the recipe exists, and we attempted operations, consider it a success from a transactional POV.
        # The calling test `test_update_crafting_recipe_non_existent` expects False if ID doesn't exist, which is now handled.
        # If an update makes no effective change to an *existing* record, it currently returns True.
        # This is generally acceptable. The main point is that non-existent IDs should fail early.

        conn.commit()
        logger.info(f"CraftingRecipe ID {recipe_id} processed for update in DB: {db_path if db_path else 'default'}.")
        # The function should return true if the recipe existed and the transaction was successful.
        # Whether actual rows changed for main recipe or ingredients can be a more nuanced success metric,
        # but for this CRUD, existing and committing is success.
        return True

    except sqlite3.IntegrityError as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to update recipe ID {recipe_id} due to integrity error: {e}")
        return False
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error while updating recipe ID {recipe_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_crafting_recipe(recipe_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes a crafting recipe from the database by its ID.
    Associated ingredients are deleted automatically due to ON DELETE CASCADE.

    Args:
        recipe_id (int): The ID of the crafting_recipe to delete.
        db_path (Optional[str]): Path to the database file for testing.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        # The ON DELETE CASCADE on recipe_ingredient.recipe_id will handle deleting ingredients.
        cursor.execute("DELETE FROM crafting_recipe WHERE id = ?", (recipe_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"CraftingRecipe ID {recipe_id} and its ingredients deleted successfully.")
            return True
        logger.warning(f"CraftingRecipe ID {recipe_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error while deleting recipe ID {recipe_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

logger.info("CRUD functions for CraftingRecipe defined.")

# --- CRUD Operations for SkillTreeNode ---

def _skill_tree_node_to_dict(node: SkillTreeNode, for_update: bool = False) -> dict:
    data = node.__dict__.copy()
    data.pop('id', None)

    if for_update:
        default_instance = node.__class__()
        update_dict = {}
        for field_name, current_value in data.items():
            if field_name not in node.__class__.__dataclass_fields__:
                continue
            default_value = getattr(default_instance, field_name)
            if current_value != default_value:
                update_dict[field_name] = current_value
        return update_dict
    else: # For create
        return {k: v for k, v in data.items() if v is not None}

def create_skill_tree_node(node: SkillTreeNode, db_path: Optional[str] = None) -> Optional[int]:
    """Creates a new skill tree node in the database."""
    data = _skill_tree_node_to_dict(node, for_update=False)
    if not data.get('name'):
        logger.error("SkillTreeNode name is required for creation.")
        return None

    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        placeholders = ':' + ', :'.join(data.keys())
        sql = f'INSERT INTO skill_tree_node ({columns}) VALUES ({placeholders})'
        
        cursor.execute(sql, data)
        conn.commit()
        new_id = cursor.lastrowid
        logger.info(f"SkillTreeNode '{node.name}' created with ID: {new_id} in DB: {db_path if db_path else 'default'}")
        return new_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Failed to create SkillTreeNode '{node.name}' due to integrity error (e.g., duplicate name or FK constraint): {e}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while creating SkillTreeNode '{node.name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_skill_tree_node_by_id(node_id: int, db_path: Optional[str] = None) -> Optional[SkillTreeNode]:
    """Retrieves a skill tree node by its ID."""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skill_tree_node WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        if row:
            logger.debug(f"SkillTreeNode with ID {node_id} found.")
            return SkillTreeNode(**dict(row))
        logger.debug(f"SkillTreeNode with ID {node_id} not found.")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching SkillTreeNode ID {node_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_skill_tree_node_by_name(name: str, db_path: Optional[str] = None) -> Optional[SkillTreeNode]:
    """Retrieves a skill tree node by its name."""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        # Assuming name is unique for SkillTreeNode as well, or this might need adjustment
        cursor.execute("SELECT * FROM skill_tree_node WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            logger.debug(f"SkillTreeNode with name '{name}' found.")
            return SkillTreeNode(**dict(row))
        logger.debug(f"SkillTreeNode with name '{name}' not found.")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching SkillTreeNode name '{name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_skill_tree_nodes(db_path: Optional[str] = None) -> List[SkillTreeNode]:
    """Retrieves all skill tree nodes from the database."""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skill_tree_node ORDER BY skill_tree_name, name") # Order by tree then name
        rows = cursor.fetchall()
        nodes = [SkillTreeNode(**dict(row)) for row in rows]
        logger.debug(f"Retrieved {len(nodes)} skill tree nodes.")
        return nodes
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching all skill tree nodes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_skill_tree_node(node_id: int, update_data: SkillTreeNode, db_path: Optional[str] = None) -> bool:
    """Updates an existing skill tree node."""
    data_to_update = _skill_tree_node_to_dict(update_data, for_update=True)

    if not data_to_update:
        logger.warning(f"No updatable fields provided for SkillTreeNode ID {node_id}.")
        return False

    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = :{key}" for key in data_to_update.keys()])
        sql = f"UPDATE skill_tree_node SET {set_clause} WHERE id = :id"
        
        data_to_update['id'] = node_id
        
        cursor.execute(sql, data_to_update)
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"SkillTreeNode ID {node_id} updated successfully.")
            return True
        logger.warning(f"SkillTreeNode ID {node_id} not found or no changes made during update.")
        return False
    except sqlite3.IntegrityError as e:
        logger.error(f"Failed to update SkillTreeNode ID {node_id} due to integrity error: {e}")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error while updating SkillTreeNode ID {node_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_skill_tree_node(node_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes a skill tree node by its ID."""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        # Consider implications if other tables reference skill_tree_node via parent_node_id
        # For now, direct delete. If parent_node_id has FK constraint with SET NULL or CASCADE, it will be handled.
        # If it's a simple integer and other nodes point to it, they might become orphaned if not handled.
        # The schema has ON DELETE SET NULL for parent_node_id, so this is fine.
        cursor.execute("DELETE FROM skill_tree_node WHERE id = ?", (node_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"SkillTreeNode ID {node_id} deleted successfully.")
            return True
        logger.warning(f"SkillTreeNode ID {node_id} not found for deletion.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error while deleting SkillTreeNode ID {node_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

logger.info("CRUD functions for SkillTreeNode defined.")
