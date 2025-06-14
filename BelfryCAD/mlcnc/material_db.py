"""
Material Database

This module provides a comprehensive material property database
for CNC machining calculations. Translated from the original TCL implementation.
"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .feed_optimizer import MaterialType


class PropertyType(Enum):
    """Types of material properties."""
    MECHANICAL = "mechanical"
    THERMAL = "thermal"
    CHEMICAL = "chemical"
    MACHINING = "machining"


@dataclass
class MaterialProperty:
    """Individual material property."""
    name: str
    value: Union[float, str, bool]
    unit: str
    source: str
    confidence: float  # 0.0 to 1.0


@dataclass
class MaterialRecord:
    """Complete material record."""
    material_id: str
    name: str
    category: MaterialType
    properties: Dict[str, MaterialProperty]
    notes: Optional[str] = None
    last_updated: Optional[str] = None


class MaterialDatabase:
    """
    Material property database for CNC machining.
    
    This class provides storage, retrieval, and management of
    material properties used in machining calculations.
    """
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize the material database.
        
        Args:
            database_path: Path to database file (optional)
        """
        self.database_path = database_path
        self.materials: Dict[str, MaterialRecord] = {}
        self._load_default_materials()
        
        if database_path and os.path.exists(database_path):
            self.load_from_file(database_path)
    
    def _load_default_materials(self):
        """Load default material properties."""
        # Aluminum 6061
        al6061_props = {
            "density": MaterialProperty("Density", 0.098, "lb/in³", "NIST", 0.95),
            "tensile_strength": MaterialProperty("Tensile Strength", 45000, "psi", "ASM", 0.9),
            "yield_strength": MaterialProperty("Yield Strength", 40000, "psi", "ASM", 0.9),
            "elastic_modulus": MaterialProperty("Elastic Modulus", 10.0e6, "psi", "ASM", 0.95),
            "poisson_ratio": MaterialProperty("Poisson's Ratio", 0.33, "", "ASM", 0.9),
            "thermal_conductivity": MaterialProperty("Thermal Conductivity", 237, "W/mK", "NIST", 0.95),
            "specific_heat": MaterialProperty("Specific Heat", 896, "J/kgK", "NIST", 0.9),
            "melting_point": MaterialProperty("Melting Point", 1220, "°F", "ASM", 0.95),
            "machinability_rating": MaterialProperty("Machinability Rating", 0.9, "", "Industry", 0.8),
            "hardness_bhn": MaterialProperty("Hardness (BHN)", 95, "BHN", "ASM", 0.9),
            "surface_speed": MaterialProperty("Surface Speed", 800, "ft/min", "Machining", 0.85),
            "chip_load": MaterialProperty("Chip Load", 0.005, "in/tooth", "Machining", 0.8)
        }
        
        self.materials["AL6061"] = MaterialRecord(
            material_id="AL6061",
            name="Aluminum 6061-T6",
            category=MaterialType.ALUMINUM,
            properties=al6061_props,
            notes="General purpose aluminum alloy"
        )
        
        # Steel 1018
        steel1018_props = {
            "density": MaterialProperty("Density", 0.284, "lb/in³", "NIST", 0.95),
            "tensile_strength": MaterialProperty("Tensile Strength", 85000, "psi", "ASM", 0.9),
            "yield_strength": MaterialProperty("Yield Strength", 70000, "psi", "ASM", 0.9),
            "elastic_modulus": MaterialProperty("Elastic Modulus", 30.0e6, "psi", "ASM", 0.95),
            "poisson_ratio": MaterialProperty("Poisson's Ratio", 0.27, "", "ASM", 0.9),
            "thermal_conductivity": MaterialProperty("Thermal Conductivity", 50, "W/mK", "NIST", 0.9),
            "specific_heat": MaterialProperty("Specific Heat", 486, "J/kgK", "NIST", 0.9),
            "melting_point": MaterialProperty("Melting Point", 2750, "°F", "ASM", 0.95),
            "machinability_rating": MaterialProperty("Machinability Rating", 0.6, "", "Industry", 0.8),
            "hardness_bhn": MaterialProperty("Hardness (BHN)", 180, "BHN", "ASM", 0.9),
            "surface_speed": MaterialProperty("Surface Speed", 400, "ft/min", "Machining", 0.85),
            "chip_load": MaterialProperty("Chip Load", 0.008, "in/tooth", "Machining", 0.8)
        }
        
        self.materials["STEEL1018"] = MaterialRecord(
            material_id="STEEL1018",
            name="Steel 1018 (Low Carbon)",
            category=MaterialType.STEEL,
            properties=steel1018_props,
            notes="Low carbon mild steel"
        )
        
        # Stainless Steel 304
        ss304_props = {
            "density": MaterialProperty("Density", 0.29, "lb/in³", "NIST", 0.95),
            "tensile_strength": MaterialProperty("Tensile Strength", 95000, "psi", "ASM", 0.9),
            "yield_strength": MaterialProperty("Yield Strength", 42000, "psi", "ASM", 0.9),
            "elastic_modulus": MaterialProperty("Elastic Modulus", 28.0e6, "psi", "ASM", 0.95),
            "poisson_ratio": MaterialProperty("Poisson's Ratio", 0.30, "", "ASM", 0.9),
            "thermal_conductivity": MaterialProperty("Thermal Conductivity", 16, "W/mK", "NIST", 0.9),
            "specific_heat": MaterialProperty("Specific Heat", 500, "J/kgK", "NIST", 0.9),
            "melting_point": MaterialProperty("Melting Point", 2800, "°F", "ASM", 0.95),
            "machinability_rating": MaterialProperty("Machinability Rating", 0.4, "", "Industry", 0.8),
            "hardness_bhn": MaterialProperty("Hardness (BHN)", 200, "BHN", "ASM", 0.9),
            "surface_speed": MaterialProperty("Surface Speed", 300, "ft/min", "Machining", 0.85),
            "chip_load": MaterialProperty("Chip Load", 0.006, "in/tooth", "Machining", 0.8)
        }
        
        self.materials["SS304"] = MaterialRecord(
            material_id="SS304",
            name="Stainless Steel 304",
            category=MaterialType.STAINLESS_STEEL,
            properties=ss304_props,
            notes="Austenitic stainless steel"
        )
        
        # Add more materials...
        self._add_brass_materials()
        self._add_plastic_materials()
    
    def _add_brass_materials(self):
        """Add brass material properties."""
        brass360_props = {
            "density": MaterialProperty("Density", 0.307, "lb/in³", "NIST", 0.95),
            "tensile_strength": MaterialProperty("Tensile Strength", 57000, "psi", "ASM", 0.9),
            "yield_strength": MaterialProperty("Yield Strength", 46000, "psi", "ASM", 0.9),
            "elastic_modulus": MaterialProperty("Elastic Modulus", 15.0e6, "psi", "ASM", 0.9),
            "poisson_ratio": MaterialProperty("Poisson's Ratio", 0.33, "", "ASM", 0.9),
            "thermal_conductivity": MaterialProperty("Thermal Conductivity", 120, "W/mK", "NIST", 0.9),
            "specific_heat": MaterialProperty("Specific Heat", 380, "J/kgK", "NIST", 0.9),
            "melting_point": MaterialProperty("Melting Point", 1700, "°F", "ASM", 0.95),
            "machinability_rating": MaterialProperty("Machinability Rating", 0.95, "", "Industry", 0.9),
            "hardness_bhn": MaterialProperty("Hardness (BHN)", 120, "BHN", "ASM", 0.9),
            "surface_speed": MaterialProperty("Surface Speed", 900, "ft/min", "Machining", 0.85),
            "chip_load": MaterialProperty("Chip Load", 0.010, "in/tooth", "Machining", 0.8)
        }
        
        self.materials["BRASS360"] = MaterialRecord(
            material_id="BRASS360",
            name="Brass 360 (Free Machining)",
            category=MaterialType.BRASS,
            properties=brass360_props,
            notes="Excellent machinability"
        )
    
    def _add_plastic_materials(self):
        """Add plastic material properties."""
        nylon_props = {
            "density": MaterialProperty("Density", 0.041, "lb/in³", "NIST", 0.9),
            "tensile_strength": MaterialProperty("Tensile Strength", 12000, "psi", "Manufacturer", 0.8),
            "yield_strength": MaterialProperty("Yield Strength", 11000, "psi", "Manufacturer", 0.8),
            "elastic_modulus": MaterialProperty("Elastic Modulus", 0.4e6, "psi", "Manufacturer", 0.8),
            "poisson_ratio": MaterialProperty("Poisson's Ratio", 0.40, "", "Literature", 0.7),
            "thermal_conductivity": MaterialProperty("Thermal Conductivity", 0.25, "W/mK", "NIST", 0.8),
            "specific_heat": MaterialProperty("Specific Heat", 1700, "J/kgK", "NIST", 0.8),
            "melting_point": MaterialProperty("Melting Point", 420, "°F", "Manufacturer", 0.9),
            "machinability_rating": MaterialProperty("Machinability Rating", 0.95, "", "Industry", 0.7),
            "hardness_shore": MaterialProperty("Hardness (Shore D)", 80, "Shore D", "ASTM", 0.8),
            "surface_speed": MaterialProperty("Surface Speed", 1200, "ft/min", "Machining", 0.7),
            "chip_load": MaterialProperty("Chip Load", 0.015, "in/tooth", "Machining", 0.7)
        }
        
        self.materials["NYLON66"] = MaterialRecord(
            material_id="NYLON66",
            name="Nylon 66",
            category=MaterialType.PLASTIC,
            properties=nylon_props,
            notes="Engineering thermoplastic"
        )
    
    def get_material(self, material_id: str) -> Optional[MaterialRecord]:
        """
        Get material record by ID.
        
        Args:
            material_id: Material identifier
            
        Returns:
            MaterialRecord if found, None otherwise
        """
        return self.materials.get(material_id.upper())
    
    def get_property(self, material_id: str, property_name: str) -> Optional[MaterialProperty]:
        """
        Get specific property for a material.
        
        Args:
            material_id: Material identifier
            property_name: Property name
            
        Returns:
            MaterialProperty if found, None otherwise
        """
        material = self.get_material(material_id)
        if material:
            return material.properties.get(property_name)
        return None
    
    def get_property_value(self, material_id: str, property_name: str) -> Optional[Union[float, str, bool]]:
        """
        Get property value for a material.
        
        Args:
            material_id: Material identifier
            property_name: Property name
            
        Returns:
            Property value if found, None otherwise
        """
        prop = self.get_property(material_id, property_name)
        return prop.value if prop else None
    
    def list_materials(self, category: Optional[MaterialType] = None) -> List[MaterialRecord]:
        """
        List all materials, optionally filtered by category.
        
        Args:
            category: Optional material category filter
            
        Returns:
            List of material records
        """
        if category:
            return [mat for mat in self.materials.values() if mat.category == category]
        return list(self.materials.values())
    
    def add_material(self, material: MaterialRecord) -> bool:
        """
        Add a new material to the database.
        
        Args:
            material: Material record to add
            
        Returns:
            True if successful, False if material already exists
        """
        if material.material_id in self.materials:
            return False
        
        self.materials[material.material_id] = material
        return True
    
    def update_material(self, material_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update material properties.
        
        Args:
            material_id: Material identifier
            updates: Dictionary of updates
            
        Returns:
            True if successful, False if material not found
        """
        material = self.get_material(material_id)
        if not material:
            return False
        
        for key, value in updates.items():
            if hasattr(material, key):
                setattr(material, key, value)
            elif key in material.properties:
                # Update property value
                material.properties[key].value = value
        
        return True
    
    def delete_material(self, material_id: str) -> bool:
        """
        Delete a material from the database.
        
        Args:
            material_id: Material identifier
            
        Returns:
            True if successful, False if material not found
        """
        if material_id in self.materials:
            del self.materials[material_id]
            return True
        return False
    
    def search_materials(self, query: str) -> List[MaterialRecord]:
        """
        Search materials by name or properties.
        
        Args:
            query: Search query
            
        Returns:
            List of matching material records
        """
        query_lower = query.lower()
        results = []
        
        for material in self.materials.values():
            # Search in name
            if query_lower in material.name.lower():
                results.append(material)
                continue
            
            # Search in material ID
            if query_lower in material.material_id.lower():
                results.append(material)
                continue
            
            # Search in properties
            for prop in material.properties.values():
                if query_lower in prop.name.lower():
                    results.append(material)
                    break
        
        return results
    
    def get_similar_materials(self, material_id: str, property_names: List[str]) -> List[MaterialRecord]:
        """
        Find materials with similar properties.
        
        Args:
            material_id: Reference material ID
            property_names: Properties to compare
            
        Returns:
            List of similar materials sorted by similarity
        """
        reference = self.get_material(material_id)
        if not reference:
            return []
        
        similar_materials = []
        
        for mat_id, material in self.materials.items():
            if mat_id == material_id:
                continue
            
            similarity_score = self._calculate_similarity(
                reference, material, property_names)
            
            if similarity_score > 0.7:  # 70% similarity threshold
                similar_materials.append((material, similarity_score))
        
        # Sort by similarity score (descending)
        similar_materials.sort(key=lambda x: x[1], reverse=True)
        
        return [mat for mat, score in similar_materials]
    
    def _calculate_similarity(self, mat1: MaterialRecord, mat2: MaterialRecord,
                            property_names: List[str]) -> float:
        """Calculate similarity score between two materials."""
        total_score = 0.0
        valid_comparisons = 0
        
        for prop_name in property_names:
            prop1 = mat1.properties.get(prop_name)
            prop2 = mat2.properties.get(prop_name)
            
            if prop1 and prop2 and isinstance(prop1.value, (int, float)) and isinstance(prop2.value, (int, float)):
                # Calculate relative difference
                diff = abs(prop1.value - prop2.value) / max(prop1.value, prop2.value)
                similarity = 1.0 - min(1.0, diff)
                total_score += similarity
                valid_comparisons += 1
        
        return total_score / valid_comparisons if valid_comparisons > 0 else 0.0
    
    def export_material_data(self, material_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export material data to dictionary format.
        
        Args:
            material_ids: Optional list of material IDs to export
            
        Returns:
            Dictionary with material data
        """
        if material_ids:
            materials_to_export = {mat_id: self.materials[mat_id] 
                                 for mat_id in material_ids 
                                 if mat_id in self.materials}
        else:
            materials_to_export = self.materials
        
        export_data = {}
        for mat_id, material in materials_to_export.items():
            export_data[mat_id] = {
                "material_id": material.material_id,
                "name": material.name,
                "category": material.category.value,
                "properties": {
                    prop_name: {
                        "name": prop.name,
                        "value": prop.value,
                        "unit": prop.unit,
                        "source": prop.source,
                        "confidence": prop.confidence
                    }
                    for prop_name, prop in material.properties.items()
                },
                "notes": material.notes,
                "last_updated": material.last_updated
            }
        
        return export_data
    
    def import_material_data(self, data: Dict[str, Any]) -> int:
        """
        Import material data from dictionary format.
        
        Args:
            data: Dictionary with material data
            
        Returns:
            Number of materials imported
        """
        imported_count = 0
        
        for mat_id, mat_data in data.items():
            try:
                # Reconstruct properties
                properties = {}
                for prop_name, prop_data in mat_data.get("properties", {}).items():
                    properties[prop_name] = MaterialProperty(
                        name=prop_data["name"],
                        value=prop_data["value"],
                        unit=prop_data["unit"],
                        source=prop_data["source"],
                        confidence=prop_data["confidence"]
                    )
                
                # Create material record
                material = MaterialRecord(
                    material_id=mat_data["material_id"],
                    name=mat_data["name"],
                    category=MaterialType(mat_data["category"]),
                    properties=properties,
                    notes=mat_data.get("notes"),
                    last_updated=mat_data.get("last_updated")
                )
                
                self.materials[mat_id] = material
                imported_count += 1
                
            except (KeyError, ValueError) as e:
                print(f"Error importing material {mat_id}: {e}")
                continue
        
        return imported_count
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save database to JSON file.
        
        Args:
            filepath: Path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = self.export_material_data()
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving database: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """
        Load database from JSON file.
        
        Args:
            filepath: Path to load file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            imported_count = self.import_material_data(data)
            print(f"Imported {imported_count} materials from {filepath}")
            return True
            
        except Exception as e:
            print(f"Error loading database: {e}")
            return False
    
    def validate_database(self) -> Dict[str, List[str]]:
        """
        Validate database integrity.
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        for mat_id, material in self.materials.items():
            # Check required properties
            required_props = ["density", "tensile_strength", "machinability_rating"]
            for prop in required_props:
                if prop not in material.properties:
                    errors.append(f"{mat_id}: Missing required property '{prop}'")
            
            # Check property values
            for prop_name, prop in material.properties.items():
                if isinstance(prop.value, (int, float)) and prop.value < 0:
                    warnings.append(f"{mat_id}: Negative value for '{prop_name}'")
                
                if prop.confidence < 0.5:
                    warnings.append(f"{mat_id}: Low confidence ({prop.confidence}) for '{prop_name}'")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "total_materials": len(self.materials)
        }