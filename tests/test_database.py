import pytest
import os
import time
import gc # Add import for garbage collection
from typing import Optional, List
from app.data.database import initialize_database, get_db_connection
from app.data.models import (
    Resource, CraftingRecipe, RecipeIngredient #, UserNote, AIChatHistory
    # SkillTreeNode, BaseBlueprint, LoreEntry, UserSetting # Removed due to no active tests for them
)
from app.data.crud import (
    create_resource, get_resource_by_id, get_resource_by_name, get_all_resources, update_resource, delete_resource,
    create_crafting_recipe, get_crafting_recipe_by_id, get_crafting_recipe_by_name, get_all_crafting_recipes, update_crafting_recipe, delete_crafting_recipe, # CraftingRecipe CRUDs
    # create_skill_tree_node, get_skill_tree_node_by_id, get_skill_tree_node_by_name, get_all_skill_tree_nodes, update_skill_tree_node, delete_skill_tree_node, # Comment out SkillTreeNode CRUDs
    # BaseBlueprint, LoreEntry, UserSetting CRUDs removed as their tests are not currently active.
)
from app.utils.logger import shutdown_logging, get_logger # Added get_logger
from datetime import datetime, timezone # Added timezone

logger = get_logger(__name__) # Initialize logger for test file

# Helper function to parse SQLite timestamps that may have 3-digit fractional seconds
def parse_sqlite_timestamp(ts_str: str) -> datetime:
    """Parse SQLite timestamp string to UTC datetime object.
    
    SQLite's %f produces 3-digit fractional seconds, while Python's %f expects 6-digit microseconds.
    This function handles the conversion properly.
    """
    # Database uses space format: '%Y-%m-%d %H:%M:%S.%f'
    timestamp_format = '%Y-%m-%d %H:%M:%S.%f'
    
    try:
        return datetime.strptime(ts_str, timestamp_format).replace(tzinfo=timezone.utc)
    except ValueError:
        # If parsing fails, try to handle the fractional seconds differently
        if '.' in ts_str:
            base_time, fractional = ts_str.rsplit('.', 1)
            # Pad fractional seconds to 6 digits for microseconds
            fractional_padded = fractional.ljust(6, '0')[:6]
            adjusted_ts = f"{base_time}.{fractional_padded}"
            return datetime.strptime(adjusted_ts, timestamp_format).replace(tzinfo=timezone.utc)
        else:
            # No fractional seconds
            return datetime.strptime(ts_str, timestamp_format.replace('.%f', '')).replace(tzinfo=timezone.utc)

# Define a test-specific database path
TEST_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
TEST_DB_NAME = 'test_dune_companion.db'
TEST_DB_PATH = os.path.join(TEST_DB_DIR, TEST_DB_NAME)

@pytest.fixture(scope="session", autouse=True)
def manage_test_log_file_usage():
    # This fixture will run once per session
    yield
    # After all tests in the session, shutdown logging to release file handles
    # This is important if tests create/delete log files rapidly
    shutdown_logging()

@pytest.fixture(scope="function") # Changed to function scope for cleaner tests
def test_db():
    """Fixture to set up and tear down an in-memory SQLite database for testing."""
    # Ensure the test database directory exists if not using :memory:
    # For this example, we will use a file-based test DB to also test path handling.
    os.makedirs(TEST_DB_DIR, exist_ok=True)
    
    # Ensure the database file is removed before initialization for a clean state
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError as e:
            logger.error(f"Critical: Could not remove existing test database file {TEST_DB_PATH} before test setup: {e}")
            # Try garbage collection and a small delay if initial removal fails in setup
            gc.collect()
            time.sleep(0.1)
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError as e_retry:
                logger.error(f"Critical: Still could not remove {TEST_DB_PATH} after retry in setup: {e_retry}")
                raise # Fail fast if setup cannot ensure a clean environment
    
    # Initialize a fresh database for each test function
    initialize_database(db_path=TEST_DB_PATH)
    
    yield TEST_DB_PATH # Provide the path to the test database

    # Teardown: close connections and remove the test database file
    # Force garbage collection to help release file handles that might be lingering
    gc.collect()
    
    # Attempt to remove the test database file with retries
    if os.path.exists(TEST_DB_PATH):
        for i in range(5):  # Try up to 5 times
            try:
                os.remove(TEST_DB_PATH)
                logger.info(f"Successfully removed test database {TEST_DB_PATH} on attempt {i + 1} during teardown.")
                break  # Exit loop if successful
            except PermissionError as e:
                logger.warning(f"Attempt {i + 1} to remove {TEST_DB_PATH} during teardown failed: {e}")
                if i < 4:  # If not the last attempt
                    gc.collect() # Try collecting again before sleep
                    time.sleep(0.2 * (i + 1))  # Wait a bit longer each time before retrying
                else:  # Last attempt failed
                    logger.error(f"Failed to remove test database {TEST_DB_PATH} after multiple attempts during teardown: {e}")
                    # Depending on strictness, you might want to raise an error here or ensure CI flags this.
            except Exception as e: # Catch other potential errors during removal
                logger.error(f"An unexpected error occurred while trying to remove {TEST_DB_PATH} during teardown: {e}")
                break # Stop trying if it's not a PermissionError
        else: # Executed if the loop completes without a break (i.e., all retries failed)
            logger.error(f"Loop completed: Failed to remove test database {TEST_DB_PATH} after all retries during teardown.")

    # Attempt to remove the test database directory if it's empty
    if os.path.exists(TEST_DB_DIR) and not os.listdir(TEST_DB_DIR):
        try:
            os.rmdir(TEST_DB_DIR)
            logger.info(f"Successfully removed test database directory {TEST_DB_DIR} during teardown.")
        except OSError as e: # Catches PermissionError and other OS-related errors like "directory not empty"
            logger.warning(f"Could not remove test database directory {TEST_DB_DIR} during teardown: {e}")
    elif os.path.exists(TEST_DB_DIR):
        # This case means the directory still contains files (e.g., the DB file if removal failed, or other unexpected files)
        logger.warning(f"Test database directory {TEST_DB_DIR} was not removed during teardown because it is not empty.")

