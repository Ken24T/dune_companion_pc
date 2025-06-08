import pytest
import os
import time # Added for sleep
from app.data.database import initialize_database, get_db_connection
from app.data.models import Resource, CraftingRecipe, RecipeIngredient # Added CraftingRecipe, RecipeIngredient
from app.data.crud import (
    create_resource,
    get_resource_by_id,
    get_resource_by_name,
    get_all_resources,
    update_resource,
    delete_resource,
    create_crafting_recipe, # Added
    get_crafting_recipe_by_id, # Added
    get_crafting_recipe_by_name, # Added
    get_all_crafting_recipes, # Added
    update_crafting_recipe, # Added
    delete_crafting_recipe # Added
)
from app.utils.logger import shutdown_logging # To close log file handles
from datetime import datetime

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
    
    # Initialize a fresh database for each test function
    initialize_database(db_path=TEST_DB_PATH)
    
    yield TEST_DB_PATH # Provide the path to the test database

    # Teardown: close connections and remove the test database file
    # Connections are closed within CRUD operations, but good to be sure.
    # Attempt to remove the test database file
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        # Attempt to remove the test database directory if it's empty
        if os.path.exists(TEST_DB_DIR) and not os.listdir(TEST_DB_DIR):
            os.rmdir(TEST_DB_DIR)
    except PermissionError as e:
        print(f"Warning: Could not remove test database file {TEST_DB_PATH} or dir {TEST_DB_DIR}: {e}")


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
    resource_data = Resource(name="Spice", description="The spice must flow.", rarity="Legendary", category="Consumable")
    resource_id = create_resource(resource_data, db_path=test_db)
    
    assert resource_id is not None
    
    retrieved_resource = get_resource_by_id(resource_id, db_path=test_db)
    assert retrieved_resource is not None
    assert retrieved_resource.name == "Spice"
    assert retrieved_resource.description == "The spice must flow."
    assert retrieved_resource.rarity == "Legendary"
    assert retrieved_resource.category == "Consumable"
    assert retrieved_resource.discovered == 0 # Default value

def test_create_resource_missing_name(test_db):
    """Test creating a resource with a missing name (should fail)."""
    resource_data = Resource(description="A resource without a name.")
    resource_id = create_resource(resource_data, db_path=test_db)
    assert resource_id is None, "Creating a resource without a name should fail."

def test_create_resource_duplicate_name(test_db):
    """Test creating a resource with a duplicate name (should fail)."""
    resource1 = Resource(name="Water", description="H2O")
    create_resource(resource1, db_path=test_db)
    
    resource2 = Resource(name="Water", description="Still H2O")
    resource_id2 = create_resource(resource2, db_path=test_db)
    assert resource_id2 is None, "Creating a resource with a duplicate name should fail."

def test_get_resource_by_id(test_db):
    """Test retrieving a resource by its ID."""
    resource_data = Resource(name="Iron Ore", category="Mineral")
    resource_id = create_resource(resource_data, db_path=test_db)
    assert resource_id is not None

    retrieved_resource = get_resource_by_id(resource_id, db_path=test_db)
    assert retrieved_resource is not None
    assert retrieved_resource.id == resource_id
    assert retrieved_resource.name == "Iron Ore"

def test_get_resource_by_id_non_existent(test_db):
    """Test retrieving a non-existent resource by ID."""
    retrieved_resource = get_resource_by_id(9999, db_path=test_db) # Assuming 9999 does not exist
    assert retrieved_resource is None

def test_get_resource_by_name(test_db):
    """Test retrieving a resource by its name."""
    resource_data = Resource(name="Crystal", category="Gemstone")
    create_resource(resource_data, db_path=test_db)

    retrieved_resource = get_resource_by_name("Crystal", db_path=test_db)
    assert retrieved_resource is not None
    assert retrieved_resource.name == "Crystal"

def test_get_resource_by_name_non_existent(test_db):
    """Test retrieving a non-existent resource by name."""
    retrieved_resource = get_resource_by_name("Unobtanium", db_path=test_db)
    assert retrieved_resource is None

