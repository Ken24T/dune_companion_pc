import sqlite3
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
DATABASE_NAME = 'dune_companion.db'
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)

def get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database.
    Ensures the data directory exists.
    Returns:
        sqlite3.Connection: A connection object to the database.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    logger.info(f"Database connection established to {DATABASE_PATH}")
    return conn

def initialize_database():
    """Initializes the database by creating tables if they don't already exist."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- Core Entities ---

        # Resource Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                rarity TEXT,
                category TEXT, -- e.g., Mineral, Flora, Fauna, Gas, Liquid, Salvage
                source_locations TEXT, -- JSON list of strings or more structured data
                icon_path TEXT,
                discovered INTEGER DEFAULT 0, -- Boolean (0 or 1)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'resource' checked/created.")

        # Crafting Recipe Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crafting_recipe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                output_item_name TEXT NOT NULL, -- Could be a resource name or a unique item
                output_quantity INTEGER DEFAULT 1,
                crafting_time_seconds INTEGER,
                required_station TEXT, -- e.g., Workbench, Forge, Chemistry Station
                skill_requirement TEXT, -- e.g., "Advanced Engineering"
                icon_path TEXT,
                discovered INTEGER DEFAULT 0, -- Boolean (0 or 1)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'crafting_recipe' checked/created.")

        # Skill Tree Node Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_tree_node (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                skill_tree_name TEXT, -- e.g., Combat, Survival, Crafting
                parent_node_id INTEGER,
                unlock_cost TEXT, -- e.g., "5 points", "Requires X item"
                effects TEXT, -- JSON list of effects or detailed description
                icon_path TEXT,
                unlocked INTEGER DEFAULT 0, -- Boolean (0 or 1)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_node_id) REFERENCES skill_tree_node(id)
            )
        ''')
        logger.info("Table 'skill_tree_node' checked/created.")
        
        # Base Blueprint Table (Simplified for MVP)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_blueprint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                category TEXT, -- e.g., Structure, Defense, Utility
                thumbnail_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'base_blueprint' checked/created.")

        # Lore / Wiki Entry Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lore_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                content_markdown TEXT,
                category TEXT, -- e.g., Characters, Locations, Factions, History
                tags TEXT, -- JSON list of strings for search
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'lore_entry' checked/created.")

        # User Setting Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_setting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'user_setting' checked/created.")

        # User Note Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_note (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL, -- e.g., 'resource', 'crafting_recipe'
                entity_id INTEGER NOT NULL,
                note_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Table 'user_note' checked/created.")
        
        # AI Chat History (Optional, basic structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sender TEXT NOT NULL, -- 'user' or 'ai'
                message_text TEXT,
                session_id TEXT -- To group messages if multiple chat sessions are supported
            )
        ''')
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
        tables_with_updated_at = [
            'resource', 'crafting_recipe', 'skill_tree_node', 
            'base_blueprint', 'lore_entry', 'user_setting', 'user_note'
        ]
        for table_name in tables_with_updated_at:
            trigger_name = f'update_{table_name}_updated_at'
            cursor.execute(f'''
                CREATE TRIGGER IF NOT EXISTS {trigger_name}
                AFTER UPDATE ON {table_name}
                FOR EACH ROW
                BEGIN
                    UPDATE {table_name}
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END;
            ''')
            logger.info(f"Trigger '{trigger_name}' checked/created for table '{table_name}'.")

        conn.commit()
        logger.info("Database initialization complete. All tables checked/created.")

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info(f"Database connection to {DATABASE_PATH} closed.")

if __name__ == '__main__':
    # This allows running the script directly to initialize the database
    # For example, during initial setup or for testing.
    logger.info("Initializing database directly from database.py...")
    initialize_database()
    logger.info("Database initialization process finished.")