def test_database_initialization(test_db):
    """Test that the database initializes correctly and tables are created."""
    conn = None
    try:
        conn = get_db_connection(db_path=test_db)
        cursor = conn.cursor()

        # Check if tables exist
        tables_to_check = [
            'resource', 'crafting_recipe', 'skill_tree_node', 'base_blueprint',
            'lore_entry', 'user_setting', 'user_note', 'ai_chat_history', 'recipe_ingredient'
        ]
        for table_name in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            assert cursor.fetchone() is not None, f"Table '{table_name}' should exist after initialization."
        
        # Check if triggers exist
        triggers_to_check = [
            'update_resource_updated_at', 'update_crafting_recipe_updated_at', 
            'update_skill_tree_node_updated_at', 'update_base_blueprint_updated_at',
            'update_lore_entry_updated_at', 'update_user_setting_updated_at',
            'update_user_note_updated_at'
        ]
        for trigger_name in triggers_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='trigger' AND name='{trigger_name}';")
            assert cursor.fetchone() is not None, f"Trigger '{trigger_name}' should exist after initialization."

    finally:
        if conn:
            conn.close()

# --- CRUD Tests for Resource ---

def test_create_resource(test_db):
    """Test creating a new resource."""
    created_resource: Optional[Resource] = create_resource(
        db_path=test_db, 
        name="Spice", 
        description="The spice must flow.", 
        rarity="Legendary", 
        category="Consumable"
    )
    
    assert created_resource is not None
    assert created_resource.id is not None
    
    retrieved_resource: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=created_resource.id)
    assert retrieved_resource is not None
    assert retrieved_resource.name == "Spice"
    assert retrieved_resource.description == "The spice must flow."
    assert retrieved_resource.rarity == "Legendary"
    assert retrieved_resource.category == "Consumable"
    assert retrieved_resource.discovered == 0 # Default value

def test_create_resource_missing_name(test_db):
    """Test creating a resource with a missing name (should fail at DB or validation layer)."""
    # create_resource now requires name as a positional argument.
    # Calling it without 'name' will raise a TypeError.
    with pytest.raises(TypeError): # This will catch the TypeError from missing 'name'
        create_resource(db_path=test_db, description="A resource without a name.") # type: ignore


def test_create_resource_duplicate_name(test_db):
    """Test creating a resource with a duplicate name (should fail)."""
    res1: Optional[Resource] = create_resource(db_path=test_db, name="Water", description="H2O")
    assert res1 is not None
    
    res2: Optional[Resource] = create_resource(db_path=test_db, name="Water", description="Still H2O")
    assert res2 is None, "Creating a resource with a duplicate name should return None."

def test_get_resource_by_id(test_db):
    """Test retrieving a resource by its ID."""
    created_resource: Optional[Resource] = create_resource(db_path=test_db, name="Iron Ore", category="Mineral")
    assert created_resource is not None
    assert created_resource.id is not None

    retrieved_resource: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=created_resource.id)
    assert retrieved_resource is not None
    assert retrieved_resource.id == created_resource.id
    assert retrieved_resource.name == "Iron Ore"

def test_get_resource_by_id_non_existent(test_db):
    """Test retrieving a non-existent resource by ID."""
    retrieved_resource: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=9999) # Assuming 9999 does not exist
    assert retrieved_resource is None

def test_get_resource_by_name_simple(test_db):
    """Test retrieving a resource by its name."""
    created_resource: Optional[Resource] = create_resource(db_path=test_db, name="Crystal", category="Gemstone")
    assert created_resource is not None

    retrieved_resource: Optional[Resource] = get_resource_by_name(db_path=test_db, name="Crystal")
    assert retrieved_resource is not None
    assert retrieved_resource.name == "Crystal"


def test_get_all_resources_unique(test_db):
    """Test retrieving all resources (unique test function to avoid name conflict)."""
    resource_data_list = [
        {"name":"Sandworm Tooth", "category":"Monster Part"},
        {"name":"Thumper", "category":"Tool"},
        {"name":"Ornithopter Fuel", "category":"Fuel"}
    ]
    for res_data in resource_data_list:
        created: Optional[Resource] = create_resource(db_path=test_db, name=res_data["name"], category=res_data["category"])
        assert created is not None

    all_resources: List[Resource] = get_all_resources(db_path=test_db)
    assert len(all_resources) == len(resource_data_list)
    
    retrieved_names = sorted([res.name for res in all_resources])
    expected_names = sorted([res_data["name"] for res_data in resource_data_list])
    assert retrieved_names == expected_names

def test_update_resource_fields(test_db):
    """Test updating an existing resource."""
    created_resource: Optional[Resource] = create_resource(
        db_path=test_db, 
        name="Solari", 
        description="Currency of the Imperium", 
        category="Currency"
    )
    assert created_resource is not None
    assert created_resource.id is not None
    resource_id: int = created_resource.id

    time.sleep(0.05) # Ensure timestamp difference for updated_at check

    updated_resource_obj: Optional[Resource] = update_resource(
        db_path=test_db, 
        resource_id=resource_id, 
        description="The official currency of the Imperium and CHOAM.", 
        rarity="Common", 
        discovered=1
    )
    assert updated_resource_obj is not None

    fetched_updated_resource: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=resource_id)
    assert fetched_updated_resource is not None
    assert fetched_updated_resource.name == "Solari" # Name should not change
    assert fetched_updated_resource.description == "The official currency of the Imperium and CHOAM."
    assert fetched_updated_resource.rarity == "Common"
    assert fetched_updated_resource.discovered == 1
    assert fetched_updated_resource.created_at is not None
    assert fetched_updated_resource.updated_at is not None
    
    # Convert timestamp strings to offset-aware UTC datetime objects
    # Use helper function to parse SQLite timestamps
    created_at_dt = parse_sqlite_timestamp(fetched_updated_resource.created_at)
    updated_at_dt = parse_sqlite_timestamp(fetched_updated_resource.updated_at)
    assert updated_at_dt > created_at_dt, "updated_at should be greater than created_at after update"