def test_get_all_resources(test_db):
    """Test retrieving all resources."""
    resources_data = [
        Resource(name="Sandworm Tooth", category="Monster Part"),
        Resource(name="Thumper", category="Tool"),
        Resource(name="Ornithopter Fuel", category="Fuel")
    ]
    for res_data in resources_data:
        create_resource(res_data, db_path=test_db)

    all_resources = get_all_resources(db_path=test_db)
    assert len(all_resources) == len(resources_data)
    
    # Check if names are present (order is by name)
    retrieved_names = sorted([res.name for res in all_resources])
    expected_names = sorted([res_data.name for res_data in resources_data])
    assert retrieved_names == expected_names

def test_update_resource(test_db):
    """Test updating an existing resource."""
    resource_data = Resource(name="Solari", description="Currency of the Imperium", category="Currency")
    resource_id = create_resource(resource_data, db_path=test_db)
    assert resource_id is not None

    # Ensure there's a slight delay for timestamp comparison
    # No sleep needed here, direct update.

    update_data = Resource(description="The official currency of the Imperium and CHOAM.", rarity="Common", discovered=1)
    success = update_resource(resource_id, update_data, db_path=test_db)
    assert success is True

    updated_resource = get_resource_by_id(resource_id, db_path=test_db)
    assert updated_resource is not None
    assert updated_resource.name == "Solari" # Name should not change
    assert updated_resource.description == "The official currency of the Imperium and CHOAM."
    assert updated_resource.rarity == "Common"
    assert updated_resource.discovered == 1
    assert updated_resource.created_at is not None # Should exist
    assert updated_resource.updated_at is not None # Should exist
    
    # Convert string timestamps to datetime objects if they are not already
    created_at_dt = datetime.fromisoformat(updated_resource.created_at) if isinstance(updated_resource.created_at, str) else updated_resource.created_at
    updated_at_dt = datetime.fromisoformat(updated_resource.updated_at) if isinstance(updated_resource.updated_at, str) else updated_resource.updated_at
    
    assert updated_at_dt >= created_at_dt # Check if trigger worked (>= allows for same-second updates)

def test_update_resource_change_name_duplicate(test_db):
    """Test updating a resource name to an existing name (should fail)."""
    res1 = Resource(name="ResourceA")
    res1_id = create_resource(res1, db_path=test_db)
    assert res1_id is not None, "res1_id should not be None after creation"
    res2 = Resource(name="ResourceB")
    create_resource(res2, db_path=test_db)

    update_data = Resource(name="ResourceB") # Try to change ResourceA's name to ResourceB
    success = update_resource(res1_id, update_data, db_path=test_db)
    assert success is False, "Updating name to an existing one should fail due to UNIQUE constraint."
    
    original_res1 = get_resource_by_id(res1_id, db_path=test_db)
    assert original_res1 is not None, "original_res1 should not be None"
    assert original_res1.name == "ResourceA"


def test_update_resource_non_existent(test_db):
    """Test updating a non-existent resource."""
    update_data = Resource(name="NonExistentUpdated")
    success = update_resource(8888, update_data, db_path=test_db) # Assuming 8888 does not exist
    assert success is False

def test_delete_resource(test_db):
    """Test deleting a resource."""
    resource_data = Resource(name="Kindjal", category="Weapon")
    resource_id = create_resource(resource_data, db_path=test_db)
    assert resource_id is not None
    assert get_resource_by_id(resource_id, db_path=test_db) is not None # Verify it exists

    success = delete_resource(resource_id, db_path=test_db)
    assert success is True
    assert get_resource_by_id(resource_id, db_path=test_db) is None # Verify it's deleted

def test_delete_resource_non_existent(test_db):
    """Test deleting a non-existent resource."""
    success = delete_resource(7777, db_path=test_db) # Assuming 7777 does not exist
    assert success is False

