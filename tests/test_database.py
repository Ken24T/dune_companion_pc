import pytest
import os
from app.data.database import initialize_database, get_db_connection
from app.data.models import Resource
from app.data.crud import (
    create_resource,
    get_resource_by_id,
    get_resource_by_name,
    get_all_resources,
    update_resource,
    delete_resource
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
    # import time
    # time.sleep(0.01)

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
    
    assert updated_at_dt > created_at_dt # Check if trigger worked

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
    assert updated_updated_at_dt.timestamp() > initial_updated_at_dt.timestamp(), \
        f"updated_at ({updated_updated_at_dt}) should be greater than initial_updated_at ({initial_updated_at_dt})"

