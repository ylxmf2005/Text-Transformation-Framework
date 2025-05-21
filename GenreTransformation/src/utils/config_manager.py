"""
Configuration Manager

This module provides the ConfigManager class for handling all configuration
aspects of the text transformation framework.
"""

import os
import yaml
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages configuration for the text transformation framework.
    
    Loads configuration from YAML files, validates settings, and provides
    configuration values to other modules.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the ConfigManager with a configuration file.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config_path = config_path
        self.config = {}
        
        # Load configuration
        self._load_config()
    
    def get_config(self, module_name: str) -> Dict:
        """
        Get configuration for a specific module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Dictionary containing module configuration
        """
        return self.config.get(module_name, {})
    
    def get_value(self, key_path: str, default=None) -> Any:
        """
        Get a specific configuration value using dot notation.
        
        Args:
            key_path: Path to the configuration value (e.g., "input_handler.semantic_core_method")
            default: Default value to return if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update_config(self, key_path: str, value: Any) -> None:
        """
        Update a configuration value.
        
        Args:
            key_path: Path to the configuration value (e.g., "input_handler.semantic_core_method")
            value: New value
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the correct nested dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Update the value
        config[keys[-1]] = value
    
    def save_config(self, path: str = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            path: Path to save configuration (defaults to original path)
        """
        save_path = path or self.config_path
        
        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def _load_config(self) -> None:
        """
        Load configuration from file.
        """
        if not os.path.exists(self.config_path):
            # Create default configuration if file doesn't exist
            self._create_default_config()
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Validate configuration
        self._validate_config()
    
    def _create_default_config(self) -> None:
        """
        Create default configuration file.
        """
        default_config = {
            "system": {
                "version": "1.0.0",
                "log_level": "INFO"
            },
            "input_handler": {
                "semantic_core_method": "option_a",  # option_a, option_b, option_c
                "attributes_method": "option_b"      # option_a, option_b
            },
            "exploration_engine": {
                "strategy": "strategy_2",            # strategy_1, strategy_2
                "evaluation": {
                    "consistency_weight": 0.3,
                    "feasibility_weight": 0.4,
                    "value_weight": 0.3,
                    "threshold": 0.6
                },
                "num_plans": 3
            },
            "generation_engine": {
                "llm_model": "gpt-4",
                "post_processing": True,
                "quality_threshold": 0.7
            },
            "attribute_manager": {
                "dimensions": {
                    "function_purpose": {
                        "active": True,
                        "weight": 1.0
                    },
                    "audience_context": {
                        "active": True,
                        "weight": 1.0
                    },
                    "structure_organization": {
                        "active": True,
                        "weight": 1.0
                    },
                    "strategy": {
                        "active": True,
                        "weight": 1.0
                    },
                    "conventions": {
                        "active": True,
                        "weight": 1.0
                    },
                    "linguistic_features": {
                        "active": True,
                        "weight": 1.0
                    },
                    "adjustment": {
                        "active": False,
                        "weight": 0.5
                    }
                }
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Write default configuration
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        self.config = default_config
    
    def _validate_config(self) -> None:
        """
        Validate configuration.
        """
        # Ensure required sections exist
        required_sections = ["system", "input_handler", "exploration_engine", 
                            "generation_engine", "attribute_manager"]
        
        for section in required_sections:
            if section not in self.config:
                self.config[section] = {}
        
        # Validate input_handler configuration
        input_handler = self.config.get("input_handler", {})
        if "semantic_core_method" not in input_handler:
            input_handler["semantic_core_method"] = "option_a"
        if "attributes_method" not in input_handler:
            input_handler["attributes_method"] = "option_b"
        
        # Validate exploration_engine configuration
        exploration_engine = self.config.get("exploration_engine", {})
        if "strategy" not in exploration_engine:
            exploration_engine["strategy"] = "strategy_2"
        if "evaluation" not in exploration_engine:
            exploration_engine["evaluation"] = {
                "consistency_weight": 0.3,
                "feasibility_weight": 0.4,
                "value_weight": 0.3,
                "threshold": 0.6
            }
        if "num_plans" not in exploration_engine:
            exploration_engine["num_plans"] = 3
        
        # Validate generation_engine configuration
        generation_engine = self.config.get("generation_engine", {})
        if "llm_model" not in generation_engine:
            generation_engine["llm_model"] = "gpt-4"
        if "post_processing" not in generation_engine:
            generation_engine["post_processing"] = True
        if "quality_threshold" not in generation_engine:
            generation_engine["quality_threshold"] = 0.7
        
        # Validate attribute_manager configuration
        attribute_manager = self.config.get("attribute_manager", {})
        if "dimensions" not in attribute_manager:
            attribute_manager["dimensions"] = {
                "function_purpose": {"active": True, "weight": 1.0},
                "audience_context": {"active": True, "weight": 1.0},
                "structure_organization": {"active": True, "weight": 1.0},
                "strategy": {"active": True, "weight": 1.0},
                "conventions": {"active": True, "weight": 1.0},
                "linguistic_features": {"active": True, "weight": 1.0},
                "adjustment": {"active": False, "weight": 0.5}
            }