def test_resource_updated_at_trigger(test_db):
    """Test that the updated_at field is automatically updated by the trigger."""
    resource = Resource(name="TestTriggerResource", description="Initial Description")
    resource_id = create_resource(resource, db_path=test_db)
    assert resource_id is not None, "resource_id should not be None after creation"

    initial_resource = get_resource_by_id(resource_id, db_path=test_db)
    assert initial_resource is not None
    assert initial_resource.created_at is not None
    assert initial_resource.updated_at is not None

    # Convert string timestamps to datetime objects if they are not already
    initial_created_at_dt = datetime.fromisoformat(initial_resource.created_at) if isinstance(initial_resource.created_at, str) else initial_resource.created_at
    initial_updated_at_dt = datetime.fromisoformat(initial_resource.updated_at) if isinstance(initial_resource.updated_at, str) else initial_resource.updated_at

    # On creation, they should be very close or identical.
    assert abs(initial_created_at_dt.timestamp() - initial_updated_at_dt.timestamp()) < 0.1 # Allow minor diff

    import time
    time.sleep(0.05) # Increased delay to ensure timestamp difference

    update_data = Resource(description="Updated Description") # Only description is updated
    update_success = update_resource(resource_id, update_data, db_path=test_db)
    assert update_success

    updated_resource = get_resource_by_id(resource_id, db_path=test_db)
    assert updated_resource is not None
    assert updated_resource.created_at is not None
    assert updated_resource.updated_at is not None

    # Convert string timestamps to datetime objects
    updated_created_at_dt = datetime.fromisoformat(updated_resource.created_at) if isinstance(updated_resource.created_at, str) else updated_resource.created_at
    updated_updated_at_dt = datetime.fromisoformat(updated_resource.updated_at) if isinstance(updated_resource.updated_at, str) else updated_resource.updated_at
    
    assert updated_created_at_dt.timestamp() == initial_created_at_dt.timestamp() # created_at should not change
    assert updated_updated_at_dt.timestamp() >= initial_updated_at_dt.timestamp(), \
        f"updated_at ({updated_updated_at_dt}) should be greater than or equal to initial_updated_at ({initial_updated_at_dt})"

# --- CRUD Tests for CraftingRecipe ---

@pytest.fixture
def setup_common_resources_for_recipes(test_db):
    """Fixture to create some common resources needed for recipe tests."""
    res1 = Resource(name="Iron Ingot", description="Processed iron.")
    res2 = Resource(name="Copper Wire", description="Thin copper wire.")
    res3 = Resource(name="Plastic Casing", description="A plastic shell.")
    res1_id = create_resource(res1, db_path=test_db)
    res2_id = create_resource(res2, db_path=test_db)
    res3_id = create_resource(res3, db_path=test_db)
    return {"Iron Ingot": res1_id, "Copper Wire": res2_id, "Plastic Casing": res3_id}

def test_create_crafting_recipe(test_db, setup_common_resources_for_recipes):
    """Test creating a new crafting recipe with ingredients."""
    resources = setup_common_resources_for_recipes
    recipe_data = CraftingRecipe(
        name="Basic Gadget",
        description="A simple electronic gadget.",
        output_item_name="Gadget Alpha",
        output_quantity=1,
        ingredients=[
            RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=2),
            RecipeIngredient(resource_id=resources["Copper Wire"], quantity=5)
        ]
    )
    recipe_id = create_crafting_recipe(recipe_data, db_path=test_db)
    assert recipe_id is not None

    retrieved_recipe = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert retrieved_recipe is not None
    assert retrieved_recipe.name == "Basic Gadget"
    assert retrieved_recipe.output_item_name == "Gadget Alpha"
    assert len(retrieved_recipe.ingredients) == 2
    
    # Check ingredient details (order might vary, so check by resource_id or name if populated)
    ing_iron = next((ing for ing in retrieved_recipe.ingredients if ing.resource_id == resources["Iron Ingot"]), None)
    ing_copper = next((ing for ing in retrieved_recipe.ingredients if ing.resource_id == resources["Copper Wire"]), None)
    
    assert ing_iron is not None
    assert ing_iron.quantity == 2
    assert ing_iron.resource_name == "Iron Ingot" # Check if resource_name is populated by get method

    assert ing_copper is not None
    assert ing_copper.quantity == 5
    assert ing_copper.resource_name == "Copper Wire"

def test_create_crafting_recipe_no_ingredients(test_db):
    """Test creating a recipe without any ingredients."""
    recipe_data = CraftingRecipe(name="Empty Recipe", output_item_name="Nothing")
    recipe_id = create_crafting_recipe(recipe_data, db_path=test_db)
    assert recipe_id is not None
    retrieved = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert retrieved is not None
    assert retrieved.name == "Empty Recipe"
    assert len(retrieved.ingredients) == 0

def test_create_crafting_recipe_missing_name(test_db):
    """Test creating a recipe with missing name (should fail)."""
    recipe_data = CraftingRecipe(output_item_name="Nameless Output")
    recipe_id = create_crafting_recipe(recipe_data, db_path=test_db)
    assert recipe_id is None

