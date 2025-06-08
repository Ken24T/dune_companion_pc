import sqlite3
from typing import List, Optional, Any, Tuple

from app.data.models import Resource
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
