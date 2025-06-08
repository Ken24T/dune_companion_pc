#!/usr/bin/env python3
"""
Create test data for the Dune Companion PC App.

This script populates the database with sample resources and crafting recipes
for testing and demonstration purposes.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / 'app'
sys.path.insert(0, str(app_dir))

from app.data.database import get_default_db_path, initialize_database
from app.data.crud import (
    create_resource, create_crafting_recipe, get_all_resources, get_all_crafting_recipes
)
from app.data.models import RecipeIngredient
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_sample_resources(db_path: str) -> dict:
    """Create sample resources and return a mapping of names to resource objects."""
    logger.info("Creating sample resources...")
    
    resource_data = [
        # Basic Materials
        {"name": "Spice", "description": "The spice must flow. Essential resource for space travel.", 
         "category": "Material", "rarity": "Legendary", "discovered": 1},
        {"name": "Water", "description": "Precious water from underground reservoirs.", 
         "category": "Material", "rarity": "Rare", "discovered": 1},
        {"name": "Plasteel", "description": "Advanced composite material used in construction.", 
         "category": "Material", "rarity": "Common", "discovered": 1},
        {"name": "Ceramic Steel", "description": "Heat-resistant alloy perfect for harsh environments.", 
         "category": "Material", "rarity": "Uncommon", "discovered": 1},
        
        # Components
        {"name": "Power Cell", "description": "Portable energy storage device.", 
         "category": "Component", "rarity": "Common", "discovered": 1},
        {"name": "Circuit Board", "description": "Electronic component for advanced devices.", 
         "category": "Component", "rarity": "Uncommon", "discovered": 1},
        {"name": "Fiber Optics", "description": "High-speed data transmission cables.", 
         "category": "Component", "rarity": "Rare", "discovered": 1},
        
        # Tools & Equipment
        {"name": "Thumper", "description": "Device for attracting sandworms.", 
         "category": "Tool", "rarity": "Uncommon", "discovered": 1},
        {"name": "Stillsuit", "description": "Full-body suit that recycles body moisture.", 
         "category": "Equipment", "rarity": "Common", "discovered": 1},
        {"name": "Crysknife", "description": "Sacred blade made from sandworm tooth.", 
         "category": "Weapon", "rarity": "Legendary", "discovered": 0},
        
        # Currency & Trade
        {"name": "Solari", "description": "Standard currency of the Imperium.", 
         "category": "Currency", "rarity": "Common", "discovered": 1},
        {"name": "Hegemony Credits", "description": "Alternative currency used in some regions.", 
         "category": "Currency", "rarity": "Common", "discovered": 1},
        
        # Raw Materials
        {"name": "Sandworm Scales", "description": "Tough scales from mature sandworms.", 
         "category": "Material", "rarity": "Epic", "discovered": 0},
        {"name": "Spice Sand", "description": "Sand infused with trace amounts of melange.", 
         "category": "Material", "rarity": "Rare", "discovered": 1},
        {"name": "Metal Ore", "description": "Raw metal extracted from deep mines.", 
         "category": "Material", "rarity": "Common", "discovered": 1},
    ]
    
    created_resources = {}
    
    for resource_info in resource_data:
        try:
            resource = create_resource(
                db_path=db_path,
                name=resource_info["name"],
                description=resource_info["description"],
                category=resource_info["category"],
                rarity=resource_info["rarity"],
                discovered=resource_info["discovered"]
            )
            if resource:
                created_resources[resource.name] = resource
                logger.info(f"Created resource: {resource.name}")
            else:
                logger.warning(f"Failed to create resource: {resource_info['name']}")
        except Exception as e:
            logger.error(f"Error creating resource {resource_info['name']}: {e}")
    
    return created_resources


def create_sample_crafting_recipes(db_path: str, resources: dict) -> list:
    """Create sample crafting recipes using the provided resources."""
    logger.info("Creating sample crafting recipes...")
    
    recipes_data = [
        {
            "name": "Basic Stillsuit",
            "description": "Entry-level moisture preservation suit for desert survival.",
            "output_item_name": "Stillsuit",
            "output_quantity": 1,
            "crafting_time_seconds": 3600,  # 1 hour
            "required_station": "Fabricator",
            "skill_requirement": "Survival I",
            "discovered": 1,
            "ingredients": [
                {"resource_name": "Plasteel", "quantity": 5},
                {"resource_name": "Fiber Optics", "quantity": 2},
                {"resource_name": "Circuit Board", "quantity": 1}
            ]
        },
        {
            "name": "Advanced Power Cell",
            "description": "High-capacity energy storage with extended duration.",
            "output_item_name": "Enhanced Power Cell",
            "output_quantity": 1,
            "crafting_time_seconds": 1800,  # 30 minutes
            "required_station": "Electronics Bench",
            "skill_requirement": "Electronics II",
            "discovered": 1,
            "ingredients": [
                {"resource_name": "Power Cell", "quantity": 2},
                {"resource_name": "Circuit Board", "quantity": 1},
                {"resource_name": "Metal Ore", "quantity": 3}
            ]
        },
        {
            "name": "Portable Thumper",
            "description": "Compact sandworm attraction device for exploration.",
            "output_item_name": "Field Thumper",
            "output_quantity": 1,
            "crafting_time_seconds": 2700,  # 45 minutes
            "required_station": "Assembly Station",
            "skill_requirement": "Engineering I",
            "discovered": 1,
            "ingredients": [
                {"resource_name": "Plasteel", "quantity": 3},
                {"resource_name": "Power Cell", "quantity": 1},
                {"resource_name": "Metal Ore", "quantity": 4}
            ]
        },
        {
            "name": "Spice Processing Unit",
            "description": "Refines raw spice into concentrated melange.",
            "output_item_name": "Refined Spice",
            "output_quantity": 3,
            "crafting_time_seconds": 5400,  # 1.5 hours
            "required_station": "Chemical Lab",
            "skill_requirement": "Chemistry II",
            "discovered": 0,  # Advanced recipe
            "ingredients": [
                {"resource_name": "Spice", "quantity": 5},
                {"resource_name": "Spice Sand", "quantity": 10},
                {"resource_name": "Circuit Board", "quantity": 2}
            ]
        },
        {
            "name": "Desert Shelter Kit",
            "description": "Portable shelter components for desert survival.",
            "output_item_name": "Shelter Kit",
            "output_quantity": 1,
            "crafting_time_seconds": 4500,  # 1.25 hours
            "required_station": "Fabricator",
            "skill_requirement": "Construction I",
            "discovered": 1,
            "ingredients": [
                {"resource_name": "Plasteel", "quantity": 8},
                {"resource_name": "Ceramic Steel", "quantity": 4},
                {"resource_name": "Fiber Optics", "quantity": 3}
            ]
        }
    ]
    
    created_recipes = []
    
    for recipe_info in recipes_data:
        try:
            # Convert ingredient names to resource IDs
            ingredients = []
            for ing_info in recipe_info["ingredients"]:
                resource_name = ing_info["resource_name"]
                if resource_name in resources:
                    ingredients.append(RecipeIngredient(
                        resource_id=resources[resource_name].id,
                        quantity=ing_info["quantity"]
                    ))
                else:
                    logger.warning(f"Resource '{resource_name}' not found for recipe '{recipe_info['name']}'")
            
            if ingredients:  # Only create recipe if we have valid ingredients
                recipe = create_crafting_recipe(
                    db_path=db_path,
                    name=recipe_info["name"],
                    description=recipe_info["description"],
                    output_item_name=recipe_info["output_item_name"],
                    output_quantity=recipe_info["output_quantity"],
                    crafting_time_seconds=recipe_info["crafting_time_seconds"],
                    required_station=recipe_info["required_station"],
                    skill_requirement=recipe_info["skill_requirement"],
                    discovered=recipe_info["discovered"],
                    ingredients=ingredients
                )
                if recipe:
                    created_recipes.append(recipe)
                    logger.info(f"Created recipe: {recipe.name}")
                else:
                    logger.warning(f"Failed to create recipe: {recipe_info['name']}")
            else:
                logger.warning(f"No valid ingredients for recipe: {recipe_info['name']}")
                
        except Exception as e:
            logger.error(f"Error creating recipe {recipe_info['name']}: {e}")
    
    return created_recipes


def main():
    """Main function to create all test data."""
    logger.info("Starting test data creation...")
    
    try:
        # Get database path and ensure it's initialized
        db_path = get_default_db_path()
        logger.info(f"Using database: {db_path}")
        
        # Initialize database if needed
        if not os.path.exists(db_path):
            logger.info("Database not found, initializing...")
            initialize_database(db_path)
        
        # Create sample resources
        resources = create_sample_resources(db_path)
        logger.info(f"Created {len(resources)} resources")
        
        # Create sample crafting recipes
        recipes = create_sample_crafting_recipes(db_path, resources)
        logger.info(f"Created {len(recipes)} crafting recipes")
        
        # Print summary
        all_resources = get_all_resources(db_path)
        all_recipes = get_all_crafting_recipes(db_path)
        
        print(f"\n{'='*50}")
        print("TEST DATA CREATION SUMMARY")
        print(f"{'='*50}")
        print(f"Total Resources: {len(all_resources)}")
        print(f"Total Crafting Recipes: {len(all_recipes)}")
        print(f"Database: {db_path}")
        print(f"{'='*50}\n")
        
        logger.info("Test data creation completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create test data: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