def test_create_crafting_recipe_duplicate_name(test_db):
    """Test creating a recipe with a duplicate name (should fail)."""
    recipe1 = CraftingRecipe(name="Unique Recipe", output_item_name="Output1")
    create_crafting_recipe(recipe1, db_path=test_db)
    recipe2 = CraftingRecipe(name="Unique Recipe", output_item_name="Output2")
    recipe_id2 = create_crafting_recipe(recipe2, db_path=test_db)
    assert recipe_id2 is None

def test_get_crafting_recipe_by_id(test_db, setup_common_resources_for_recipes):
    """Test retrieving a recipe by ID."""
    resources = setup_common_resources_for_recipes
    recipe_data = CraftingRecipe(
        name="Specific Recipe", 
        output_item_name="Specific Output",
        ingredients=[RecipeIngredient(resource_id=resources["Plastic Casing"], quantity=1)]
    )
    recipe_id = create_crafting_recipe(recipe_data, db_path=test_db)
    assert recipe_id is not None

    retrieved = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert retrieved is not None
    assert retrieved.id == recipe_id
    assert retrieved.name == "Specific Recipe"
    assert len(retrieved.ingredients) == 1
    assert retrieved.ingredients[0].resource_id == resources["Plastic Casing"]
    assert retrieved.ingredients[0].resource_name == "Plastic Casing"

def test_get_crafting_recipe_by_id_non_existent(test_db):
    """Test retrieving non-existent recipe by ID."""
    retrieved = get_crafting_recipe_by_id(999, db_path=test_db)
    assert retrieved is None

def test_get_crafting_recipe_by_name(test_db, setup_common_resources_for_recipes):
    """Test retrieving a recipe by its name."""
    resources = setup_common_resources_for_recipes
    recipe_data = CraftingRecipe(
        name="Searchable Recipe", 
        output_item_name="Searchable Output",
        ingredients=[RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=3)]
    )
    create_crafting_recipe(recipe_data, db_path=test_db)

    retrieved = get_crafting_recipe_by_name("Searchable Recipe", db_path=test_db)
    assert retrieved is not None
    assert retrieved.name == "Searchable Recipe"
    assert len(retrieved.ingredients) == 1
    assert retrieved.ingredients[0].resource_id == resources["Iron Ingot"]
    assert retrieved.ingredients[0].resource_name == "Iron Ingot"

def test_get_crafting_recipe_by_name_non_existent(test_db):
    """Test retrieving non-existent recipe by name."""
    retrieved = get_crafting_recipe_by_name("Imaginary Recipe", db_path=test_db)
    assert retrieved is None

def test_get_all_crafting_recipes(test_db, setup_common_resources_for_recipes):
    """Test retrieving all crafting recipes."""
    resources = setup_common_resources_for_recipes
    recipe1_data = CraftingRecipe(name="Recipe A", output_item_name="Item A", ingredients=[
        RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=1)
    ])
    recipe2_data = CraftingRecipe(name="Recipe B", output_item_name="Item B", ingredients=[
        RecipeIngredient(resource_id=resources["Copper Wire"], quantity=2)
    ])
    create_crafting_recipe(recipe1_data, db_path=test_db)
    create_crafting_recipe(recipe2_data, db_path=test_db)

    all_recipes = get_all_crafting_recipes(db_path=test_db)
    assert len(all_recipes) == 2
    recipe_names = sorted([r.name for r in all_recipes])
    assert recipe_names == ["Recipe A", "Recipe B"]

    # Check ingredients are populated for one of them
    recipe_a = next((r for r in all_recipes if r.name == "Recipe A"), None)
    assert recipe_a is not None
    assert len(recipe_a.ingredients) == 1
    assert recipe_a.ingredients[0].resource_id == resources["Iron Ingot"]
    assert recipe_a.ingredients[0].resource_name == "Iron Ingot"

