#!/usr/bin/env python3
"""
Import/Export Service for Dune Companion PC App.

This module provides functionality to import and export data in various formats
including JSON, Markdown, and CSV. It handles resources, crafting recipes,
and other game data for backup, sharing, and migration purposes.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Any, Optional

from app.data.database import get_default_db_path
from app.data.crud import (
    get_all_resources, get_all_crafting_recipes
)
from app.data.models import Resource, CraftingRecipe
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
                # If format_type is not recognized, return False
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
                self._write_resources_csv([self._resource_to_dict(r) for r in resources], export_path)
                logger.info(f"Resources exported to CSV: {export_path}")
                return True
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
    
    def import_data(self, import_path: Path, format_type: str = 'json', 
                   merge_strategy: str = 'update') -> bool:
        """
        Import data from the specified file.
        
        Args:
            import_path: Path to the file to import
            format_type: Format of the file ('json', 'csv')
            merge_strategy: How to handle existing data ('update', 'replace', 'skip')
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            if not import_path.exists():
                raise FileNotFoundError(f"Import file not found: {import_path}")
            
            if format_type == 'json':
                return self._import_json(import_path, merge_strategy)
            elif format_type == 'csv':
                return self._import_csv(import_path, merge_strategy)
            else:
                raise ValueError(f"Import not supported for format: {format_type}")
                
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            return False
    
    # Private helper methods
    
    def _get_all_data(self) -> Dict[str, Any]:
        """Get all data from the database."""
        resources = get_all_resources(self.db_path)
        recipes = get_all_crafting_recipes(self.db_path)
        
        return {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'app_version': '0.1.0',
                'format_version': '1.0'
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
    
    # JSON Export/Import
    
    def _export_json(self, data: Dict[str, Any], export_path: Path) -> bool:
        """Export data as JSON file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
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
            
            # Import resources if present
            if 'resources' in data:
                self._import_resources_data(data['resources'], merge_strategy)
            
            # Import crafting recipes if present
            if 'crafting_recipes' in data:
                self._import_recipes_data(data['crafting_recipes'], merge_strategy)
            
            logger.info(f"Data imported from JSON: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import JSON: {e}")
            return False
    
    # CSV Import

    def _import_csv(self, import_path: Path, merge_strategy: str) -> bool:
        """
        Import data from a CSV file.
        This implementation assumes the CSV file is for resources or crafting recipes,
        based on the filename.
        """
        try:
            if "resource" in import_path.name:
                with open(import_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    resources_data = [row for row in reader]
                self._import_resources_data(resources_data, merge_strategy)
                logger.info(f"Resources imported from CSV: {import_path}")
                return True
            elif "recipe" in import_path.name:
                with open(import_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    recipes_data = [row for row in reader]
                self._import_recipes_data(recipes_data, merge_strategy)
                logger.info(f"Crafting recipes imported from CSV: {import_path}")
                return True
            else:
                logger.error(f"Unknown CSV import type for file: {import_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to import CSV: {e}")
            return False

    # Markdown Export
    
    def _export_markdown(self, data: Dict[str, Any], export_path: Path) -> bool:
        """Export data as Markdown file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("# Dune Companion Data Export\n\n")
                f.write(f"**Export Date:** {data['metadata']['export_date']}\n")
                f.write(f"**App Version:** {data['metadata']['app_version']}\n\n")
                
                # Export resources
                if data['resources']:
                    f.write("## Resources\n\n")
                    for resource in data['resources']:
                        f.write(f"### {resource['name']}\n")
                        f.write(f"- **Category:** {resource['category']}\n")
                        f.write(f"- **Rarity:** {resource['rarity']}\n")
                        f.write(f"- **Source Locations:** {resource['source_locations']}\n")
                        if resource['description']:
                            f.write(f"- **Description:** {resource['description']}\n")
                        f.write("\n")
                
                # Export crafting recipes
                if data['crafting_recipes']:
                    f.write("## Crafting Recipes\n\n")
                    for recipe in data['crafting_recipes']:
                        f.write(f"### {recipe['name']}\n")
                        f.write(f"- **Output:** {recipe['output_quantity']}x {recipe['output_item_name']}\n")
                        f.write(f"- **Station:** {recipe['required_station']}\n")
                        f.write(f"- **Time:** {recipe['crafting_time_seconds']} seconds\n")
                        f.write(f"- **Skill Required:** {recipe['skill_requirement']}\n")
                        if recipe['description']:
                            f.write(f"- **Description:** {recipe['description']}\n")
                        f.write("\n")
            
            logger.info(f"Data exported to Markdown: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Markdown: {e}")
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

    # CSV Export
    
    def _export_csv(self, data: Dict[str, Any], export_path: Path) -> bool:
        """Export data as separate CSV files in a directory."""
        try:
            # Create directory for CSV files
            csv_dir = export_path.with_suffix('')
            csv_dir.mkdir(parents=True, exist_ok=True)
            
            # Export resources
            if data['resources']:
                resources_path = csv_dir / 'resources.csv'
                self._write_resources_csv(data['resources'], resources_path)
            
            # Export crafting recipes
            if data['crafting_recipes']:
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
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(resources)
    
    def _write_recipes_csv(self, recipes: List[Dict], file_path: Path) -> None:
        """Write crafting recipes data to CSV file."""
        fieldnames = ['id', 'name', 'description', 'output_item_name', 'output_quantity', 
                     'crafting_time_seconds', 'required_station', 'skill_requirement', 
                     'icon_path', 'discovered', 'ingredients', 'created_at', 'updated_at']
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(recipes)

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
    
    # Import helper methods
    
    def _import_resources_data(self, resources_data: List[Dict], merge_strategy: str) -> None:
        """Import resources data into database."""
        from app.data.crud import create_resource, update_resource, get_resource_by_name
        
        for resource_dict in resources_data:
            try:
                existing = get_resource_by_name(self.db_path, resource_dict['name'])
                
                if existing:
                    if merge_strategy == 'update' and existing.id is not None:
                        # Update existing resource
                        update_resource(
                            self.db_path,
                            existing.id,
                            name=resource_dict.get('name'),
                            description=resource_dict.get('description'),
                            rarity=resource_dict.get('rarity'),
                            category=resource_dict.get('category'),
                            source_locations=resource_dict.get('source_locations'),
                            icon_path=resource_dict.get('icon_path'),
                            discovered=resource_dict.get('discovered', 0)
                        )
                        logger.debug(f"Updated resource: {resource_dict['name']}")
                    elif merge_strategy == 'skip':
                        # Skip existing resources
                        logger.debug(f"Skipped existing resource: {resource_dict['name']}")
                        continue
                else:
                    # Create new resource
                    create_resource(
                        self.db_path,
                        name=resource_dict['name'],
                        description=resource_dict.get('description'),
                        rarity=resource_dict.get('rarity'),
                        category=resource_dict.get('category'),
                        source_locations=resource_dict.get('source_locations'),
                        icon_path=resource_dict.get('icon_path'),
                        discovered=resource_dict.get('discovered', 0)
                    )
                    logger.debug(f"Created resource: {resource_dict['name']}")
                    
            except Exception as e:
                logger.error(f"Failed to import resource {resource_dict.get('name', 'unknown')}: {e}")

    def _import_recipes_data(self, recipes_data: List[Dict], merge_strategy: str) -> None:
        """Import crafting recipes data into database."""
        from app.data.crud import create_crafting_recipe, get_crafting_recipe_by_name
        
        for recipe_dict in recipes_data:
            try:
                existing = get_crafting_recipe_by_name(self.db_path, recipe_dict['name'])
                
                if existing:
                    if merge_strategy == 'update':
                        # For now, skip complex recipe updates since they require careful handling
                        logger.debug(f"Skipped update for existing recipe: {recipe_dict['name']}")
                    elif merge_strategy == 'skip':
                        # Skip existing recipes
                        logger.debug(f"Skipped existing recipe: {recipe_dict['name']}")
                        continue
                else:
                    # Create new recipe
                    create_crafting_recipe(
                        self.db_path,
                        name=recipe_dict['name'],
                        output_item_name=recipe_dict.get('output_item_name', ''),
                        output_quantity=recipe_dict.get('output_quantity', 1),
                        description=recipe_dict.get('description'),
                        crafting_time_seconds=recipe_dict.get('crafting_time_seconds'),
                        required_station=recipe_dict.get('required_station'),
                        skill_requirement=recipe_dict.get('skill_requirement'),
                        icon_path=recipe_dict.get('icon_path'),
                        discovered=recipe_dict.get('discovered', 0)
                    )
                    logger.debug(f"Created recipe: {recipe_dict['name']}")
                    
            except Exception as e:
                logger.error(f"Failed to import recipe {recipe_dict.get('name', 'unknown')}: {e}")


# Convenience functions for external use

def export_all_data(export_path: Union[str, Path], format_type: str = 'json') -> bool:
    """Convenience function to export all data."""
    service = ImportExportService()
    return service.export_all_data(Path(export_path), format_type)


def import_data(import_path: Union[str, Path], format_type: str = 'json', 
               merge_strategy: str = 'update') -> bool:
    """Convenience function to import data."""
    service = ImportExportService()
    return service.import_data(Path(import_path), format_type, merge_strategy)


def export_resources(export_path: Union[str, Path], format_type: str = 'json') -> bool:
    """Convenience function to export resources only."""
    service = ImportExportService()
    return service.export_resources(Path(export_path), format_type)


def export_crafting_recipes(export_path: Union[str, Path], format_type: str = 'json') -> bool:
    """Convenience function to export crafting recipes only."""
    service = ImportExportService()
    return service.export_crafting_recipes(Path(export_path), format_type)
