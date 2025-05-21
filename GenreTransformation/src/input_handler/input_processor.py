"""
Input Processor Module

This module handles the processing of input text and extraction of semantic core (C_sem)
and original attributes (A_orig).
"""

import json
import os
import requests
import re
from typing import Dict, Any, Optional, Union


class InputHandler:
    """
    Handles the processing of input text and extraction of semantic core and original attributes.
    
    Supports three distinct scenarios:
    - Scenario 1: Direct use of original text without feature extraction
    - Scenario 2: Extraction of structured features
    - Scenario 3: Extraction of text-form features
    
    For attributes, supports two options:
    - Option A: No attributes used
    - Option B: Attributes extracted from text using LLM
    """
    
    def __init__(self, config_manager, attribute_manager):
        """
        Initialize the InputHandler with configuration and attribute manager.
        
        Args:
            config_manager: Configuration manager instance
            attribute_manager: Attribute manager instance
        """
        self.config_manager = config_manager
        self.attribute_manager = attribute_manager
        
        # Get configuration
        self.extraction_scenario = config_manager.get_value(
            "input_handler.extraction_scenario", "scenario_1")
        
        # Get attributes method configuration
        self.attributes_method = config_manager.get_value(
            "input_handler.attributes_method", "option_b")
        
        # Get LLM configuration
        self.llm_config = config_manager.get_value("generation_engine.llm_config", {})
    
    def process_input(self, input_data: Dict) -> Dict:
        """
        Process input according to the selected extraction scenario.
        
        Args:
            input_data: Input data dictionary which may contain:
                - original_text: Original text content
                - target_genre: Target genre (for direct use scenario)
                - user_instruction: Optional user instruction
        
        Returns:
            Dictionary with appropriate data based on the scenario
        """
        result = {}
        
        # Process based on extraction scenario
        if self.extraction_scenario == "scenario_1":
            # Scenario 1: Direct use of original text without feature extraction
            if "original_text" not in input_data:
                raise ValueError("Original text required for direct use scenario")
            
            # For direct use, we skip extraction and use target attributes directly
            target_genre = input_data.get("target_genre", "blog_post")
            result = self._direct_use_scenario(input_data["original_text"], target_genre)
            
        elif self.extraction_scenario == "scenario_2":
            # Scenario 2: Extraction of structured features
            if "original_text" not in input_data:
                raise ValueError("Original text required for structured extraction")
            
            # Extract structured semantic core
            result["semantic_core"] = self._extract_structured_semantic_core(
                input_data["original_text"])
            
            # Handle attributes based on method
            if self.attributes_method == "option_a":
                # Option A: No attributes used
                result["attributes"] = {}
            else:  # Default to option_b
                # Option B: Extract attributes from text
                result["attributes"] = self._extract_attributes_from_text(
                    input_data["original_text"])
            
        elif self.extraction_scenario == "scenario_3":
            # Scenario 3: Extraction of text-form features
            if "original_text" not in input_data:
                raise ValueError("Original text required for text-form extraction")
            
            # Extract semantic core
            extracted = self._extract_full(input_data["original_text"])
            result["semantic_core"] = extracted["semantic_core"]
            
            # Handle attributes based on method
            if self.attributes_method == "option_a":
                # Option A: No attributes used
                result["attributes"] = {}
            else:  # Default to option_b
                # Option B: Use extracted attributes
                result["attributes"] = extracted.get("original_attributes", {})
            
        else:
            raise ValueError(f"Unsupported extraction scenario: {self.extraction_scenario}")
        
        # Add user instruction if provided
        if "user_instruction" in input_data:
            result["user_instruction"] = input_data["user_instruction"]
        
        return result
    
    def _direct_use_scenario(self, original_text: str, target_genre: str) -> Dict:
        """
        Handle direct use scenario (no feature extraction).
        
        Args:
            original_text: Original text content
            target_genre: Target genre
            
        Returns:
            Dictionary with original_text and target_attributes
        """
        # Load the direct use prompt template
        template_path = os.path.join("prompts", "extraction", "direct_use.txt")
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt
        prompt = prompt_template.format(
            original_text=original_text,
            target_genre=target_genre
        )
        
        # Call LLM to get target attributes
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            response_data = json.loads(llm_response)
            target_attributes = response_data.get("target_attributes", {})
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                response_data = json.loads(repaired_json)
                target_attributes = response_data.get("target_attributes", {})
            except json.JSONDecodeError:
                # If repair fails, use default attributes for the target genre
                target_attributes = self.attribute_manager.get_base_attributes(target_genre)
        
        # Return original text and target attributes
        return {
            "original_text": original_text,
            "target_attributes": target_attributes
        }
    
    def _extract_structured_semantic_core(self, text: str) -> Dict:
        """
        Extract structured semantic core from text using LLM.
        
        Args:
            text: Source text
            
        Returns:
            Structured semantic core
        """
        # Load the structured semantic core extraction prompt template
        template_path = os.path.join("prompts", "extraction", "extract_structured_semantic_core.txt")
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt
        prompt = prompt_template.format(original_text=text)
        
        # Call LLM to extract structured semantic core
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            structured_core = json.loads(llm_response)
            return structured_core
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                structured_core = json.loads(repaired_json)
                return structured_core
            except json.JSONDecodeError:
                # If repair fails, create a simple structured core
                return {
                    "main_summary_neutral": text[:500] + "...",
                    "identified_entities": [],
                    "key_events_or_states": [],
                    "core_propositions_or_claims": []
                }
    
    def _extract_attributes_from_text(self, text: str) -> Dict:
        """
        Extract attributes from text using LLM.
        
        Args:
            text: Source text
            
        Returns:
            Extracted attributes
        """
        # Load the attribute extraction prompt template
        template_path = os.path.join("prompts", "extraction", "extract_attributes.txt")
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt
        prompt = prompt_template.format(source_text=text)
        
        # Call LLM to extract attributes
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            attributes = json.loads(llm_response)
            return self.attribute_manager.normalize_attributes(attributes)
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                attributes = json.loads(repaired_json)
                return self.attribute_manager.normalize_attributes(attributes)
            except json.JSONDecodeError:
                # If repair fails, try to extract structured information from text
                return self._parse_attributes_from_text(llm_response)
    
    def _extract_full(self, text: str) -> Dict:
        """
        Extract both semantic core and original attributes from text using LLM.
        
        Args:
            text: Source text
            
        Returns:
            Dictionary with semantic_core and original_attributes
        """
        # Load the full extraction prompt template
        template_path = os.path.join("prompts", "extraction", "extract_full.txt")
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Format the prompt
        prompt = prompt_template.format(original_text=text)
        
        # Call LLM to extract semantic core and attributes
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            result = json.loads(llm_response)
            return result
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                result = json.loads(repaired_json)
                return result
            except json.JSONDecodeError:
                # If repair fails, create a simple result
                return {
                    "semantic_core": text[:500] + "...",
                    "original_attributes": self.attribute_manager.get_base_attributes("blog_post")
                }
    
    def _parse_attributes_from_text(self, text: str) -> Dict:
        """
        Parse attributes from LLM text response when JSON parsing fails.
        
        Args:
            text: LLM response text
            
        Returns:
            Parsed attributes
        """
        # Initialize attributes dictionary
        attributes = {
            "function_purpose": "",
            "audience_context": "",
            "structure_organization": "",
            "strategy": "",
            "conventions": "",
            "linguistic_features": {
                "information_density": "medium",
                "interactivity": "medium",
                "emotion": "neutral",
                "tone": "neutral"
            }
        }
        
        # Extract attributes from text using simple pattern matching
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for section headers
            if "function/purpose" in line.lower():
                current_section = "function_purpose"
            elif "audience/context" in line.lower():
                current_section = "audience_context"
            elif "structure/organization" in line.lower():
                current_section = "structure_organization"
            elif "strategy" in line.lower():
                current_section = "strategy"
            elif "conventions" in line.lower():
                current_section = "conventions"
            elif "linguistic features" in line.lower():
                current_section = "linguistic_features"
            elif current_section == "linguistic_features":
                # Check for linguistic feature attributes
                if "information density" in line.lower():
                    value = self._extract_value(line)
                    if value:
                        attributes["linguistic_features"]["information_density"] = value
                elif "interactivity" in line.lower():
                    value = self._extract_value(line)
                    if value:
                        attributes["linguistic_features"]["interactivity"] = value
                elif "emotion" in line.lower() or "sentiment" in line.lower():
                    value = self._extract_value(line)
                    if value:
                        attributes["linguistic_features"]["emotion"] = value
                elif "tone" in line.lower() or "formality" in line.lower():
                    value = self._extract_value(line)
                    if value:
                        attributes["linguistic_features"]["tone"] = value
            elif current_section and current_section != "linguistic_features":
                # Extract value for current section
                if ":" in line:
                    value = line.split(":", 1)[1].strip()
                    attributes[current_section] = value
                elif not attributes[current_section]:
                    # Use the line as value if no value has been set yet
                    attributes[current_section] = line
        
        return attributes
    
    def _extract_value(self, line: str) -> str:
        """Extract value from a line of text."""
        if ":" in line:
            return line.split(":", 1)[1].strip()
        elif "-" in line:
            return line.split("-", 1)[1].strip()
        else:
            return ""
    
    def _repair_json(self, text: str) -> str:
        """
        Attempt to repair malformed JSON.
        
        Args:
            text: Potentially malformed JSON string
            
        Returns:
            Repaired JSON string
        """
        # Try to extract JSON from text (in case there's additional text before/after JSON)
        json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        # Fix common JSON errors
        
        # Fix missing quotes around keys
        text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', text)
        
        # Fix single quotes to double quotes
        text = re.sub(r'\'', r'"', text)
        
        # Fix trailing commas in objects and arrays
        text = re.sub(r',(\s*[\]}])', r'\1', text)
        
        # Fix missing commas between elements
        text = re.sub(r'(["}\]]\s*)(["{\[])', r'\1,\2', text)
        
        return text
    
    def _call_llm(self, prompt: str, expect_json: bool = False) -> str:
        """
        Call LLM with prompt.
        
        Args:
            prompt: Formatted prompt string
            expect_json: Whether to expect JSON response
            
        Returns:
            LLM response text
        """
        # Get LLM configuration
        base_url = self.llm_config.get("base_url", "https://api.openai.com/v1")
        api_key = self.llm_config.get("llm_api_key", os.environ.get("OPENAI_API_KEY", ""))
        model = self.llm_config.get("model", "gpt-4.1")
        temperature = self.llm_config.get("temperature", 0.7)
        max_tokens = self.llm_config.get("max_tokens", 2000)
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Prepare system message based on whether we expect JSON
        system_message = "You are a text analysis assistant that extracts semantic cores and attributes from text."
        if expect_json:
            system_message += " Always respond with valid JSON. Do not include any explanations or text outside of the JSON structure."
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add response_format for JSON mode if expecting JSON
        if expect_json:
            payload["response_format"] = {"type": "json_object"}
        
        # Make API call
        try:
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            # If API call fails, return a default response
            print(f"LLM API call failed: {e}")
            return "{}" if expect_json else ""
