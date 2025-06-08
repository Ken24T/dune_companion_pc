import sqlite3
import os
from typing import Optional, Dict # Added for type hinting
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default database directory and name
DEFAULT_DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DEFAULT_DATABASE_NAME = 'dune_companion.db'
DEFAULT_DATABASE_PATH = os.path.join(DEFAULT_DATABASE_DIR, DEFAULT_DATABASE_NAME)

# Timestamp format for SQLite, ensuring it produces ISO 8601 compatible strings
# Using a custom format that SQLite can handle and Python can parse
timestamp_format = "'%Y-%m-%d %H:%M:%f'"

# Default value for created_at and updated_at columns using UTC
now_utc_default = f"strftime({timestamp_format}, 'now', 'utc')" # Using explicit UTC
# now_utc_default = f"strftime({timestamp_format}, 'now')" # Using 'now' which is typically UTC in SQLite, simpler

# Trigger for updating updated_at column using UTC
now_utc_trigger = f"strftime({timestamp_format}, 'now', 'utc')" # Using explicit UTC
# now_utc_trigger = f"strftime({timestamp_format}, 'now')" # Using 'now'


# SQL commands for table creation
TABLE_DEFINITIONS: Dict[str, str] = {
    "resource": f"""
        CREATE TABLE IF NOT EXISTS resource (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            rarity TEXT,
            category TEXT,
            source_locations TEXT, -- JSON string for list of locations
            icon_path TEXT,
            discovered INTEGER DEFAULT 0, -- Boolean (0 or 1)
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "crafting_recipe": f"""
        CREATE TABLE IF NOT EXISTS crafting_recipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            output_item_name TEXT NOT NULL, -- Could be a resource name or a unique item
            output_quantity INTEGER DEFAULT 1,
            crafting_time_seconds INTEGER, -- Added missing column
            required_station TEXT, -- Added this line
            skill_requirement TEXT, -- Added this line
            icon_path TEXT, -- Added this line
            discovered INTEGER DEFAULT 0, -- Added this line
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "skill_tree_node": f"""
        CREATE TABLE IF NOT EXISTS skill_tree_node (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            skill_type TEXT, -- e.g., 'Passive', 'Active', 'Upgrade'
            unlock_requirements TEXT, -- JSON string for prerequisites (e.g., other skills, level)
            effects TEXT, -- JSON string describing what the skill does
            icon_path TEXT,
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "base_blueprint": f"""
        CREATE TABLE IF NOT EXISTS base_blueprint (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            resource_costs TEXT, -- JSON string for resources and quantities
            construction_time_seconds INTEGER,
            icon_path TEXT,
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "lore_entry": f"""
        CREATE TABLE IF NOT EXISTS lore_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            category TEXT, -- e.g., 'History', 'Characters', 'Locations'
            unlock_conditions TEXT, -- How the player discovers this lore
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "user_setting": f"""
        CREATE TABLE IF NOT EXISTS user_setting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT NOT NULL UNIQUE,
            setting_value TEXT,
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "user_note": f"""
        CREATE TABLE IF NOT EXISTS user_note (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT NOT NULL,
            tags TEXT, -- Comma-separated or JSON
            created_at TEXT DEFAULT ({now_utc_default}),
            updated_at TEXT DEFAULT ({now_utc_default})
        )
    """,
    "ai_chat_history": f"""
        CREATE TABLE IF NOT EXISTS ai_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT DEFAULT ({now_utc_default}),
            sender TEXT NOT NULL, -- 'user' or 'ai'
            message TEXT NOT NULL,
            metadata TEXT -- JSON for any extra info, e.g., context provided
        )
    """,
}

# SQL commands for trigger creation
TRIGGER_DEFINITIONS: Dict[str, str] = {
    "resource": f"""
        CREATE TRIGGER IF NOT EXISTS update_resource_updated_at
        AFTER UPDATE ON resource
        FOR EACH ROW
        BEGIN
            UPDATE resource SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
    "crafting_recipe": f"""
        CREATE TRIGGER IF NOT EXISTS update_crafting_recipe_updated_at
        AFTER UPDATE ON crafting_recipe
        FOR EACH ROW
        BEGIN
            UPDATE crafting_recipe SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
    "skill_tree_node": f"""
        CREATE TRIGGER IF NOT EXISTS update_skill_tree_node_updated_at
        AFTER UPDATE ON skill_tree_node
        FOR EACH ROW
        BEGIN
            UPDATE skill_tree_node SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
    "base_blueprint": f"""
        CREATE TRIGGER IF NOT EXISTS update_base_blueprint_updated_at
        AFTER UPDATE ON base_blueprint
        FOR EACH ROW
        BEGIN
            UPDATE base_blueprint SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
    "lore_entry": f"""
        CREATE TRIGGER IF NOT EXISTS update_lore_entry_updated_at
        AFTER UPDATE ON lore_entry
        FOR EACH ROW
        BEGIN
            UPDATE lore_entry SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
    "user_setting": f"""
        CREATE TRIGGER IF NOT EXISTS update_user_setting_updated_at
        AFTER UPDATE ON user_setting
        FOR EACH ROW
        BEGIN
            UPDATE user_setting SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
    "user_note": f"""
        CREATE TRIGGER IF NOT EXISTS update_user_note_updated_at
        AFTER UPDATE ON user_note
        FOR EACH ROW
        BEGIN
            UPDATE user_note SET updated_at = {now_utc_trigger} WHERE id = OLD.id;
        END;
    """,
}

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database.
    Enables foreign key support for the connection.
    Args:
        db_path (Optional[str]): Path to the database file. Uses default if None.
    Returns:
        sqlite3.Connection: A database connection object.
    """
    path_to_use = db_path if db_path else DEFAULT_DATABASE_PATH
    
    # Ensure the directory for the database exists
    if path_to_use != ':memory:': # Do not try to create dirs for in-memory DB
        os.makedirs(os.path.dirname(path_to_use), exist_ok=True)
        
    conn = sqlite3.connect(path_to_use)
    conn.row_factory = sqlite3.Row  # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
    logger.info(f"Database connection established to {path_to_use}")
    return conn

def initialize_database(db_path: Optional[str] = None):
    """Initializes the database by creating tables if they don't already exist.
    Args:
        db_path (Optional[str]): Path to the database file. 
                                 If None, uses DEFAULT_DATABASE_PATH.
    """
    conn = None
    actual_db_path = db_path if db_path else DEFAULT_DATABASE_PATH
    try:
        conn = get_db_connection(actual_db_path)
        cursor = conn.cursor()

        # --- Core Entities ---

        # Resource Table
        cursor.execute(TABLE_DEFINITIONS["resource"])
        logger.info("Table 'resource' checked/created.")

        # Crafting Recipe Table
        cursor.execute(TABLE_DEFINITIONS["crafting_recipe"])
        logger.info("Table 'crafting_recipe' checked/created.")

        # Skill Tree Node Table
        cursor.execute(TABLE_DEFINITIONS["skill_tree_node"])
        logger.info("Table 'skill_tree_node' checked/created.")
        
        # Base Blueprint Table (Simplified for MVP)
        cursor.execute(TABLE_DEFINITIONS["base_blueprint"])
        logger.info("Table 'base_blueprint' checked/created.")

        # Lore / Wiki Entry Table
        cursor.execute(TABLE_DEFINITIONS["lore_entry"])
        logger.info("Table 'lore_entry' checked/created.")

        # User Setting Table
        cursor.execute(TABLE_DEFINITIONS["user_setting"])
        logger.info("Table 'user_setting' checked/created.")

        # User Note Table
        cursor.execute(TABLE_DEFINITIONS["user_note"])
        logger.info("Table 'user_note' checked/created.")
        
        # AI Chat History (Optional, basic structure)
        cursor.execute(TABLE_DEFINITIONS["ai_chat_history"])
        logger.info("Table 'ai_chat_history' checked/created.")

        # --- Relationship Tables (Many-to-Many) ---

        # Crafting Recipe Ingredients (Links crafting_recipe to resource)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_ingredient (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES crafting_recipe(id) ON DELETE CASCADE,
                FOREIGN KEY (resource_id) REFERENCES resource(id) ON DELETE CASCADE,
                UNIQUE (recipe_id, resource_id) 
            )
        ''')
        logger.info("Table 'recipe_ingredient' checked/created.")
        
        # --- Triggers for updated_at ---
        # Use the TRIGGER_DEFINITIONS dictionary to create triggers
        for table_name, trigger_sql in TRIGGER_DEFINITIONS.items():
            cursor.execute(trigger_sql)
            logger.info(f"Trigger for table \'{table_name}\' checked/created using TRIGGER_DEFINITIONS.")

        conn.commit()
        logger.info("Database initialization complete. All tables checked/created.")

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info(f"Database connection to {actual_db_path} closed.")

def get_default_db_path() -> str:
    """Get the default database path."""
    return DEFAULT_DATABASE_PATH


def database_exists(db_path: Optional[str] = None) -> bool:
    """Check if the database file exists."""
    if db_path is None:
        db_path = DEFAULT_DATABASE_PATH
    return os.path.exists(db_path)


if __name__ == '__main__':
    # This allows running the script directly to initialize the database
    # For example, during initial setup or for testing.
    logger.info(f"Initializing database directly from database.py at {DEFAULT_DATABASE_PATH}...")
    initialize_database() # Uses default path
    logger.info("Database initialization process finished.")
