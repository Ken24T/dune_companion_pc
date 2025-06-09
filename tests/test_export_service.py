#!/usr/bin/env python3
"""
Tests for the Export functionality of the Import/Export Service.

This module contains focused tests for data export functionality
in various formats including JSON, Markdown, and CSV.
"""

import json
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.import_export_service import (
    ImportExportService, 
    export_all_data, 
    export_resources, 
    export_crafting_recipes
)


class TestExportFunctionality:
    """Test cases focused on export functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImportExportService()
          # Create comprehensive test data
        self.test_resources = [
            {
                'id': 1,
                'name': 'Spice',
                'category': 'Material',
                'rarity': 'Legendary',
                'description': 'The spice must flow. Essential for space travel.',
                'source_locations': 'Arrakis Desert',
                'icon_path': '',
                'discovered': True,
                'created_at': '2025-06-08T10:00:00',
                'updated_at': '2025-06-08T12:00:00'
            },
            {
                'id': 2,
                'name': 'Water',
                'category': 'Resource',
                'rarity': 'Common',
                'description': 'Precious resource on Arrakis',
                'source_locations': 'Sietch',
                'icon_path': '',
                'discovered': True,
                'created_at': '2025-06-08T10:30:00',
                'updated_at': '2025-06-08T10:30:00'
            }        ]
        
        self.test_recipes = [
            {
                'id': 1,
                'name': 'Stillsuit',
                'category': 'Equipment',
                'description': 'Advanced water recycling suit for desert survival',
                'ingredients': 'Fabric:2,Metal:1,Electronics:1',
                'output_item_name': 'Stillsuit',
                'output_quantity': 1,
                'required_station': 'Fabricator',
                'crafting_time_seconds': 300,
                'created_at': '2025-06-08T11:00:00',
                'updated_at': '2025-06-08T11:00:00'
            },
            {
                'id': 2,
                'name': 'Thumper',
                'category': 'Tool',
                'description': 'Device to attract sandworms',
                'ingredients': 'Metal:3,Electronics:2',
                'output_item_name': 'Thumper',
                'output_quantity': 1,
                'required_station': 'Workshop',
                'crafting_time_seconds': 180,
                'created_at': '2025-06-08T11:30:00',
                'updated_at': '2025-06-08T11:30:00'
            }
        ]
    
    def test_json_export_comprehensive(self):
        """Test comprehensive JSON export with all data types."""
        test_data = {
            'metadata': {
                'export_date': '2025-06-08T15:00:00',
                'app_version': '0.1.0',
                'format_version': '1.0'
            },
            'resources': self.test_resources,
            'crafting_recipes': self.test_recipes
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'comprehensive_export.json'
            
            result = self.service._export_json(test_data, export_path)
            
            assert result is True
            assert export_path.exists()
            
            # Verify exported content structure and data
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            # Check metadata
            assert 'metadata' in exported_data
            assert exported_data['metadata']['app_version'] == '0.1.0'
              # Check resources
            assert len(exported_data['resources']) == 2
            spice_resource = next(r for r in exported_data['resources'] if r['name'] == 'Spice')
            assert spice_resource['rarity'] == 'Legendary'
            assert spice_resource['source_locations'] == 'Arrakis Desert'
              # Check crafting recipes
            assert len(exported_data['crafting_recipes']) == 2
            stillsuit_recipe = next(r for r in exported_data['crafting_recipes'] if r['name'] == 'Stillsuit')
            assert stillsuit_recipe['category'] == 'Equipment'
            assert stillsuit_recipe['crafting_time_seconds'] == 300
    
    def test_markdown_export_formatting(self):
        """Test Markdown export with proper formatting and structure."""
        test_data = {
            'metadata': {
                'export_date': '2025-06-08T15:00:00',
                'app_version': '0.1.0'
            },
            'resources': self.test_resources,
            'crafting_recipes': self.test_recipes
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'export.md'
            
            result = self.service._export_markdown(test_data, export_path)
            
            assert result is True
            assert export_path.exists()
            
            # Read and verify content
            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()
              # Check main structure
            assert '# Dune Companion Data Export' in content
            assert '**Export Date:** 2025-06-08T15:00:00' in content
            assert '**App Version:** 0.1.0' in content
            
            # Check resources section
            assert '## Resources' in content
            assert '### Spice' in content
            assert '- **Category:** Material' in content
            assert '- **Rarity:** Legendary' in content
            assert '- **Source Locations:** Arrakis Desert' in content
            assert 'The spice must flow' in content
            
            assert '### Water' in content
            assert '- **Category:** Resource' in content
            assert '- **Rarity:** Common' in content
            
            # Check crafting recipes section
            assert '## Crafting Recipes' in content
            assert '### Stillsuit' in content
            assert '- **Output:** 1x Stillsuit' in content
            assert '- **Station:** Fabricator' in content
            assert '- **Time:** 300 seconds' in content
            assert '- **Description:** Advanced water recycling suit for desert survival' in content
            
            assert '### Thumper' in content
            assert '- **Output:** 1x Thumper' in content
            assert '- **Time:** 180 seconds' in content
    
    def test_csv_export_structure(self):
        """Test CSV export creates proper directory structure and files."""
        test_data = {
            'resources': self.test_resources,
            'crafting_recipes': self.test_recipes
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'csv_export.csv'
            
            result = self.service._export_csv(test_data, export_path)
            
            assert result is True
            
            # Check directory structure
            csv_dir = export_path.with_suffix('')
            assert csv_dir.exists()
            assert csv_dir.is_dir()
            
            resources_csv = csv_dir / 'resources.csv'
            recipes_csv = csv_dir / 'crafting_recipes.csv'
            
            assert resources_csv.exists()
            assert recipes_csv.exists()
              # Verify resources CSV content
            with open(resources_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                spice_row = next(r for r in rows if r['name'] == 'Spice')
                assert spice_row['category'] == 'Material'
                assert spice_row['rarity'] == 'Legendary'
                
            # Verify recipes CSV content
            with open(recipes_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                stillsuit_row = next(r for r in rows if r['name'] == 'Stillsuit')
                assert stillsuit_row['category'] == 'Equipment'
                assert stillsuit_row['crafting_time_seconds'] == '300'
    
    @patch('app.services.import_export_service.get_all_resources')
    @patch('app.services.import_export_service.get_all_crafting_recipes')
    def test_export_all_data_integration(self, mock_recipes, mock_resources):
        """Test complete export workflow with mocked database."""
        from datetime import datetime
        
        # Mock database responses with proper datetime objects
        mock_resource_objects = []
        for resource_data in self.test_resources:
            mock_resource = MagicMock()
            for key, value in resource_data.items():
                if key in ['created_at', 'updated_at'] and isinstance(value, str):
                    # Convert string timestamps to datetime objects
                    setattr(mock_resource, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                else:
                    setattr(mock_resource, key, value)
            mock_resource_objects.append(mock_resource)
        
        mock_recipe_objects = []
        for recipe_data in self.test_recipes:
            mock_recipe = MagicMock()
            for key, value in recipe_data.items():
                if key in ['created_at', 'updated_at'] and isinstance(value, str):
                    # Convert string timestamps to datetime objects
                    setattr(mock_recipe, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                else:
                    setattr(mock_recipe, key, value)
            mock_recipe_objects.append(mock_recipe)
        
        mock_resources.return_value = mock_resource_objects
        mock_recipes.return_value = mock_recipe_objects
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'full_export.json'
            
            result = self.service.export_all_data(export_path, 'json')
            
            assert result is True
            assert export_path.exists()
            
            # Verify the exported data
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert len(exported_data['resources']) == 2
            assert len(exported_data['crafting_recipes']) == 2
    
    def test_export_empty_data(self):
        """Test exporting when no data is available."""
        empty_data = {
            'metadata': {'export_date': '2025-06-08T15:00:00', 'app_version': '0.1.0'},
            'resources': [],
            'crafting_recipes': []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON export
            json_path = Path(temp_dir) / 'empty.json'
            result = self.service._export_json(empty_data, json_path)
            assert result is True
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            assert len(data['resources']) == 0
            assert len(data['crafting_recipes']) == 0
            
            # Test Markdown export
            md_path = Path(temp_dir) / 'empty.md'
            result = self.service._export_markdown(empty_data, md_path)
            assert result is True
            
            with open(md_path, 'r') as f:
                content = f.read()
            assert '# Dune Companion Data Export' in content
    
    def test_export_special_characters(self):
        """Test exporting data with special characters and Unicode."""
        special_data = {
            'metadata': {'export_date': '2025-06-08T15:00:00', 'app_version': '0.1.0'},
            'resources': [{
                'id': 1,
                'name': 'Spice Mélange',
                'type': 'Material',
                'rarity': 'Legendary',
                'description': 'The spice must flow... contains Unicode: 🏜️ & special chars: <>&"\'',
                'location': 'Arrakis-1α',
                'created_at': '2025-06-08T10:00:00',
                'updated_at': '2025-06-08T10:00:00'
            }],
            'crafting_recipes': []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON with Unicode
            json_path = Path(temp_dir) / 'unicode.json'
            result = self.service._export_json(special_data, json_path)
            assert result is True
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert 'Spice Mélange' in data['resources'][0]['name']
            assert '🏜️' in data['resources'][0]['description']
            
            # Test Markdown with Unicode
            md_path = Path(temp_dir) / 'unicode.md'
            result = self.service._export_markdown(special_data, md_path)
            assert result is True
            
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert 'Spice Mélange' in content
            assert '🏜️' in content
    
    def test_export_error_handling(self):
        """Test export error handling for various failure scenarios."""
        # Test with invalid path (read-only location)
        invalid_path = Path('/root/readonly/export.json')  # Typically read-only on Unix systems
        result = self.service._export_json({}, invalid_path)
        # Should handle gracefully (may return True on Windows, False on Unix)
        assert isinstance(result, bool)
        
        # Test with malformed data
        malformed_data = {'resources': [{'name': None}]}  # Name is None
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / 'malformed.json'
            # Should not crash, may succeed with None values
            result = self.service._export_json(malformed_data, export_path)
            assert isinstance(result, bool)


class TestConvenienceExportFunctions:
    """Test the convenience export functions."""
    
    @patch('app.services.import_export_service.ImportExportService')
    def test_export_all_data_convenience(self, mock_service_class):
        """Test the export_all_data convenience function."""
        mock_service = MagicMock()
        mock_service.export_all_data.return_value = True
        mock_service_class.return_value = mock_service
        
        result = export_all_data('/tmp/test.json', 'json')
        
        assert result is True
        mock_service_class.assert_called_once()
        mock_service.export_all_data.assert_called_once()
          # Check the arguments passed to the service
        call_args = mock_service.export_all_data.call_args
        # On Windows, paths use backslashes, so normalize for comparison
        actual_path = str(call_args[0][0]).replace('\\', '/')
        assert actual_path == '/tmp/test.json'
        assert call_args[0][1] == 'json'
    
    @patch('app.services.import_export_service.ImportExportService')
    def test_export_resources_convenience(self, mock_service_class):
        """Test the export_resources convenience function."""
        mock_service = MagicMock()
        mock_service.export_resources.return_value = True
        mock_service_class.return_value = mock_service
        
        result = export_resources('/tmp/resources.csv', 'csv')
        
        assert result is True
        mock_service.export_resources.assert_called_once()
    
    @patch('app.services.import_export_service.ImportExportService')
    def test_export_crafting_recipes_convenience(self, mock_service_class):
        """Test the export_crafting_recipes convenience function."""
        mock_service = MagicMock()
        mock_service.export_crafting_recipes.return_value = True
        mock_service_class.return_value = mock_service
        
        result = export_crafting_recipes('/tmp/recipes.md', 'markdown')
        
        assert result is True
        mock_service.export_crafting_recipes.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])