def test_get_resource_by_name(test_db):
    """Test retrieving a resource by its name."""
    created_resource: Optional[Resource] = create_resource(db_path=test_db, name="Crystal", category="Gemstone")
    assert created_resource is not None

    retrieved_resource: Optional[Resource] = get_resource_by_name(db_path=test_db, name="Crystal")
    assert retrieved_resource is not None
    assert retrieved_resource.name == "Crystal"

def test_get_resource_by_name_non_existent(test_db):
    """Test retrieving a non-existent resource by name."""
    retrieved_resource: Optional[Resource] = get_resource_by_name(db_path=test_db, name="Unobtanium")
    assert retrieved_resource is None

def test_get_all_resources(test_db):
    """Test retrieving all resources."""
    resource_data_list = [
        {"name":"Sandworm Tooth", "category":"Monster Part"},
        {"name":"Thumper", "category":"Tool"},
        {"name":"Ornithopter Fuel", "category":"Fuel"}
    ]
    for res_data in resource_data_list:
        created: Optional[Resource] = create_resource(db_path=test_db, name=res_data["name"], category=res_data["category"])
        assert created is not None

    all_resources: List[Resource] = get_all_resources(db_path=test_db)
    assert len(all_resources) == len(resource_data_list)
    
    retrieved_names = sorted([res.name for res in all_resources])
    expected_names = sorted([res_data["name"] for res_data in resource_data_list])
    assert retrieved_names == expected_names

def test_update_resource(test_db):
    """Test updating an existing resource."""
    created_resource: Optional[Resource] = create_resource(
        db_path=test_db, 
        name="Solari", 
        description="Currency of the Imperium", 
        category="Currency"
    )
    assert created_resource is not None
    assert created_resource.id is not None
    resource_id: int = created_resource.id

    time.sleep(0.05) # Ensure timestamp difference for updated_at check

    updated_resource_obj: Optional[Resource] = update_resource(
        db_path=test_db, 
        resource_id=resource_id, 
        description="The official currency of the Imperium and CHOAM.", 
        rarity="Common", 
        discovered=1
    )
    assert updated_resource_obj is not None

    fetched_updated_resource: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=resource_id)
    assert fetched_updated_resource is not None
    assert fetched_updated_resource.name == "Solari" # Name should not change
    assert fetched_updated_resource.description == "The official currency of the Imperium and CHOAM."
    assert fetched_updated_resource.rarity == "Common"
    assert fetched_updated_resource.discovered == 1
    assert fetched_updated_resource.created_at is not None
    assert fetched_updated_resource.updated_at is not None
    
    # Convert timestamp strings to offset-aware UTC datetime objects
    # Ensure the format string matches the one used in database.py
    created_at_dt = parse_sqlite_timestamp(fetched_updated_resource.created_at)
    updated_at_dt = parse_sqlite_timestamp(fetched_updated_resource.updated_at)
    assert updated_at_dt > created_at_dt, "updated_at should be greater than created_at after update"

def test_update_resource_change_name_duplicate(test_db):
    """Test updating a resource name to an existing name (should fail)."""
    res1: Optional[Resource] = create_resource(db_path=test_db, name="ResourceA")
    assert res1 is not None and res1.id is not None
    res1_id: int = res1.id
    
    res2: Optional[Resource] = create_resource(db_path=test_db, name="ResourceB")
    assert res2 is not None

    # Try to change ResourceA's name to ResourceB
    updated_res: Optional[Resource] = update_resource(db_path=test_db, resource_id=res1_id, name="ResourceB")
    assert updated_res is None, "Updating name to an existing one should return None."
    
    original_res1: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=res1_id)
    assert original_res1 is not None
    assert original_res1.name == "ResourceA"

def test_update_resource_non_existent(test_db):
    """Test updating a non-existent resource."""
    updated_res: Optional[Resource] = update_resource(db_path=test_db, resource_id=8888, name="NonExistentUpdated") # Assuming 8888 does not exist
    assert updated_res is None

def test_delete_resource(test_db):
    """Test deleting a resource."""
    created_resource: Optional[Resource] = create_resource(db_path=test_db, name="Kindjal", category="Weapon")
    assert created_resource is not None
    assert created_resource.id is not None
    resource_id: int = created_resource.id
    
    assert get_resource_by_id(db_path=test_db, resource_id=resource_id) is not None # Verify it exists

    success: bool = delete_resource(db_path=test_db, resource_id=resource_id)
    assert success is True
    assert get_resource_by_id(db_path=test_db, resource_id=resource_id) is None # Verify it's deleted

def test_delete_resource_non_existent(test_db):
    """Test deleting a non-existent resource."""
    success: bool = delete_resource(db_path=test_db, resource_id=7777) # Assuming 7777 does not exist
    assert success is False