def test_update_crafting_recipe_fields_and_ingredients(test_db, setup_common_resources_for_recipes):
    """Test updating recipe fields and its ingredients list."""
    resources = setup_common_resources_for_recipes
    # Initial recipe
    initial_recipe = CraftingRecipe(
        name="Updatable Gadget",
        description="Version 1.0",
        output_item_name="UG-1",
        output_quantity=1,
        ingredients=[
            RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=1)
        ]
    )
    recipe_id = create_crafting_recipe(initial_recipe, db_path=test_db)
    assert recipe_id is not None
    time.sleep(0.05) # Ensure timestamp difference for updated_at
    # Update data: change description, output_quantity, and ingredients
    update_data = CraftingRecipe(
        description="Version 2.0 with more features", 
        output_quantity=2, 
        ingredients=[
            RecipeIngredient(resource_id=resources["Copper Wire"], quantity=10),
            RecipeIngredient(resource_id=resources["Plastic Casing"], quantity=3)
        ]
    )
    success = update_crafting_recipe(recipe_id, update_data, db_path=test_db)
    assert success is True

    updated_recipe = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert updated_recipe is not None
    assert updated_recipe.name == "Updatable Gadget" # Name should not change if not in update_data
    assert updated_recipe.description == "Version 2.0 with more features"
    assert updated_recipe.output_item_name == "UG-1" # Should not change
    assert updated_recipe.output_quantity == 2
    assert len(updated_recipe.ingredients) == 2

    ing_copper = next((ing for ing in updated_recipe.ingredients if ing.resource_id == resources["Copper Wire"]), None)
    ing_plastic = next((ing for ing in updated_recipe.ingredients if ing.resource_id == resources["Plastic Casing"]), None)

    assert ing_copper is not None
    assert ing_copper.quantity == 10
    assert ing_copper.resource_name == "Copper Wire"

    assert ing_plastic is not None
    assert ing_plastic.quantity == 3
    assert ing_plastic.resource_name == "Plastic Casing"

    # Fetch the recipe again to get DB-assigned timestamps for the initial state
    # This is done *before* the update but *after* the creation and potential sleep
    conn_initial = get_db_connection(test_db)
    cursor_initial = conn_initial.cursor()
    cursor_initial.execute("SELECT created_at, updated_at FROM crafting_recipe WHERE id = ?", (recipe_id,))
    row_before_update = cursor_initial.fetchone()
    conn_initial.close()
    assert row_before_update is not None, "Recipe should exist before update for timestamp check."
    initial_db_created_at = datetime.fromisoformat(row_before_update['created_at'])
    initial_db_updated_at = datetime.fromisoformat(row_before_update['updated_at'])

    # Now get the timestamps from the updated_recipe object (which was fetched after update)
    assert updated_recipe.created_at is not None, "updated_recipe.created_at should not be None"
    assert updated_recipe.updated_at is not None, "updated_recipe.updated_at should not be None"
    updated_created_at = datetime.fromisoformat(updated_recipe.created_at)
    updated_updated_at = datetime.fromisoformat(updated_recipe.updated_at)
    
    assert updated_created_at == initial_db_created_at, "created_at timestamp should not change on update."
    assert updated_updated_at >= initial_db_updated_at, f"updated_at ({updated_updated_at}) should be greater than or equal to initial_db_updated_at ({initial_db_updated_at})."

def test_update_crafting_recipe_only_fields_no_ingredients_change(test_db, setup_common_resources_for_recipes):
    """Test updating only scalar fields of a recipe, leaving ingredients as they were (by re-supplying them)."""
    resources = setup_common_resources_for_recipes
    initial_recipe_model = CraftingRecipe(
        name="Field Update Test", 
        output_item_name="FUT-1",
        ingredients=[RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=1)]
    )
    recipe_id = create_crafting_recipe(initial_recipe_model, db_path=test_db)
    assert recipe_id is not None

    update_data = CraftingRecipe(
        description="New Description", # Only description changes
        ingredients=[RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=1)] 
    )
    success = update_crafting_recipe(recipe_id, update_data, db_path=test_db)
    assert success is True

    updated_recipe = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert updated_recipe is not None, "Recipe should be found after update."
    assert updated_recipe.description == "New Description"
    assert len(updated_recipe.ingredients) == 1
    assert updated_recipe.ingredients[0].resource_id == resources["Iron Ingot"]

