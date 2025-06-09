#!/usr/bin/env python3
"""
Tests for the Import/Export Service.

This module contains comprehensive tests for importing and exporting
Dune Companion data in various formats.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.import_export_service import ImportExportService, export_all_data, import_data


class TestImportExportService:
    """Test cases for the ImportExportService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImportExportService()
        
        # Sample test data
        self.sample_resource = {
            'id': 1,
            'name': 'Spice',
            'category': 'Material',
            'rarity': 'Legendary',
            'description': 'The spice must flow',
            'source_locations': 'Arrakis',
            'created_at': '2025-06-08T10:00:00',
            'updated_at': '2025-06-08T10:00:00'
        }
        
        self.sample_recipe = {
            'id': 1,
            'name': 'Stillsuit',
            'description': 'Water recycling suit',
            'output_item_name': 'Stillsuit',
            'output_quantity': 1,
            'required_station': 'Fabricator',
            'crafting_time_seconds': 300,
            'ingredients': [],
            'created_at': '2025-06-08T10:00:00',
            'updated_at': '2025-06-08T10:00:00'
        }

    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        assert self.service.supported_formats == ['json', 'markdown', 'csv']
        assert isinstance(self.service, ImportExportService)
    
    @patch('app.services.import_export_service.get_all_resources')
    @patch('app.services.import_export_service.get_all_crafting_recipes')
    def test_get_all_data(self, mock_recipes, mock_resources):
        """Test getting all data from database."""
        # Mock database responses
        mock_resource = MagicMock()
        mock_resource.id = 1
        mock_resource.name = 'Spice'
        mock_resource.category = 'Material'
        mock_resource.rarity = 'Legendary'
        mock_resource.description = 'The spice must flow'
        mock_resource.source_locations = 'Arrakis'
        mock_resource.icon_path = None
        mock_resource.discovered = 1
        mock_resource.created_at = None
        mock_resource.updated_at = None
        
        mock_recipe = MagicMock()
        mock_recipe.id = 1
        mock_recipe.name = 'Stillsuit'
        mock_recipe.description = 'Water recycling suit'
        mock_recipe.output_item_name = 'Stillsuit'
        mock_recipe.output_quantity = 1
        mock_recipe.crafting_time_seconds = 300
        mock_recipe.required_station = 'Fabricator'
        mock_recipe.skill_requirement = None
        mock_recipe.icon_path = None
        mock_recipe.discovered = 1
        mock_recipe.ingredients = []
        mock_recipe.created_at = None
        mock_recipe.updated_at = None
        
        mock_resources.return_value = [mock_resource]
        mock_recipes.return_value = [mock_recipe]
        
        data = self.service._get_all_data()
        
        assert 'metadata' in data
        assert 'resources' in data
        assert 'crafting_recipes' in data
        assert len(data['resources']) == 1
        assert len(data['crafting_recipes']) == 1
        assert data['resources'][0]['name'] == 'Spice'
        assert data['crafting_recipes'][0]['name'] == 'Stillsuit'

    def test_resource_to_dict(self):
        """Test converting Resource object to dictionary."""
        resource = MagicMock()
        resource.id = 1
        resource.name = 'Spice'
        resource.category = 'Material'
        resource.rarity = 'Legendary'
        resource.description = 'The spice must flow'
        resource.source_locations = 'Arrakis'
        resource.icon_path = None
        resource.discovered = 1
        resource.created_at = None
        resource.updated_at = None
        
        result = self.service._resource_to_dict(resource)
        
        assert result['id'] == 1
        assert result['name'] == 'Spice'
        assert result['category'] == 'Material'
        assert result['rarity'] == 'Legendary'
        assert result['description'] == 'The spice must flow'
        assert result['source_locations'] == 'Arrakis'

    def test_recipe_to_dict(self):
        """Test converting CraftingRecipe object to dictionary."""
        recipe = MagicMock()
        recipe.id = 1
        recipe.name = 'Stillsuit'
        recipe.description = 'Water recycling suit'
        recipe.output_item_name = 'Stillsuit'
        recipe.output_quantity = 1
        recipe.crafting_time_seconds = 300
        recipe.required_station = 'Fabricator'
        recipe.skill_requirement = None
        recipe.icon_path = None
        recipe.discovered = 1
        recipe.ingredients = []
        recipe.created_at = None
        recipe.updated_at = None
        
        result = self.service._recipe_to_dict(recipe)
        
        assert result['id'] == 1
        assert result['name'] == 'Stillsuit'
        assert result['description'] == 'Water recycling suit'
        assert result['output_item_name'] == 'Stillsuit'
        assert result['output_quantity'] == 1
        assert result['crafting_time_seconds'] == 300
        assert result['required_station'] == 'Fabricator'

    def test_export_json(self):
        """Test exporting data to JSON format."""
        test_data = {
            'metadata': {'export_date': '2025-06-08T10:00:00'},
            'resources': [self.sample_resource],
            'crafting_recipes': [self.sample_recipe]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'test_export.json'
            result = self.service._export_json(test_data, export_path)
            
            assert result is True
            assert export_path.exists()
            
            # Verify JSON content
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert exported_data['metadata']['export_date'] == '2025-06-08T10:00:00'
            assert len(exported_data['resources']) == 1
            assert exported_data['resources'][0]['name'] == 'Spice'

    def test_export_markdown(self):
        """Test exporting data to Markdown format."""
        test_data = {
            'metadata': {
                'export_date': '2025-06-08T10:00:00',
                'app_version': '0.1.0'
            },
            'resources': [self.sample_resource],
            'crafting_recipes': [self.sample_recipe]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'test_export.md'
            result = self.service._export_markdown(test_data, export_path)
            
            assert result is True
            assert export_path.exists()
            
            # Check that file contains expected content
            content = export_path.read_text(encoding='utf-8')
            assert 'Dune Companion Data Export' in content
            assert 'Spice' in content
            assert 'Stillsuit' in content

    def test_export_csv(self):
        """Test exporting data to CSV format."""
        test_data = {
            'resources': [self.sample_resource],
            'crafting_recipes': [self.sample_recipe]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'test_export.csv'
            result = self.service._export_csv(test_data, export_path)
            
            assert result is True
            
            # Check that CSV directory was created
            csv_dir = export_path.with_suffix('')
            assert csv_dir.exists()
            assert (csv_dir / 'resources.csv').exists()
            assert (csv_dir / 'crafting_recipes.csv').exists()

    def test_import_json(self):
        """Test importing data from JSON format."""
        test_data = {
            'metadata': {'export_date': '2025-06-08T10:00:00'},
            'resources': [self.sample_resource],
            'crafting_recipes': [self.sample_recipe]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / 'test_import.json'
            
            # Create test JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            # Test import (this will require mocking CRUD operations)
            with patch('app.services.import_export_service.create_resource') as mock_create_resource, \
                 patch('app.services.import_export_service.create_crafting_recipe') as mock_create_recipe:
                
                result = self.service.import_data(json_path, 'json')
                assert result is True

    def test_export_all_data_json(self):
        """Test exporting all data to JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch.object(self.service, '_get_all_data') as mock_get_data:
            
            mock_get_data.return_value = {
                'metadata': {'export_date': '2025-06-08T10:00:00'},
                'resources': [self.sample_resource],
                'crafting_recipes': [self.sample_recipe]
            }
            
            export_path = Path(temp_dir) / 'all_data.json'
            result = self.service.export_all_data(export_path, 'json')
            
            assert result is True
            assert export_path.exists()

    def test_export_resources_only(self):
        """Test exporting only resources."""
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch('app.services.import_export_service.get_all_resources') as mock_resources:
            
            mock_resource = MagicMock()
            mock_resource.id = 1
            mock_resource.name = 'Spice'
            mock_resource.category = 'Material'
            mock_resource.rarity = 'Legendary'
            mock_resource.description = 'The spice must flow'
            mock_resource.source_locations = 'Arrakis'
            mock_resource.icon_path = None
            mock_resource.discovered = 1
            mock_resource.created_at = None
            mock_resource.updated_at = None
            
            mock_resources.return_value = [mock_resource]
            
            export_path = Path(temp_dir) / 'resources_only.json'
            result = self.service.export_resources(export_path, 'json')
            
            assert result is True
            assert export_path.exists()

    def test_export_recipes_only(self):
        """Test exporting only crafting recipes."""
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch('app.services.import_export_service.get_all_crafting_recipes') as mock_recipes:
            
            mock_recipe = MagicMock()
            mock_recipe.id = 1
            mock_recipe.name = 'Stillsuit'
            mock_recipe.description = 'Water recycling suit'
            mock_recipe.output_item_name = 'Stillsuit'
            mock_recipe.output_quantity = 1
            mock_recipe.crafting_time_seconds = 300
            mock_recipe.required_station = 'Fabricator'
            mock_recipe.skill_requirement = None
            mock_recipe.icon_path = None
            mock_recipe.discovered = 1
            mock_recipe.ingredients = []
            mock_recipe.created_at = None
            mock_recipe.updated_at = None
            
            mock_recipes.return_value = [mock_recipe]
            
            export_path = Path(temp_dir) / 'recipes_only.json'
            result = self.service.export_crafting_recipes(export_path, 'json')
            
            assert result is True
            assert export_path.exists()

    def test_unsupported_export_format(self):
        """Test exporting with unsupported format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'test_export.xml'
            result = self.service.export_all_data(export_path, 'xml')
            
            assert result is False

    def test_import_nonexistent_file(self):
        """Test importing from nonexistent file."""
        nonexistent_path = Path('nonexistent_file.json')
        result = self.service.import_data(nonexistent_path, 'json')
        
        assert result is False

    def test_import_unsupported_format(self):
        """Test importing with unsupported format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / 'test.xml'
            xml_path.write_text('<data></data>')
            
            result = self.service.import_data(xml_path, 'xml')
            assert result is False


class TestConvenienceFunctions:
    """Test the module-level convenience functions."""

    def test_export_all_data_function(self):
        """Test the export_all_data convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch('app.services.import_export_service.ImportExportService') as mock_service_class:
            
            mock_service = MagicMock()
            mock_service.export_all_data.return_value = True
            mock_service_class.return_value = mock_service
            
            export_path = Path(temp_dir) / 'test_export.json'
            result = export_all_data(export_path, 'json')
            
            assert result is True
            mock_service.export_all_data.assert_called_once_with(export_path, 'json')

    def test_import_data_function(self):
        """Test the import_data convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch('app.services.import_export_service.ImportExportService') as mock_service_class:
            
            mock_service = MagicMock()
            mock_service.import_data.return_value = True
            mock_service_class.return_value = mock_service
            
            import_path = Path(temp_dir) / 'test_import.json'
            import_path.write_text('{}')
            
            result = import_data(import_path, 'json')
            
            assert result is True
            mock_service.import_data.assert_called_once_with(import_path, 'json', 'update')