def test_resource_updated_at_trigger(test_db):
    """Test that the updated_at field is automatically updated by the trigger."""
    resource_name = "TestTriggerResource"
    resource_description = "Initial Description"
    resource_category = "TestCategory"
    resource_rarity = "Common"

    created_resource_obj: Optional[Resource] = create_resource(
        db_path=test_db,
        name=resource_name,
        description=resource_description,
        category=resource_category,
        rarity=resource_rarity
    )
    assert created_resource_obj is not None, "Resource creation failed"
    assert created_resource_obj.id is not None, "Resource ID is None after creation"
    resource_id: int = created_resource_obj.id

    initial_resource: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=resource_id)
    assert initial_resource is not None, "Failed to retrieve initial resource"
    assert initial_resource.created_at is not None, "Initial resource created_at is None"
    assert initial_resource.updated_at is not None, "Initial resource updated_at is not None" 
    initial_created_at_dt = parse_sqlite_timestamp(initial_resource.created_at)
    initial_updated_at_dt = parse_sqlite_timestamp(initial_resource.updated_at)
    assert abs(initial_created_at_dt.timestamp() - initial_updated_at_dt.timestamp()) < 0.1 # Should be very close

    time.sleep(0.05) # Ensure timestamp difference

    update_success_obj: Optional[Resource] = update_resource(
        db_path=test_db,
        resource_id=resource_id,
        description="Updated Description for Trigger Test",
        rarity="Rare" # Change another field
    )
    assert update_success_obj is not None, "Resource update failed in trigger test"

    updated_resource_db: Optional[Resource] = get_resource_by_id(db_path=test_db, resource_id=resource_id)
    assert updated_resource_db is not None, "Failed to retrieve updated resource in trigger test"
    assert updated_resource_db.created_at is not None and updated_resource_db.updated_at is not None

    final_created_at_dt = parse_sqlite_timestamp(updated_resource_db.created_at)
    final_updated_at_dt = parse_sqlite_timestamp(updated_resource_db.updated_at)

    assert final_created_at_dt == initial_created_at_dt, "created_at should not change on update"
    assert final_updated_at_dt > initial_updated_at_dt, "updated_at should be greater than initial updated_at after update"

# --- Fixture for CraftingRecipe tests ---
@pytest.fixture(scope="function")
def setup_common_resources_for_recipes(test_db):
    """Set up some common resources needed for recipe tests.
    Creates them if they don't exist, or fetches them if they do.
    """
    logger.info("Setting up common resources for recipe tests...")
    resources_to_create_and_fetch = [
        {"name": "Iron Ingot", "category": "Material", "key": "iron_ingot"},
        {"name": "Copper Wire", "category": "Component", "key": "copper_wire"},
        {"name": "Plastic Casing", "category": "Component", "key": "plastic_casing"},
    ]
    
    created_or_fetched_resources = {}
    
    for res_data in resources_to_create_and_fetch:
        resource = create_resource(db_path=test_db, name=res_data["name"], category=res_data["category"])
        if resource is None: 
            logger.warning(f"Resource '{res_data['name']}' creation returned None (likely exists), attempting to fetch.")
            resource = get_resource_by_name(db_path=test_db, name=res_data["name"])
        
        if resource is None:
            # This case should ideally not be hit if the DB is clean or the item truly exists.
            # Logging an error here helps diagnose if there's a deeper issue.
            logger.error(f"Critical error: Failed to create AND fetch resource: {res_data['name']}. DB state is unexpected.")

        assert resource is not None, f"Failed to create or fetch resource: {res_data['name']}"
        assert resource.id is not None, f"Resource '{res_data['name']}' has no ID after creation/fetching."
        created_or_fetched_resources[res_data["key"]] = resource
        logger.info(f"Ensured resource '{res_data['name']}' (ID: {resource.id}) is available for the test.")
            
    return created_or_fetched_resources

