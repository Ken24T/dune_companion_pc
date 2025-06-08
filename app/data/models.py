from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any # Using Dict and Any for JSON fields for now

# Using logger from the app
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Resource:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    rarity: Optional[str] = None
    category: Optional[str] = None
    source_locations: Optional[str] = None # Storing as JSON string as per schema
    icon_path: Optional[str] = None
    discovered: int = 0 # Boolean (0 or 1)
    created_at: Optional[str] = None # Will be ISO format string
    updated_at: Optional[str] = None # Will be ISO format string

@dataclass
class CraftingRecipe:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    output_item_name: str = ""
    output_quantity: int = 1
    crafting_time_seconds: Optional[int] = None
    required_station: Optional[str] = None
    skill_requirement: Optional[str] = None
    icon_path: Optional[str] = None
    discovered: int = 0 # Boolean (0 or 1)
    # For ingredients, we'll handle this via a separate list of RecipeIngredient or similar
    ingredients: List['RecipeIngredient'] = field(default_factory=list) 
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class RecipeIngredient:
    id: Optional[int] = None
    recipe_id: int = 0
    resource_id: int = 0
    quantity: int = 0
    # Optionally, store the resource name for convenience, though not in DB table
    resource_name: Optional[str] = None 

@dataclass
class SkillTreeNode:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    skill_tree_name: Optional[str] = None
    parent_node_id: Optional[int] = None
    unlock_cost: Optional[str] = None
    effects: Optional[str] = None # Storing as JSON string or detailed text
    icon_path: Optional[str] = None
    unlocked: int = 0 # Boolean (0 or 1)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class BaseBlueprint: # Simplified for MVP
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    category: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class LoreEntry:
    id: Optional[int] = None
    title: str = ""
    content_markdown: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None # Storing as JSON string
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class UserSetting:
    id: Optional[int] = None
    setting_key: str = ""
    setting_value: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class UserNote:
    id: Optional[int] = None
    entity_type: str = "" # e.g., 'resource', 'crafting_recipe'
    entity_id: int = 0
    note_text: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class AIChatHistory:
    id: Optional[int] = None
    timestamp: Optional[str] = None # ISO format string
    sender: str = "" # 'user' or 'ai'
    message_text: Optional[str] = None
    session_id: Optional[str] = None

logger.info("Data models defined.")