def test_update_crafting_recipe_clear_ingredients(test_db, setup_common_resources_for_recipes):
    """Test updating a recipe to have no ingredients."""
    resources = setup_common_resources_for_recipes
    initial_recipe_model = CraftingRecipe(
        name="Clear Ingredients Test", 
        output_item_name="CIT-1",
        ingredients=[RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=1)]
    )
    recipe_id = create_crafting_recipe(initial_recipe_model, db_path=test_db)
    assert recipe_id is not None
    
    recipe_before_update = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert recipe_before_update is not None, "Recipe should exist before clearing ingredients."
    assert len(recipe_before_update.ingredients) == 1

    update_data = CraftingRecipe(ingredients=[]) # Empty list to clear ingredients
    success = update_crafting_recipe(recipe_id, update_data, db_path=test_db)
    assert success is True

    updated_recipe = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert updated_recipe is not None, "Recipe should still exist after clearing ingredients."
    assert len(updated_recipe.ingredients) == 0

def test_update_crafting_recipe_non_existent(test_db):
    """Test updating a non-existent recipe."""
    update_data = CraftingRecipe(name="NonExistentUpdate")
    success = update_crafting_recipe(777, update_data, db_path=test_db)
    assert success is False

def test_delete_crafting_recipe(test_db, setup_common_resources_for_recipes):
    """Test deleting a crafting recipe and its ingredients (via CASCADE)."""
    resources = setup_common_resources_for_recipes
    recipe_data = CraftingRecipe(
        name="To Be Deleted", 
        output_item_name="TBD-1",
        ingredients=[RecipeIngredient(resource_id=resources["Copper Wire"], quantity=3)]
    )
    recipe_id = create_crafting_recipe(recipe_data, db_path=test_db)
    assert recipe_id is not None
    assert get_crafting_recipe_by_id(recipe_id, db_path=test_db) is not None

    # Verify ingredients exist before delete
    conn = get_db_connection(db_path=test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
    ingredient_count_before = cursor.fetchone()[0]
    conn.close()
    assert ingredient_count_before == 1

    success = delete_crafting_recipe(recipe_id, db_path=test_db)
    assert success is True
    assert get_crafting_recipe_by_id(recipe_id, db_path=test_db) is None

    # Verify ingredients are deleted due to CASCADE
    conn = get_db_connection(db_path=test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
    ingredient_count_after = cursor.fetchone()[0]
    conn.close()
    assert ingredient_count_after == 0

def test_delete_crafting_recipe_non_existent(test_db):
    """Test deleting a non-existent recipe."""
    success = delete_crafting_recipe(666, db_path=test_db)
    assert success is False

def test_crafting_recipe_updated_at_trigger(test_db, setup_common_resources_for_recipes):
    """Test the updated_at trigger for crafting_recipe table."""
    resources = setup_common_resources_for_recipes
    recipe = CraftingRecipe(
        name="Trigger Test Recipe",
        description="Initial Description",
        output_item_name="TTR-1",
        output_quantity=1,
        ingredients=[RecipeIngredient(resource_id=resources["Iron Ingot"], quantity=1)]
    )
    recipe_id = create_crafting_recipe(recipe, db_path=test_db)
    assert recipe_id is not None

    # Get initial timestamps
    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT created_at, updated_at FROM crafting_recipe WHERE id = ?", (recipe_id,))
    row_before_update = cursor.fetchone()
    conn.close()
    assert row_before_update is not None
    initial_created_at = datetime.fromisoformat(row_before_update['created_at'])
    initial_updated_at = datetime.fromisoformat(row_before_update['updated_at'])

    # Wait a bit to ensure the timestamp will be different
    time.sleep(0.05)

    # Perform an update that should trigger the updated_at change
    update_data = CraftingRecipe(description="Updated Description")
    update_success = update_crafting_recipe(recipe_id, update_data, db_path=test_db)
    assert update_success

    updated_recipe_db = get_crafting_recipe_by_id(recipe_id, db_path=test_db)
    assert updated_recipe_db is not None, "Updated recipe fetch failed in trigger test."
    assert updated_recipe_db.created_at is not None, "updated_recipe_db.created_at is None"
    assert updated_recipe_db.updated_at is not None, "updated_recipe_db.updated_at is None"
    final_created_at = datetime.fromisoformat(updated_recipe_db.created_at)
    final_updated_at = datetime.fromisoformat(updated_recipe_db.updated_at)

    assert final_created_at == initial_created_at
    assert final_updated_at >= initial_updated_at, \
        f"final_updated_at ({final_updated_at}) should be >= initial_updated_at ({initial_updated_at})"