# --- CRUD Tests for CraftingRecipe ---
class TestCraftingRecipeCRUD: # Group tests in a class

    def test_create_crafting_recipe(self, test_db, setup_common_resources_for_recipes):
        """Test creating a new crafting recipe with ingredients."""
        resources = setup_common_resources_for_recipes
        assert resources["iron_ingot"].id is not None # Ensure IDs are not None
        assert resources["copper_wire"].id is not None

        created_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db,
            name="Basic Gadget",
            description="A simple electronic gadget.",
            output_item_name="Gadget Alpha",
            output_quantity=1,
            ingredients=[
                RecipeIngredient(resource_id=resources["iron_ingot"].id, quantity=2), 
                RecipeIngredient(resource_id=resources["copper_wire"].id, quantity=5)
            ]
        )
        assert created_recipe is not None
        assert created_recipe.id is not None

        retrieved_recipe: Optional[CraftingRecipe] = get_crafting_recipe_by_id(db_path=test_db, recipe_id=created_recipe.id)
        assert retrieved_recipe is not None
        assert retrieved_recipe.name == "Basic Gadget"
        assert retrieved_recipe.output_item_name == "Gadget Alpha"
        assert len(retrieved_recipe.ingredients) == 2
        
        ing_iron = next((ing for ing in retrieved_recipe.ingredients if ing.resource_id == resources["iron_ingot"].id), None)
        ing_copper = next((ing for ing in retrieved_recipe.ingredients if ing.resource_id == resources["copper_wire"].id), None)
        
        assert ing_iron is not None
        assert ing_iron.quantity == 2
        assert ing_iron.resource_name == "Iron Ingot"

        assert ing_copper is not None
        assert ing_copper.quantity == 5
        assert ing_copper.resource_name == "Copper Wire"

    def test_create_crafting_recipe_no_ingredients(self, test_db):
        """Test creating a recipe without any ingredients."""
        created_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db, 
            name="Empty Recipe", 
            output_item_name="Nothing"
        )
        assert created_recipe is not None
        assert created_recipe.id is not None
        retrieved: Optional[CraftingRecipe] = get_crafting_recipe_by_id(db_path=test_db, recipe_id=created_recipe.id)
        assert retrieved is not None
        assert retrieved.name == "Empty Recipe"
        assert len(retrieved.ingredients) == 0

    def test_create_crafting_recipe_missing_mandatory_fields(self, test_db):
        """Test creating a recipe with missing mandatory fields (should fail)."""
        # Missing name
        with pytest.raises(TypeError): # Name is a required positional arg
            create_crafting_recipe(db_path=test_db, output_item_name="Nameless Output") # type: ignore
    
        # Missing output_item_name
        with pytest.raises(TypeError): # output_item_name is a required positional arg
            create_crafting_recipe(db_path=test_db, name="Recipe With No Output Name") # type: ignore

    def test_create_crafting_recipe_duplicate_name(self, test_db):
        """Test creating a recipe with a duplicate name (should fail)."""
        recipe1: Optional[CraftingRecipe] = create_crafting_recipe(db_path=test_db, name="Unique Recipe", output_item_name="Output1")
        assert recipe1 is not None
        recipe2: Optional[CraftingRecipe] = create_crafting_recipe(db_path=test_db, name="Unique Recipe", output_item_name="Output2")
        assert recipe2 is None

    def test_get_crafting_recipe_by_id(self, test_db, setup_common_resources_for_recipes):
        """Test retrieving a recipe by ID."""
        resources = setup_common_resources_for_recipes
        assert resources["plastic_casing"].id is not None

        created_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db,
            name="Advanced Gadget",
            output_item_name="Gadget Beta",
            ingredients=[RecipeIngredient(resource_id=resources["plastic_casing"].id, quantity=1)]
        )
        assert created_recipe is not None
        assert created_recipe.id is not None

        retrieved: Optional[CraftingRecipe] = get_crafting_recipe_by_id(db_path=test_db, recipe_id=created_recipe.id)
        assert retrieved is not None
        assert retrieved.id == created_recipe.id
        assert retrieved.name == "Advanced Gadget"
        assert len(retrieved.ingredients) == 1
        assert retrieved.ingredients[0].resource_id == resources["plastic_casing"].id
        assert retrieved.ingredients[0].resource_name == "Plastic Casing"

    def test_get_crafting_recipe_by_id_non_existent(self, test_db):
        """Test retrieving non-existent recipe by ID."""
        retrieved: Optional[CraftingRecipe] = get_crafting_recipe_by_id(db_path=test_db, recipe_id=999)
        assert retrieved is None

    def test_get_crafting_recipe_by_name(self, test_db, setup_common_resources_for_recipes):
        """Test retrieving a recipe by its name."""
        resources = setup_common_resources_for_recipes
        assert resources["iron_ingot"].id is not None

        created_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db,
            name="Searchable Recipe", 
            output_item_name="Searchable Output",
            ingredients=[RecipeIngredient(resource_id=resources["iron_ingot"].id, quantity=3)]
        )
        assert created_recipe is not None

        retrieved: Optional[CraftingRecipe] = get_crafting_recipe_by_name(db_path=test_db, name="Searchable Recipe")
        assert retrieved is not None
        assert retrieved.name == "Searchable Recipe"
        assert len(retrieved.ingredients) == 1
        assert retrieved.ingredients[0].resource_id == resources["iron_ingot"].id
        assert retrieved.ingredients[0].resource_name == "Iron Ingot"

    def test_get_crafting_recipe_by_name_non_existent(self, test_db):
        """Test retrieving non-existent recipe by name."""
        retrieved: Optional[CraftingRecipe] = get_crafting_recipe_by_name(db_path=test_db, name="Imaginary Recipe")
        assert retrieved is None

    def test_get_all_crafting_recipes(self, test_db, setup_common_resources_for_recipes):
        """Test retrieving all crafting recipes."""
        resources = setup_common_resources_for_recipes
        assert resources["iron_ingot"].id is not None
        assert resources["copper_wire"].id is not None

        create_crafting_recipe(db_path=test_db, name="Recipe A", output_item_name="Item A", ingredients=[
            RecipeIngredient(resource_id=resources["iron_ingot"].id, quantity=1)
        ])
        create_crafting_recipe(db_path=test_db, name="Recipe B", output_item_name="Item B", ingredients=[
            RecipeIngredient(resource_id=resources["copper_wire"].id, quantity=2)
        ])

        all_recipes: List[CraftingRecipe] = get_all_crafting_recipes(db_path=test_db)
        assert len(all_recipes) == 2
        recipe_names = sorted([r.name for r in all_recipes])
        assert recipe_names == ["Recipe A", "Recipe B"]

        # Check ingredients are populated for one of them
        recipe_a = next((r for r in all_recipes if r.name == "Recipe A"), None)
        assert recipe_a is not None
        assert len(recipe_a.ingredients) == 1
        assert recipe_a.ingredients[0].resource_id == resources["iron_ingot"].id
        assert recipe_a.ingredients[0].resource_name == "Iron Ingot"

    def test_update_crafting_recipe_fields_and_ingredients(self, test_db, setup_common_resources_for_recipes):
        """Test updating recipe fields and its ingredients list."""
        resources = setup_common_resources_for_recipes
        assert resources["iron_ingot"].id is not None
        assert resources["copper_wire"].id is not None
        assert resources["plastic_casing"].id is not None

        created_initial_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db,
            name="Updatable Gadget",
            description="Version 1.0",
            output_item_name="UG-1",
            output_quantity=1,
            ingredients=[
                RecipeIngredient(resource_id=resources["iron_ingot"].id, quantity=1)
            ]
        )
        assert created_initial_recipe is not None and created_initial_recipe.id is not None
        recipe_id: int = created_initial_recipe.id
        
        time.sleep(0.05) # Ensure timestamp difference

        updated_recipe_obj: Optional[CraftingRecipe] = update_crafting_recipe(
            db_path=test_db, 
            recipe_id=recipe_id,
            description="Version 2.0 with more features", 
            output_quantity=2, 
            ingredients=[
                RecipeIngredient(resource_id=resources["copper_wire"].id, quantity=10),
                RecipeIngredient(resource_id=resources["plastic_casing"].id, quantity=3)
            ]
        )
        assert updated_recipe_obj is not None

        fetched_updated_recipe = get_crafting_recipe_by_id(db_path=test_db, recipe_id=recipe_id)
        assert fetched_updated_recipe is not None
        assert fetched_updated_recipe.name == "Updatable Gadget" 
        assert fetched_updated_recipe.description == "Version 2.0 with more features"
        assert fetched_updated_recipe.output_item_name == "UG-1" 
        assert fetched_updated_recipe.output_quantity == 2
        assert len(fetched_updated_recipe.ingredients) == 2

        ing_copper = next((ing for ing in fetched_updated_recipe.ingredients if ing.resource_id == resources["copper_wire"].id), None)
        ing_plastic = next((ing for ing in fetched_updated_recipe.ingredients if ing.resource_id == resources["plastic_casing"].id), None)

        assert ing_copper is not None and ing_copper.quantity == 10 and ing_copper.resource_name == "Copper Wire"
        assert ing_plastic is not None and ing_plastic.quantity == 3 and ing_plastic.resource_name == "Plastic Casing"
        assert fetched_updated_recipe.created_at is not None and fetched_updated_recipe.updated_at is not None
        # Ensure the format string matches the one used in database.py
        created_at_dt = parse_sqlite_timestamp(fetched_updated_recipe.created_at)
        updated_at_dt = parse_sqlite_timestamp(fetched_updated_recipe.updated_at)
        assert updated_at_dt > created_at_dt

    def test_delete_crafting_recipe_and_ingredients(self, test_db, setup_common_resources_for_recipes):
        """Test deleting a crafting recipe and its ingredients (via CASCADE)."""
        resources = setup_common_resources_for_recipes
        assert resources["copper_wire"].id is not None

        created_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db,
            name="To Be Deleted", 
            output_item_name="TBD-1",
            ingredients=[RecipeIngredient(resource_id=resources["copper_wire"].id, quantity=3)]
        )
        assert created_recipe is not None and created_recipe.id is not None
        recipe_id: int = created_recipe.id
        
        assert get_crafting_recipe_by_id(db_path=test_db, recipe_id=recipe_id) is not None

        # Verify ingredients exist before delete
        conn = get_db_connection(db_path=test_db)
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
        ingredient_count_before_tuple = cursor.fetchone()
        assert ingredient_count_before_tuple is not None
        ingredient_count_before = ingredient_count_before_tuple[0]
        conn.close()
        assert ingredient_count_before == 1

        success: bool = delete_crafting_recipe(db_path=test_db, recipe_id=recipe_id)
        assert success is True
        assert get_crafting_recipe_by_id(db_path=test_db, recipe_id=recipe_id) is None

        # Verify ingredients are deleted due to CASCADE
        conn = get_db_connection(db_path=test_db)
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
        ingredient_count_after_tuple = cursor.fetchone()
        assert ingredient_count_after_tuple is not None
        ingredient_count_after = ingredient_count_after_tuple[0]
        conn.close()
        assert ingredient_count_after == 0

    def test_delete_crafting_recipe_non_existent(self, test_db):
        """Test deleting a non-existent recipe."""
        success = delete_crafting_recipe(db_path=test_db, recipe_id=666)
        assert success is False

    def test_crafting_recipe_updated_at_trigger(self, test_db, setup_common_resources_for_recipes):
        """Test the updated_at trigger for crafting_recipe table."""
        resources = setup_common_resources_for_recipes
        assert resources["iron_ingot"].id is not None

        created_recipe: Optional[CraftingRecipe] = create_crafting_recipe(
            db_path=test_db,
            name="Trigger Test Recipe",
            description="Initial Description",
            output_item_name="TTR-1",
            output_quantity=1,
            ingredients=[RecipeIngredient(resource_id=resources["iron_ingot"].id, quantity=1)]
        )
        assert created_recipe is not None and created_recipe.id is not None
        recipe_id: int = created_recipe.id

        initial_recipe_db: Optional[CraftingRecipe] = get_crafting_recipe_by_id(db_path=test_db, recipe_id=recipe_id)
        assert initial_recipe_db is not None
        assert initial_recipe_db.created_at is not None and initial_recipe_db.updated_at is not None

        initial_created_at = parse_sqlite_timestamp(initial_recipe_db.created_at)
        initial_updated_at = parse_sqlite_timestamp(initial_recipe_db.updated_at)
        assert abs(initial_created_at.timestamp() - initial_updated_at.timestamp()) < 0.1 # Should be very close

        time.sleep(0.05)

        update_success_obj: Optional[CraftingRecipe] = update_crafting_recipe(
            db_path=test_db,
            recipe_id=recipe_id,
            description="Updated Description"
        )
        assert update_success_obj is not None

        updated_recipe_db: Optional[CraftingRecipe] = get_crafting_recipe_by_id(db_path=test_db, recipe_id=recipe_id)
        assert updated_recipe_db is not None, "Updated recipe fetch failed in trigger test."
        assert updated_recipe_db.created_at is not None and updated_recipe_db.updated_at is not None
        # Ensure the format string matches the one used in database.py
        final_created_at = parse_sqlite_timestamp(updated_recipe_db.created_at)
        final_updated_at = parse_sqlite_timestamp(updated_recipe_db.updated_at)

        assert final_created_at == initial_created_at, "created_at should not change on update"
        assert final_updated_at > initial_updated_at, "updated_at should be greater than initial updated_at after update"

