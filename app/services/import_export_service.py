#!/usr/bin/env python3
"""
Import/Export Service for Dune Companion PC App.

This module provides functionality to import and export data in various formats
including JSON, Markdown, and CSV. It handles resources, crafting recipes,
and other game data for backup, sharing, and migration purposes.
"""

import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.data.database import get_default_db_path
from app.data.crud import (
    get_all_resources, get_all_crafting_recipes,
    create_resource, update_resource, get_resource_by_name, # Added update_resource, get_resource_by_name
    create_crafting_recipe, update_crafting_recipe, get_crafting_recipe_by_name # Added update_crafting_recipe, get_crafting_recipe_by_name
)
from app.data.models import Resource, CraftingRecipe, RecipeIngredient # Ensure RecipeIngredient is available for recipe import
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImportExportService:
    """Service for importing and exporting Dune Companion data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the import/export service."""
        self.supported_formats = ['json', 'markdown', 'csv']
        self.db_path = db_path or get_default_db_path()
        logger.info("Import/Export service initialized")
    
    # Export Methods
    
    def export_all_data(self, export_path: Path, format_type: str = 'json') -> bool:
        """
        Export all application data to the specified format.
        
        Args:
            export_path: Path where the exported data will be saved
            format_type: Format to export ('json', 'markdown', 'csv')
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")
            
            # Get all data from database
            data = self._get_all_data()
            
            if format_type == 'json':
                return self._export_json(data, export_path)
            elif format_type == 'markdown':
                return self._export_markdown(data, export_path)
            elif format_type == 'csv':
                return self._export_csv(data, export_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
    
    def export_resources(self, export_path: Path, format_type: str = 'json') -> bool:
        """Export only resources data."""
        try:
            resources = get_all_resources(self.db_path)
            data = {'resources': [self._resource_to_dict(r) for r in resources]}
            
            if format_type == 'json':
                return self._export_json(data, export_path)
            elif format_type == 'csv':
                return self._export_resources_csv(resources, export_path)
            elif format_type == 'markdown':
                return self._export_resources_markdown(resources, export_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to export resources: {e}")
            return False
    
    def export_crafting_recipes(self, export_path: Path, format_type: str = 'json') -> bool:
        """Export only crafting recipes data."""
        try:
            recipes = get_all_crafting_recipes(self.db_path)
            data = {'crafting_recipes': [self._recipe_to_dict(r) for r in recipes]}
            
            if format_type == 'json':
                return self._export_json(data, export_path)
            elif format_type == 'csv':
                return self._export_recipes_csv(recipes, export_path)
            elif format_type == 'markdown':
                return self._export_recipes_markdown(recipes, export_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to export crafting recipes: {e}")
            return False
    
    # Import Methods
    
    def import_data(self, import_path: Path, format_type: str, merge_strategy: str = 'update') -> bool:
        """
        Import data from specified file and format.
        
        Args:
            import_path: Path to the file to import
            format_type: Format of the file ('json', 'markdown', 'csv')
            merge_strategy: How to handle existing data ('update', 'replace', 'skip')
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")
            
            if not import_path.exists():
                logger.error(f"Import file does not exist: {import_path}")
                return False
            
            if format_type == 'json':
                return self._import_json(import_path, merge_strategy)
            elif format_type == 'markdown':
                return self._import_markdown(import_path, merge_strategy)
            elif format_type == 'csv':
                return self._import_csv(import_path, merge_strategy)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            return False
    
    # Helper Methods
    
    def _get_all_data(self) -> Dict[str, Any]:
        """Get all data from database with metadata."""
        resources = get_all_resources(self.db_path)
        recipes = get_all_crafting_recipes(self.db_path)
        
        return {
            'metadata': {
                'export_date': datetime.now(timezone.utc).isoformat(),
                'app_version': '0.1.0',
                'total_resources': len(resources),
                'total_recipes': len(recipes)
            },
            'resources': [self._resource_to_dict(r) for r in resources],
            'crafting_recipes': [self._recipe_to_dict(r) for r in recipes]
        }
    
    def _resource_to_dict(self, resource: Resource) -> Dict[str, Any]:
        """Convert a Resource object to dictionary."""
        return {
            'id': resource.id,
            'name': resource.name,
            'category': resource.category,
            'rarity': resource.rarity,
            'description': resource.description,
            'source_locations': getattr(resource, 'source_locations', None),
            'icon_path': getattr(resource, 'icon_path', None),
            'discovered': getattr(resource, 'discovered', 0),
            'created_at': resource.created_at,
            'updated_at': resource.updated_at
        }
    
    def _recipe_to_dict(self, recipe: CraftingRecipe) -> Dict[str, Any]:
        """Convert a CraftingRecipe object to dictionary."""
        return {
            'id': recipe.id,
            'name': recipe.name,
            'category': getattr(recipe, 'category', None),
            'description': recipe.description,
            'output_item_name': recipe.output_item_name,
            'output_quantity': recipe.output_quantity,
            'crafting_time_seconds': recipe.crafting_time_seconds,
            'required_station': recipe.required_station,
            'skill_requirement': recipe.skill_requirement,
            'icon_path': recipe.icon_path,
            'discovered': recipe.discovered,
            'ingredients': recipe.ingredients,
            'created_at': recipe.created_at,
            'updated_at': recipe.updated_at
        }
    
    # --- START: Moved and Updated Import helper methods ---
    def _import_resources_data(self, resources_data: List[Dict], merge_strategy: str) -> None:
        """Import resources data using specified merge strategy."""
        for resource_data in resources_data:
            try:
                resource_name = resource_data.get('name')
                if not resource_name:
                    logger.warning(f"Skipping resource import due to missing name: {resource_data}")
                    continue

                existing_resource = get_resource_by_name(self.db_path, resource_name)

                if existing_resource:
                    if existing_resource.id is None: # Check if ID is None
                        logger.warning(f"Skipping update for resource '{resource_name}' due to missing ID in existing record.")
                        continue

                    if merge_strategy == 'update':
                        logger.info(f"Updating existing resource: {resource_name}")
                        update_payload = {k: v for k, v in resource_data.items() if k not in ['id', 'name', 'created_at', 'updated_at']}
                        update_resource(
                            db_path=self.db_path,
                            resource_id=existing_resource.id, 
                            **update_payload
                        )
                    elif merge_strategy == 'replace':
                        logger.info(f"Replacing existing resource: {resource_name}")
                        # Delete the old resource
                        from app.data.crud import delete_resource # Local import to avoid circular dependency if any at module level
                        delete_resource(self.db_path, existing_resource.id)
                        # Create the new resource
                        create_payload = {k: v for k, v in resource_data.items() if k not in ['id', 'created_at', 'updated_at']}
                        create_resource(
                            db_path=self.db_path,
                            **create_payload
                        )
                    elif merge_strategy == 'skip':
                        logger.info(f"Skipping existing resource: {resource_name}")
                        continue 
                else: # Resource does not exist, create it
                    logger.info(f"Creating new resource: {resource_name}")
                    # Prepare data for create_resource, ensure all required fields are present
                    # 'name' is already confirmed.
                    create_payload = {k: v for k, v in resource_data.items() if k not in ['id', 'created_at', 'updated_at']}
                    create_resource(
                        db_path=self.db_path,
                        **create_payload
                    )
                    
            except Exception as e:
                logger.error(f"Failed to import resource {resource_data.get('name', 'Unknown')}: {e}")
    
    def _import_recipes_data(self, recipes_data: List[Dict], merge_strategy: str) -> None:
        """Import crafting recipes data using specified merge strategy."""
        for recipe_data in recipes_data:
            try:
                recipe_name = recipe_data.get('name')
                if not recipe_name:
                    logger.warning(f"Skipping recipe import due to missing name: {recipe_data}")
                    continue

                existing_recipe = get_crafting_recipe_by_name(self.db_path, recipe_name)
                
                parsed_ingredients = []
                ingredients_input = recipe_data.get('ingredients', [])
                if ingredients_input:
                    for ing_data in ingredients_input:
                        if isinstance(ing_data, RecipeIngredient):
                            parsed_ingredients.append(ing_data)
                        elif isinstance(ing_data, dict) and 'resource_id' in ing_data and 'quantity' in ing_data:
                            if ing_data['resource_id'] is not None:
                                parsed_ingredients.append(RecipeIngredient(**ing_data))
                            else:
                                logger.warning(f"Skipping ingredient with None resource_id for recipe '{recipe_name}': {ing_data}")
                        elif isinstance(ing_data, dict) and 'name' in ing_data and 'quantity' in ing_data:
                            resource = get_resource_by_name(self.db_path, ing_data['name'])
                            if resource and resource.id is not None: 
                                parsed_ingredients.append(RecipeIngredient(resource_id=resource.id, quantity=ing_data['quantity']))
                            else:
                                logger.warning(f"Ingredient resource '{ing_data['name']}' not found or has no ID for recipe '{recipe_name}'. Skipping ingredient.")
                        else:
                            logger.warning(f"Invalid ingredient format for recipe '{recipe_name}': {ing_data}")

                if existing_recipe:
                    if existing_recipe.id is None: 
                        logger.warning(f"Skipping update for recipe '{recipe_name}' due to missing ID in existing record.")
                        continue
                        
                    if merge_strategy == 'update':
                        logger.info(f"Updating existing recipe: {recipe_name}")
                        update_payload = {k: v for k, v in recipe_data.items() if k not in ['id', 'name', 'created_at', 'updated_at', 'ingredients']}
                        update_crafting_recipe(
                            db_path=self.db_path,
                            recipe_id=existing_recipe.id,
                            ingredients=parsed_ingredients,
                            **update_payload
                        )
                    elif merge_strategy == 'replace':
                        logger.info(f"Replacing existing recipe: {recipe_name}")
                        # Delete the old recipe
                        from app.data.crud import delete_crafting_recipe # Local import
                        delete_crafting_recipe(self.db_path, existing_recipe.id)
                        # Create the new recipe
                        create_payload = {k: v for k, v in recipe_data.items() if k not in ['id', 'created_at', 'updated_at', 'ingredients']}
                        if 'name' not in create_payload:
                            create_payload['name'] = recipe_name
                        if 'output_item_name' not in create_payload or not create_payload['output_item_name']:
                            logger.warning(f"Recipe '{recipe_name}' missing 'output_item_name' during replace. Skipping creation.")
                            continue # Skip creating this specific recipe if essential info is missing for new one
                        create_crafting_recipe(
                            db_path=self.db_path,
                            ingredients=parsed_ingredients,
                            **create_payload
                        )
                    elif merge_strategy == 'skip':
                        logger.info(f"Skipping existing recipe: {recipe_name}")
                        continue
                else: # Recipe does not exist, create it
                    logger.info(f"Creating new recipe: {recipe_name}")
                    create_payload = {k: v for k, v in recipe_data.items() if k not in ['id', 'created_at', 'updated_at', 'ingredients']}
                    if 'name' not in create_payload:
                        create_payload['name'] = recipe_name
                    if 'output_item_name' not in create_payload or not create_payload['output_item_name']:
                        logger.warning(f"Recipe '{recipe_name}' missing 'output_item_name'. Skipping creation.")
                        continue

                    create_crafting_recipe(
                        db_path=self.db_path,
                        ingredients=parsed_ingredients,
                        **create_payload
                    )

            except Exception as e:
                logger.error(f"Failed to import recipe {recipe_data.get('name', 'Unknown')}: {e}")
    # --- END: Moved and Updated Import helper methods ---

    # JSON Export/Import
    
    def _export_json(self, data: Dict[str, Any], export_path: Path) -> bool:
        """Export data as JSON file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Data exported to JSON: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return False
    
    def _import_json(self, import_path: Path, merge_strategy: str) -> bool:
        """Import data from JSON file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'resources' in data:
                self._import_resources_data(data['resources'], merge_strategy)
            
            if 'crafting_recipes' in data:
                self._import_recipes_data(data['crafting_recipes'], merge_strategy)
            
            logger.info(f"Data imported from JSON: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import JSON: {e}")
            return False
    
    # Markdown Export/Import
    
    def _export_markdown(self, data: Dict[str, Any], export_path: Path) -> bool:
        """Export data as Markdown file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# Dune Companion Data Export\n\n")
                
                if 'metadata' in data:
                    f.write("## Export Information\n\n")
                    metadata = data['metadata']
                    f.write(f"- **Export Date:** {metadata.get('export_date', 'Unknown')}\n")
                    f.write(f"- **App Version:** {metadata.get('app_version', 'Unknown')}\n")
                    f.write(f"- **Total Resources:** {metadata.get('total_resources', 0)}\n")
                    f.write(f"- **Total Recipes:** {metadata.get('total_recipes', 0)}\n\n")
                
                # Write resources
                if 'resources' in data and data['resources']:
                    f.write("## Resources\n\n")
                    for resource in data['resources']:
                        f.write(f"### {resource['name']}\n")
                        f.write(f"- **Category:** {resource.get('category', 'Unknown')}\n")
                        f.write(f"- **Rarity:** {resource.get('rarity', 'Unknown')}\n")
                        if resource.get('description'):
                            f.write(f"- **Description:** {resource['description']}\n")
                        if resource.get('source_locations'):
                            f.write(f"- **Source Locations:** {resource['source_locations']}\n")
                        f.write("\n")
                
                # Write crafting recipes
                if 'crafting_recipes' in data and data['crafting_recipes']:
                    f.write("## Crafting Recipes\n\n")
                    for recipe in data['crafting_recipes']:
                        f.write(f"### {recipe['name']}\n")
                        f.write(f"- **Output:** {recipe.get('output_quantity', 1)}x {recipe.get('output_item_name', 'Unknown')}\n")
                        if recipe.get('required_station'):
                            f.write(f"- **Station:** {recipe['required_station']}\n")
                        if recipe.get('crafting_time_seconds'):
                            f.write(f"- **Time:** {recipe['crafting_time_seconds']} seconds\n")
                        if recipe.get('skill_requirement'):
                            f.write(f"- **Skill Required:** {recipe['skill_requirement']}\n")
                        if recipe.get('description'):
                            f.write(f"- **Description:** {recipe['description']}\n")
                        f.write("\n")
            
            logger.info(f"Data exported to Markdown: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Markdown: {e}")
            return False
    
    def _import_markdown(self, import_path: Path, merge_strategy: str) -> bool:
        """Import data from a structured Markdown file."""
        logger.info(f"Attempting to import Markdown data from: {import_path}")
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            resources_data = []
            recipes_data = []
            
            current_section = None
            current_item: Optional[Dict[str, Any]] = None

            for line in content.splitlines():
                line = line.strip()
                if not line: # Skip empty lines
                    continue

                if line.startswith("## Resources"):
                    current_section = "resources"
                    if current_item: # Save previous item if any
                        # This case implies we were in a recipe section and found a new Resource section header
                        # which is unusual for the expected format but handling defensively.
                        if current_section == "recipes": # This condition will actually be false due to line above
                            recipes_data.append(current_item) # So this line is unlikely to be hit.
                    current_item = None
                    continue
                elif line.startswith("## Crafting Recipes"):
                    if current_item and current_section == "resources": # Save last resource item before switching
                        resources_data.append(current_item)
                    current_section = "recipes"
                    current_item = None
                    continue
                elif line.startswith("### "):
                    if current_item:
                        if current_section == "resources":
                            resources_data.append(current_item)
                        elif current_section == "recipes":
                            recipes_data.append(current_item)
                    
                    item_name = line[4:].strip()
                    current_item = {"name": item_name}
                    if current_section == "resources" and current_item is not None:
                        current_item['category'] = None # Initialize category for resources
                    if current_section == "recipes" and current_item is not None:
                        current_item['ingredients'] = [] 
                        current_item['category'] = None # Initialize category for recipes
                    continue

                elif line.startswith("- ") and current_item is not None:
                    try:
                        line_content_after_dash = line[2:]
                        colon_idx = line_content_after_dash.find(':')
                        
                        if colon_idx == -1:
                            logger.warning(f"Malformed key-value line (no colon found): {line}")
                            continue

                        raw_key_part = line_content_after_dash[:colon_idx]
                        value_part = line_content_after_dash[colon_idx+1:].strip()

                        processed_key = raw_key_part.strip()

                        if processed_key.endswith(':'):
                            processed_key = processed_key[:-1]
                        
                        if processed_key.startswith('**') and processed_key.endswith('**') and len(processed_key) >= 4:
                            processed_key = processed_key[2:-2]
                        elif processed_key.startswith('*') and processed_key.endswith('*') and len(processed_key) >= 2:
                            processed_key = processed_key[1:-1]
                        
                        final_key = processed_key.strip().lower().replace(' ', '_')
                        
                        value = value_part

                        if not final_key:
                            logger.warning(f"Empty key after processing line: {line} (processed_key was: '{processed_key}')")
                            continue
                        
                        if current_section == "resources":
                            if final_key == 'category':
                                current_item['category'] = value
                            elif final_key == 'rarity':
                                current_item['rarity'] = value
                            elif final_key == 'description':
                                current_item['description'] = value
                            elif final_key == 'source_locations':
                                current_item['source_locations'] = value
                            elif final_key == 'icon_path':
                                current_item['icon_path'] = value
                            elif final_key == 'name': # Name is already set from ###, but allow override if explicitly listed
                                current_item['name'] = value
                            elif final_key == 'discovered':
                                current_item['discovered'] = int(value) if value.isdigit() else 0
                            # Add other resource fields as needed, with type conversion

                        elif current_section == "recipes":
                            if final_key == "output": 
                                parts = value.split('x', 1)
                                if len(parts) == 2 and parts[0].strip().isdigit():
                                    current_item['output_quantity'] = int(parts[0].strip())
                                    current_item['output_item_name'] = parts[1].strip()
                                else:
                                    current_item['output_item_name'] = value 
                                    current_item['output_quantity'] = 1
                            elif final_key == "station":
                                current_item['required_station'] = value
                            elif final_key == "time": 
                                time_val = value.split()[0]
                                current_item['crafting_time_seconds'] = int(time_val) if time_val.isdigit() else 0
                            elif final_key == "description":
                                current_item['description'] = value
                            elif final_key == "category":
                                current_item['category'] = value
                            elif final_key == "skill_required" or final_key == "skill_requirement":
                                current_item['skill_requirement'] = value
                            elif final_key == "icon_path":
                                current_item['icon_path'] = value
                            elif final_key == 'discovered':
                                current_item['discovered'] = int(value) if value.isdigit() else 0
                            elif final_key == "ingredient" or final_key == "ingredients":
                                # Improved ingredient parsing: expects "- Ingredient: 2x Iron Ingot" or "- Ingredients: 2x Iron Ingot"
                                # or "- Ingredient: Spice" (implies quantity 1)
                                ing_parts = value.split('x', 1)
                                ing_qty = 1
                                ing_name = ''
                                if len(ing_parts) == 2 and ing_parts[0].strip().isdigit():
                                    ing_qty = int(ing_parts[0].strip())
                                    ing_name = ing_parts[1].strip()
                                elif len(ing_parts) == 1:
                                    ing_name = ing_parts[0].strip()
                                else:
                                    logger.warning(f"Could not parse ingredient line format: {line} for recipe {current_item.get('name')}")
                                    continue
                                
                                if ing_name:
                                    # Ensure 'ingredients' list exists, which it should if current_section is "recipes"
                                    if 'ingredients' not in current_item:
                                        current_item['ingredients'] = []
                                    current_item['ingredients'].append({"name": ing_name, "quantity": ing_qty})
                                else:
                                    logger.warning(f"Empty ingredient name from line: {line} for recipe {current_item.get('name')}")
                            # Add other recipe fields with type conversion
                    except ValueError as ve:
                        logger.warning(f"Skipping line due to ValueError: '{line}'. Error: {ve}")
                    except Exception as e:
                        logger.warning(f"Skipping line due to parsing error: '{line}'. Error: {e}")
            
            # Add the last item being processed
            if current_item:
                if current_section == "resources":
                    resources_data.append(current_item)
                elif current_section == "recipes":
                    recipes_data.append(current_item)

            if not resources_data and not recipes_data:
                logger.warning(f"No data parsed from Markdown file: {import_path}")
                return False

            if resources_data:
                logger.info(f"Parsed {len(resources_data)} resources from Markdown.")
                self._import_resources_data(resources_data, merge_strategy)
            
            if recipes_data:
                logger.info(f"Parsed {len(recipes_data)} recipes from Markdown.")
                self._import_recipes_data(recipes_data, merge_strategy)
            
            logger.info(f"Data imported from Markdown: {import_path}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Markdown import file not found: {import_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to import Markdown: {e}", exc_info=True)
            return False
    
    def _export_resources_markdown(self, resources: List[Resource], export_path: Path) -> bool:
        """Export resources as Markdown file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("# Dune Companion Resources Export\n\n")
                for resource in resources:
                    f.write(f"## {resource.name}\n")
                    f.write(f"- **Category:** {resource.category}\n")
                    f.write(f"- **Rarity:** {resource.rarity}\n")
                    f.write(f"- **Source Locations:** {getattr(resource, 'source_locations', '')}\n")
                    if resource.description:
                        f.write(f"- **Description:** {resource.description}\n")
                    f.write("\n")
            logger.info(f"Resources exported to Markdown: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export resources to Markdown: {e}")
            return False
    
    # CSV Export/Import
    
    def _export_csv(self, data: Dict[str, Any], export_path: Path) -> bool:
        """Export data as separate CSV files in a directory."""
        try:
            # Create directory for CSV files
            csv_dir = export_path.with_suffix('')
            csv_dir.mkdir(parents=True, exist_ok=True)
            
            # Export resources
            if 'resources' in data and data['resources']:
                resources_path = csv_dir / 'resources.csv'
                self._write_resources_csv(data['resources'], resources_path)
              # Export crafting recipes
            if 'crafting_recipes' in data and data['crafting_recipes']:
                recipes_path = csv_dir / 'crafting_recipes.csv'
                self._write_recipes_csv(data['crafting_recipes'], recipes_path)
            
            logger.info(f"Data exported to CSV directory: {csv_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False
    
    def _write_resources_csv(self, resources: List[Dict], file_path: Path) -> None:
        """Write resources data to CSV file."""
        fieldnames = ['id', 'name', 'category', 'rarity', 'description', 'source_locations', 
                     'icon_path', 'discovered', 'created_at', 'updated_at']
        
        # Filter data to only include fieldnames to avoid CSV writer issues
        filtered_resources = []
        for resource in resources:
            filtered_resource = {field: resource.get(field, '') for field in fieldnames}
            filtered_resources.append(filtered_resource)
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_resources)
    
    def _write_recipes_csv(self, recipes: List[Dict], file_path: Path) -> None:
        """Write crafting recipes data to CSV file."""
        fieldnames = ['id', 'name', 'category', 'description', 'output_item_name', 'output_quantity', 
                     'crafting_time_seconds', 'required_station', 'skill_requirement', 
                     'icon_path', 'discovered', 'ingredients', 'created_at', 'updated_at']
        
        # Filter data to only include fieldnames to avoid CSV writer issues
        filtered_recipes = []
        for recipe in recipes:
            filtered_recipe = {field: recipe.get(field, '') for field in fieldnames}
            filtered_recipes.append(filtered_recipe)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_recipes)

    def _export_resources_csv(self, resources: List[Resource], export_path: Path) -> bool:
        """Export resources as CSV file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            resources_data = [self._resource_to_dict(r) for r in resources]
            self._write_resources_csv(resources_data, export_path)
            logger.info(f"Resources exported to CSV: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export resources to CSV: {e}")
            return False

    def _export_recipes_csv(self, recipes: List[CraftingRecipe], export_path: Path) -> bool:
        """Export crafting recipes as CSV file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            recipes_data = [self._recipe_to_dict(r) for r in recipes]
            self._write_recipes_csv(recipes_data, export_path)
            logger.info(f"Crafting recipes exported to CSV: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export recipes to CSV: {e}")
            return False

    def _export_recipes_markdown(self, recipes: List[CraftingRecipe], export_path: Path) -> bool:
        """Export crafting recipes as Markdown file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("# Dune Companion Crafting Recipes Export\n\n")
                for recipe in recipes:
                    f.write(f"## {recipe.name}\n")
                    f.write(f"- **Output:** {recipe.output_quantity}x {recipe.output_item_name}\n")
                    f.write(f"- **Station:** {recipe.required_station}\n")
                    f.write(f"- **Time:** {recipe.crafting_time_seconds} seconds\n")
                    f.write(f"- **Skill Required:** {recipe.skill_requirement}\n")
                    if recipe.description:
                        f.write(f"- **Description:** {recipe.description}\n")
                    f.write("\n")
            logger.info(f"Crafting recipes exported to Markdown: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export recipes to Markdown: {e}")
            return False
    
    def _import_csv(self, import_path: Path, merge_strategy: str) -> bool:
        """Import data from CSV files within a specified directory."""
        logger.info(f"Attempting to import CSV data from directory: {import_path}")
        if not import_path.is_dir():
            logger.error(f"CSV import path must be a directory: {import_path}")
            return False

        resources_file = import_path / 'resources.csv'
        recipes_file = import_path / 'crafting_recipes.csv'

        imported_something = False
        overall_success = True # Track if any individual import step fails

        if resources_file.exists():
            try:
                with open(resources_file, 'r', encoding='utf-8', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    resources_data = []
                    for row in reader:
                        # Basic type conversion - can be expanded
                        row['discovered'] = int(row.get('discovered', 0)) if row.get('discovered') else 0
                        if 'id' in row: # remove id from dict as create_resource does not take it
                            del row['id']
                        resources_data.append(row)
                
                if resources_data:
                    self._import_resources_data(resources_data, merge_strategy)
                    logger.info(f"Successfully processed resources from {resources_file}")
                    imported_something = True
                else:
                    logger.info(f"No data found in {resources_file}")

            except Exception as e:
                logger.error(f"Failed to import resources from CSV {resources_file}: {e}")
                overall_success = False # Mark as failed but continue to recipes
        else:
            logger.warning(f"Resources CSV file not found: {resources_file}")

        if recipes_file.exists():
            try:
                with open(recipes_file, 'r', encoding='utf-8', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    recipes_data = []
                    for row in reader:
                        # Basic type conversion
                        row['output_quantity'] = int(row.get('output_quantity', 1)) if row.get('output_quantity') else 1
                        row['crafting_time_seconds'] = int(row.get('crafting_time_seconds', 0)) if row.get('crafting_time_seconds') else 0
                        row['discovered'] = int(row.get('discovered', 0)) if row.get('discovered') else 0
                        
                        ingredients_str = row.get('ingredients')
                        if ingredients_str:
                            try:
                                # Ensure ingredients are parsed correctly, especially if they are simple lists of dicts
                                ingredients_parsed = json.loads(ingredients_str)
                                # The create_crafting_recipe expects a list of RecipeIngredient objects or dicts
                                # that can be converted. If CSV stores them as dicts, this should be fine.
                                row['ingredients'] = ingredients_parsed
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse ingredients JSON for recipe {row.get('name')}: {ingredients_str}")
                                row['ingredients'] = [] 
                        else:
                            row['ingredients'] = []
                        
                        if 'id' in row: 
                            del row['id']
                        recipes_data.append(row)

                if recipes_data:
                    self._import_recipes_data(recipes_data, merge_strategy)
                    logger.info(f"Successfully processed recipes from {recipes_file}")
                    imported_something = True
                else:
                    logger.info(f"No data found in {recipes_file}")

            except Exception as e:
                logger.error(f"Failed to import recipes from CSV {recipes_file}: {e}")
                overall_success = False
        else:
            logger.warning(f"Crafting recipes CSV file not found: {recipes_file}")
        
        if not imported_something and overall_success: # if nothing was imported but no errors occurred
            logger.info(f"No new data to import from CSV files in {import_path}")
            # Return True because the operation completed without error, even if no data changed.
            # If it's preferred to return False if no files were found/processed, adjust this logic.
            return True 

        return overall_success and imported_something
    
    # Import helper methods
