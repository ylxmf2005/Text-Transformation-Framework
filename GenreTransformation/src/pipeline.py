"""
Core pipeline for the text transformation framework.

This module implements the TransformationPipeline class which orchestrates the entire
transformation process from input to output.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union

from src.input_handler.input_processor import InputHandler
from src.attribute_manager.dimensions import AttributeManager
from src.exploration_engine.exploration_processor import ExplorationEngine
from src.generation_engine.generation_processor import GenerationEngine
from src.utils.config_manager import ConfigManager


class TransformationPipeline:
    """
    Orchestrates the entire transformation process from input to output.
    
    Implements the three-step process:
    1. Extraction: Extract semantic core and attributes from source text
    2. Exploration: Generate transformation plans
    3. Generation: Produce final text based on selected plan
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the TransformationPipeline with configuration.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize configuration manager
        self.config_manager = ConfigManager(config_path)
        
        # Initialize attribute manager
        self.attribute_manager = AttributeManager(self.config_manager)
        
        # Initialize input handler
        self.input_handler = InputHandler(self.config_manager, self.attribute_manager)
        
        # Initialize exploration engine
        self.exploration_engine = ExplorationEngine(self.config_manager, self.attribute_manager)
        
        # Initialize generation engine
        self.generation_engine = GenerationEngine(self.config_manager, self.attribute_manager)
        
        # State variables
        self.semantic_core = None
        self.original_attributes = None
        self.transformation_plans = []
        self.selected_plan = None
        self.final_text = None
    
    def extract(self, source_text: str) -> Dict:
        """
        Step 1: Extract semantic core and attributes from source text.
        
        Args:
            source_text: Source text content
            
        Returns:
            Dictionary with semantic_core and attributes
        """
        # Process input
        input_data = {"original_text": source_text}
        result = self.input_handler.process_input(input_data)
        
        # Store results in state
        self.semantic_core = result.get("semantic_core")
        self.original_attributes = result.get("original_attributes")
        
        return {
            "semantic_core": self.semantic_core,
            "attributes": self.original_attributes
        }
    
    def explore(self, user_instruction: str = None) -> List[Dict]:
        """
        Step 2: Generate transformation plans.
        
        Args:
            user_instruction: Optional user instruction
            
        Returns:
            List of transformation plan dictionaries
        """
        # Check if extraction has been performed
        if self.semantic_core is None or self.original_attributes is None:
            raise ValueError("Extraction must be performed before exploration")
        
        # Generate transformation plans
        self.transformation_plans = self.exploration_engine.explore(
            self.semantic_core, self.original_attributes, user_instruction)
        
        return self.transformation_plans
    
    def select_plan(self, plan_index: int = 0) -> Dict:
        """
        Select a transformation plan.
        
        Args:
            plan_index: Index of plan to select
            
        Returns:
            Selected plan dictionary
        """
        # Check if exploration has been performed
        if not self.transformation_plans:
            raise ValueError("Exploration must be performed before selecting a plan")
        
        # Validate plan index
        if plan_index < 0 or plan_index >= len(self.transformation_plans):
            raise ValueError(f"Invalid plan index: {plan_index}")
        
        # Select plan
        self.selected_plan = self.transformation_plans[plan_index]
        
        return self.selected_plan
    
    def generate(self) -> str:
        """
        Step 3: Generate final text based on selected plan.
        
        Returns:
            Generated text
        """
        # Check if a plan has been selected
        if self.selected_plan is None:
            raise ValueError("A transformation plan must be selected before generation")
        
        # Extract required information from selected plan
        target_genre = self.selected_plan.get("target_genre")
        target_attributes = self.selected_plan.get("target_attributes")
        instruction = self.selected_plan.get("instruction")
        
        # Calculate final attributes
        final_attributes = self.attribute_manager.calculate_final_attributes(
            self.original_attributes, target_attributes, target_genre)
        
        # Generate final text
        self.final_text = self.generation_engine.generate(
            self.semantic_core, final_attributes, instruction)
        
        return self.final_text
    
    def transform(self, source_text: str, user_instruction: str = None, plan_index: int = 0) -> str:
        """
        Perform the entire transformation process.
        
        Args:
            source_text: Source text content
            user_instruction: Optional user instruction
            plan_index: Index of plan to select
            
        Returns:
            Generated text
        """
        # Step 1: Extract
        self.extract(source_text)
        
        # Step 2: Explore
        self.explore(user_instruction)
        
        # Select plan
        self.select_plan(plan_index)
        
        # Step 3: Generate
        return self.generate()