# --- Tests for SkillTreeNode ---
# class TestSkillTreeNodeCRUD:
# def test_create_skill_tree_node(test_db):
#     """Test creating a new skill tree node."""
#     created_node: Optional[SkillTreeNode] = create_skill_tree_node(
#         db_path=test_db,
#         name="Basic Armor Plating", 
#         description="Increases hull integrity.", 
#         skill_tree_name="Vehicle Enhancements",
#         unlock_cost="500 Solari, 10 Iron", 
#         effects="Hull +10%"
#     )
#     assert created_node is not None and created_node.id is not None

#     retrieved_node = get_skill_tree_node_by_id(db_path=test_db, node_id=created_node.id)
#     assert retrieved_node is not None
#     assert retrieved_node.name == "Basic Armor Plating"
#     assert retrieved_node.skill_tree_name == "Vehicle Enhancements"
#     assert retrieved_node.unlocked == 0 # Default

# def test_create_skill_tree_node_with_parent(test_db):
#     """Test creating a skill tree node with a parent."""
#     parent_node: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Prerequisite Skill", skill_tree_name="Core Skills")
#     assert parent_node is not None and parent_node.id is not None
#     parent_id: int = parent_node.id

#     child_node: Optional[SkillTreeNode] = create_skill_tree_node(
#         db_path=test_db,
#         name="Advanced Skill", 
#         skill_tree_name="Core Skills", 
#         parent_node_id=parent_id
#     )
#     assert child_node is not None and child_node.id is not None

#     retrieved_child = get_skill_tree_node_by_id(db_path=test_db, node_id=child_node.id)
#     assert retrieved_child is not None
#     assert retrieved_child.parent_node_id == parent_id

# def test_create_skill_tree_node_missing_name(test_db):
#     """Test creating a skill node with a missing name (should fail)."""
#     with pytest.raises(TypeError): # Name is required
#          create_skill_tree_node(db_path=test_db, description="A skill without a name.", skill_tree_name="Test Tree")


# def test_create_skill_tree_node_duplicate_name(test_db):
#     """Test creating a skill node with a duplicate name (should fail if names are unique)."""
#     create_skill_tree_node(db_path=test_db, name="Duplicate Skill Name Test", skill_tree_name="Test Tree")
    
#     node2: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Duplicate Skill Name Test", skill_tree_name="Test Tree")
#     assert node2 is None, "Creating a skill node with a duplicate name in the same tree should fail."

#     node3: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Duplicate Skill Name Test", skill_tree_name="Another Test Tree")
#     assert node3 is not None, "Creating a skill node with the same name in a different tree should succeed."


# def test_get_skill_tree_node_by_id(test_db):
#     """Test retrieving a skill node by its ID."""
#     created_node: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Target Node", skill_tree_name="Search Tree")
#     assert created_node is not None and created_node.id is not None

#     retrieved = get_skill_tree_node_by_id(db_path=test_db, node_id=created_node.id)
#     assert retrieved is not None
#     assert retrieved.id == created_node.id
#     assert retrieved.name == "Target Node"

# def test_get_skill_tree_node_by_id_non_existent(test_db):
#     """Test retrieving a non-existent skill node by ID."""
#     retrieved = get_skill_tree_node_by_id(db_path=test_db, node_id=9001)
#     assert retrieved is None

# def test_get_skill_tree_node_by_name(test_db): # Assuming (name, skill_tree_name) is unique
#     """Test retrieving a skill node by its name and tree."""
#     unique_node_name = "UniqueGlobalSkillName"
#     tree_name = "Global Search Tree"
#     create_skill_tree_node(db_path=test_db, name=unique_node_name, skill_tree_name=tree_name)

#     retrieved = get_skill_tree_node_by_name(db_path=test_db, name=unique_node_name, skill_tree_name=tree_name)
#     assert retrieved is not None
#     assert retrieved.name == unique_node_name
#     assert retrieved.skill_tree_name == tree_name

# def test_get_skill_tree_node_by_name_non_existent(test_db):
#     """Test retrieving a non-existent skill node by name."""
#     retrieved = get_skill_tree_node_by_name(db_path=test_db, name="Mythical Skill", skill_tree_name="NonExistentTree")
#     assert retrieved is None

# def test_get_all_skill_tree_nodes(test_db):
#     """Test retrieving all skill tree nodes."""
#     create_skill_tree_node(db_path=test_db, name="Skill Alpha", skill_tree_name="Tree X")
#     create_skill_tree_node(db_path=test_db, name="Skill Beta", skill_tree_name="Tree Y")
#     create_skill_tree_node(db_path=test_db, name="Skill Gamma", skill_tree_name="Tree X")

#     all_nodes: List[SkillTreeNode] = get_all_skill_tree_nodes(db_path=test_db)
#     assert len(all_nodes) == 3
    
#     retrieved_names = sorted([n.name for n in all_nodes])
#     expected_names = sorted(["Skill Alpha", "Skill Beta", "Skill Gamma"])
#     assert retrieved_names == expected_names

# def test_update_skill_tree_node(test_db):
#     """Test updating an existing skill tree node."""
#     created_node: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Evolvable Skill", description="Version 1", skill_tree_name="Update Tree")
#     assert created_node is not None and created_node.id is not None
#     node_id: int = created_node.id

#     initial_node = get_skill_tree_node_by_id(db_path=test_db, node_id=node_id)
#     assert initial_node is not None and initial_node.created_at is not None and initial_node.updated_at is not None
#     initial_created_at = datetime.fromisoformat(initial_node.created_at)
#     initial_updated_at = datetime.fromisoformat(initial_node.updated_at)

#     time.sleep(0.05)

#     updated_node_obj: Optional[SkillTreeNode] = update_skill_tree_node(
#         db_path=test_db, 
#         node_id=node_id, 
#         description="Version 2 - Enhanced", 
#         unlocked=1, 
#         effects="New Effect"
#     )
#     assert updated_node_obj is not None

#     fetched_updated_node = get_skill_tree_node_by_id(db_path=test_db, node_id=node_id)
#     assert fetched_updated_node is not None
#     assert fetched_updated_node.name == "Evolvable Skill" 
#     assert fetched_updated_node.description == "Version 2 - Enhanced"
#     assert fetched_updated_node.unlocked == 1
#     assert fetched_updated_node.effects == "New Effect"
    
#     assert fetched_updated_node.created_at is not None and fetched_updated_node.updated_at is not None
#     updated_created_at = datetime.fromisoformat(fetched_updated_node.created_at)
#     updated_updated_at = datetime.fromisoformat(fetched_updated_node.updated_at)

#     assert updated_created_at == initial_created_at
#     assert updated_updated_at > initial_updated_at 
#     # Check it actually changed if the initial timestamps were equal
#     if initial_created_at == initial_updated_at:
#          assert updated_updated_at >= initial_updated_at, "updated_at should change if it was same as created_at" # Changed > to >=
#     else: # if initial_updated_at was already > initial_created_at (e.g. due to a prior update not in this test scope)
#         assert updated_updated_at >= initial_updated_at, "updated_at should advance on subsequent updates" # Changed > to >=

# def test_update_skill_tree_node_change_name_to_duplicate(test_db):
#     """Test updating a skill node name to an existing name in the same tree (should fail)."""
#     nodeA: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="NodeA", skill_tree_name="Collision Test Tree")
#     assert nodeA is not None and nodeA.id is not None
#     nodeA_id: int = nodeA.id
    
#     create_skill_tree_node(db_path=test_db, name="NodeB", skill_tree_name="Collision Test Tree")

#     updated_node: Optional[SkillTreeNode] = update_skill_tree_node(db_path=test_db, node_id=nodeA_id, name="NodeB")
#     assert updated_node is None, "Updating name to a duplicate in the same tree should fail."

#     original_nodeA = get_skill_tree_node_by_id(db_path=test_db, node_id=nodeA_id)
#     assert original_nodeA is not None
#     assert original_nodeA.name == "NodeA"

# def test_update_skill_tree_node_non_existent(test_db):
#     """Test updating a non-existent skill tree node."""
#     updated_node: Optional[SkillTreeNode] = update_skill_tree_node(db_path=test_db, node_id=8888, name="NonExistentUpdated")
#     assert updated_node is None

# def test_delete_skill_tree_node(test_db):
#     """Test deleting a skill tree node."""
#     created_node: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Ephemeral Skill", skill_tree_name="Delete Tree")
#     assert created_node is not None and created_node.id is not None
#     node_id: int = created_node.id
    
#     assert get_skill_tree_node_by_id(db_path=test_db, node_id=node_id) is not None

#     success: bool = delete_skill_tree_node(db_path=test_db, node_id=node_id)
#     assert success is True
#     assert get_skill_tree_node_by_id(db_path=test_db, node_id=node_id) is None

# def test_delete_skill_tree_node_with_children(test_db):
#     """Test deleting a skill tree node that is a parent, children's parent_node_id should become NULL."""
#     parent: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Parent Skill", skill_tree_name="Family Tree")
#     assert parent is not None and parent.id is not None
#     parent_id: int = parent.id

#     child1: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Child Skill 1", skill_tree_name="Family Tree", parent_node_id=parent_id)
#     assert child1 is not None and child1.id is not None
#     child_id1: int = child1.id

#     child2: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="Child Skill 2", skill_tree_name="Family Tree", parent_node_id=parent_id)
#     assert child2 is not None and child2.id is not None
#     child_id2: int = child2.id

#     child1_before_delete = get_skill_tree_node_by_id(db_path=test_db, node_id=child_id1)
#     assert child1_before_delete is not None and child1_before_delete.parent_node_id == parent_id
    
#     child2_before_delete = get_skill_tree_node_by_id(db_path=test_db, node_id=child_id2)
#     assert child2_before_delete is not None and child2_before_delete.parent_node_id == parent_id

#     success_delete_parent: bool = delete_skill_tree_node(db_path=test_db, node_id=parent_id)
#     assert success_delete_parent is True
#     assert get_skill_tree_node_by_id(db_path=test_db, node_id=parent_id) is None

#     updated_child1 = get_skill_tree_node_by_id(db_path=test_db, node_id=child_id1)
#     assert updated_child1 is not None and updated_child1.parent_node_id is None

#     updated_child2 = get_skill_tree_node_by_id(db_path=test_db, node_id=child_id2)
#     assert updated_child2 is not None and updated_child2.parent_node_id is None

# def test_delete_skill_tree_node_non_existent(test_db):
#     """Test deleting a non-existent skill tree node."""
#     success: bool = delete_skill_tree_node(db_path=test_db, node_id=7777)
#     assert success is False

# def test_skill_tree_node_updated_at_trigger(test_db):
#     """Test that the updated_at field is automatically updated for skill_tree_node."""
#     created_node: Optional[SkillTreeNode] = create_skill_tree_node(db_path=test_db, name="TriggerSkill", description="Initial Desc", skill_tree_name="Trigger Test Tree")
#     assert created_node is not None and created_node.id is not None
#     node_id: int = created_node.id

#     initial_node = get_skill_tree_node_by_id(db_path=test_db, node_id=node_id)
#     assert initial_node is not None and initial_node.created_at is not None and initial_node.updated_at is not None
#     initial_created_at = datetime.fromisoformat(initial_node.created_at)
#     initial_updated_at = datetime.fromisoformat(initial_node.updated_at)

#     time.sleep(0.05)

#     update_success_obj: Optional[SkillTreeNode] = update_skill_tree_node(db_path=test_db, node_id=node_id, description="Updated Desc")
#     assert update_success_obj is not None

#     updated_node_db = get_skill_tree_node_by_id(db_path=test_db, node_id=node_id)
#     assert updated_node_db is not None and updated_node_db.created_at is not None and updated_node_db.updated_at is not None
#     final_created_at = datetime.fromisoformat(updated_node_db.created_at)
#     final_updated_at = datetime.fromisoformat(updated_node_db.updated_at)

#     assert final_created_at == initial_created_at
#     assert final_updated_at > initial_updated_at

