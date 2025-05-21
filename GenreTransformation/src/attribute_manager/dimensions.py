"""
Dimensions module

This module defines the AttributeManager class which handles the multi-dimensional
attributes of text as defined in the framework.
"""

import json
import yaml
import os
import requests
import re
from typing import Dict, List, Any, Optional, Union


class AttributeManager:
    """
    Manages text attributes across multiple dimensions:
    1. Function/Purpose
    2. Audience/Context
    3. Structure/Organization
    4. Strategy (Rhetorical/Communicative)
    5. Conventions
    6. Linguistic Features
    7. Adjustment
    
    Provides methods for creating, manipulating, and comparing attribute sets.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the AttributeManager with configuration.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.dimension_config = config_manager.get_config("attribute_manager").get("dimensions", {})
        
        # Get LLM configuration
        self.llm_config = config_manager.get_value("generation_engine.llm_config", {})
        
        # Define dimension descriptions (for reference only, not restrictive)
        self.dimension_descriptions = {
            "function_purpose": "The primary purpose or function of the text",
            "audience_context": "The target audience and context of the text",
            "structure_organization": "The organizational structure of the text",
            "strategy": "The rhetorical or communicative strategies used",
            "conventions": "The conventions followed in the text",
            "linguistic_features": {
                "information_density": "The density of information in the text",
                "interactivity": "The degree of interaction with the reader",
                "emotion": "The emotional content of the text",
                "tone": "The tone of the text"
            },
            "adjustment": "Additional adjustments to the text attributes"
        }
        
        # Define example attributes for common genres (as guidance only, not restrictions)
        self._load_genre_examples()
    
    def _load_genre_examples(self):
        """
        Load genre examples from file or create default examples.
        This is for guidance only, not for enforcing restrictions.
        """
        # Try to load from file
        examples_path = os.path.join("configs", "genre_examples.yaml")
        if os.path.exists(examples_path):
            try:
                with open(examples_path, 'r') as f:
                    self.genre_example_attributes = yaml.safe_load(f)
                return
            except Exception as e:
                print(f"Error loading genre examples: {e}")
        
        # Default examples if file not found or loading fails
        self.genre_example_attributes = {
            "news_article": {
                "function_purpose": "expository",
                "audience_context": "general_public",
                "structure_organization": "importance_order",
                "strategy": "logical_appeal",
                "conventions": "genre_structure",
                "linguistic_features": {
                    "information_density": "high",
                    "interactivity": "low",
                    "emotion": "low",
                    "tone": "objective"
                }
            },
            "academic_paper": {
                "function_purpose": "expository",
                "audience_context": "expert_academic",
                "structure_organization": "thematic",
                "strategy": "logical_appeal",
                "conventions": "citation_reference",
                "linguistic_features": {
                    "information_density": "high",
                    "interactivity": "low",
                    "emotion": "low",
                    "tone": "formal"
                }
            },
            "blog_post": {
                "function_purpose": "expository",
                "audience_context": "general_public",
                "structure_organization": "thematic",
                "strategy": "direct_address",
                "conventions": "formatting",
                "linguistic_features": {
                    "information_density": "medium",
                    "interactivity": "high",
                    "emotion": "medium",
                    "tone": "semi_formal"
                }
            },
            "story": {
                "function_purpose": "narrative",
                "audience_context": "general_public",
                "structure_organization": "chronological",
                "strategy": "storytelling",
                "conventions": "genre_structure",
                "linguistic_features": {
                    "information_density": "medium",
                    "interactivity": "medium",
                    "emotion": "high",
                    "tone": "informal"
                }
            },
            "technical_manual": {
                "function_purpose": "instructional",
                "audience_context": "professional",
                "structure_organization": "enumeration",
                "strategy": "direct_address",
                "conventions": "formatting",
                "linguistic_features": {
                    "information_density": "high",
                    "interactivity": "medium",
                    "emotion": "low",
                    "tone": "formal"
                }
            },
            "persuasive_essay": {
                "function_purpose": "argumentative",
                "audience_context": "general_public",
                "structure_organization": "thematic",
                "strategy": "logical_appeal",
                "conventions": "genre_structure",
                "linguistic_features": {
                    "information_density": "medium",
                    "interactivity": "medium",
                    "emotion": "medium",
                    "tone": "persuasive"
                }
            }
        }
    
    def create_attribute_set(self, source: Union[str, Dict], method: str = "direct") -> Dict:
        """
        Create attribute set from various sources (text, JSON, etc.)
        
        Args:
            source: Source data (text or structured data)
            method: Method to use ("direct", "extract", "llm")
            
        Returns:
            Dictionary containing attribute set
        """
        if method == "direct" and isinstance(source, dict):
            # Direct input of attributes - accept as is with minimal normalization
            return self.normalize_attributes(source)
        
        elif method == "extract" and isinstance(source, str):
            # Extract attributes from text using LLM
            return self._extract_attributes_from_text_llm(source)
        
        elif method == "llm" and isinstance(source, dict):
            # Use LLM to enhance attributes
            return self._enhance_attributes_with_llm(source)
        
        else:
            # Flexible fallback - try to handle the input in the most appropriate way
            if isinstance(source, dict):
                return self.normalize_attributes(source)
            elif isinstance(source, str):
                return self._extract_attributes_from_text_llm(source)
            else:
                # Return empty attribute set as last resort
                return self.normalize_attributes({})
    
    def get_base_attributes(self, genre: str) -> Dict:
        """
        Get example attributes for a specific genre.
        These are only examples, not enforced restrictions.
        
        Args:
            genre: Genre name
            
        Returns:
            Dictionary of example attributes for the genre
        """
        # First try to get from examples
        if genre in self.genre_example_attributes:
            return self.genre_example_attributes[genre].copy()
        
        # If genre not found, use LLM to generate attributes for this genre
        attributes = self._generate_attributes_for_genre_llm(genre)
        if attributes:
            return attributes
        
        # Fallback to default set if LLM fails
        return {
            "function_purpose": "expository",
            "audience_context": "general_public",
            "structure_organization": "thematic",
            "strategy": "logical_appeal",
            "conventions": "genre_structure",
            "linguistic_features": {
                "information_density": "medium",
                "interactivity": "medium",
                "emotion": "neutral",
                "tone": "semi_formal"
            }
        }
    
    def calculate_final_attributes(self, base_attrs: Dict, delta_attrs: Dict, target_genre: str) -> Dict:
        """
        Calculate final attributes based on formula:
        A_final = CalFinalAttrs(A_base, ΔA_instruct, G_target)
        
        Args:
            base_attrs: Base attributes (A_base)
            delta_attrs: Attribute changes from instructions (ΔA_instruct)
            target_genre: Target genre (G_target)
            
        Returns:
            Final attribute set (A_final)
        """
        # Start with base attributes for the target genre if not provided
        if not base_attrs:
            base_attrs = self.get_base_attributes(target_genre)
        
        # Apply delta attributes (overwrite base values)
        final_attrs = self._deep_merge(base_attrs, delta_attrs)
        
        # Add target genre to final attributes if not present
        if "target_genre" not in final_attrs:
            final_attrs["target_genre"] = target_genre
        
        # Apply dimension weights from configuration
        final_attrs = self._apply_dimension_weights(final_attrs)
        
        return final_attrs
    
    def compare_attributes(self, attrs1: Dict, attrs2: Dict) -> Dict:
        """
        Compare two attribute sets and return differences.
        
        Args:
            attrs1: First attribute set
            attrs2: Second attribute set
            
        Returns:
            Dictionary of differences
        """
        differences = {}
        
        # Compare top-level dimensions
        for dim in set(list(attrs1.keys()) + list(attrs2.keys())):
            if dim not in attrs1:
                differences[dim] = {"status": "added", "value": attrs2[dim]}
            elif dim not in attrs2:
                differences[dim] = {"status": "removed", "value": attrs1[dim]}
            elif dim == "linguistic_features":
                # Special handling for nested linguistic features
                ling_diff = {}
                for feature in set(list(attrs1.get(dim, {}).keys()) + list(attrs2.get(dim, {}).keys())):
                    if feature not in attrs1.get(dim, {}):
                        ling_diff[feature] = {"status": "added", "value": attrs2[dim][feature]}
                    elif feature not in attrs2.get(dim, {}):
                        ling_diff[feature] = {"status": "removed", "value": attrs1[dim][feature]}
                    elif attrs1[dim][feature] != attrs2[dim][feature]:
                        ling_diff[feature] = {
                            "status": "changed",
                            "old_value": attrs1[dim][feature],
                            "new_value": attrs2[dim][feature]
                        }
                
                if ling_diff:
                    differences[dim] = ling_diff
            elif attrs1[dim] != attrs2[dim]:
                differences[dim] = {
                    "status": "changed",
                    "old_value": attrs1[dim],
                    "new_value": attrs2[dim]
                }
        
        return differences
    
    def check_attribute_completeness(self, attrs: Dict) -> Dict:
        """
        Check attribute set for completeness and return missing dimensions.
        This is for guidance only, not for enforcing restrictions.
        
        Args:
            attrs: Attribute set to check
            
        Returns:
            Dictionary of missing dimensions
        """
        # Check recommended dimensions
        recommended_dimensions = ["function_purpose", "audience_context", "structure_organization", 
                                 "strategy", "conventions", "linguistic_features"]
        
        missing = {}
        
        for dim in recommended_dimensions:
            if dim not in attrs:
                missing[dim] = self.dimension_descriptions[dim]
        
        # Check linguistic features
        if "linguistic_features" in attrs:
            recommended_features = ["information_density", "interactivity", "emotion", "tone"]
            missing_features = {}
            
            for feature in recommended_features:
                if feature not in attrs["linguistic_features"]:
                    missing_features[feature] = self.dimension_descriptions["linguistic_features"][feature]
            
            if missing_features:
                missing["linguistic_features"] = missing_features
        
        return missing
    
    def normalize_attributes(self, attrs: Dict) -> Dict:
        """
        Normalize attribute set by ensuring consistent structure.
        This is minimal normalization, not enforcing restrictions.
        
        Args:
            attrs: Attribute set
            
        Returns:
            Normalized attribute set
        """
        # Create a copy to avoid modifying the original
        normalized = attrs.copy() if attrs else {}
        
        # Ensure linguistic_features is a dictionary if present
        if "linguistic_features" in normalized and not isinstance(normalized["linguistic_features"], dict):
            normalized["linguistic_features"] = {"general": normalized["linguistic_features"]}
        
        # If linguistic_features is missing, add an empty dict
        if "linguistic_features" not in normalized:
            normalized["linguistic_features"] = {}
        
        return normalized
    
    def serialize_attributes(self, attrs: Dict, format: str = "json") -> str:
        """
        Convert attributes to specified format for output.
        
        Args:
            attrs: Attribute set
            format: Output format ("json" or "yaml")
            
        Returns:
            Serialized attributes as string
        """
        if format == "json":
            return json.dumps(attrs, indent=2)
        elif format == "yaml":
            return yaml.dump(attrs, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _extract_attributes_from_text_llm(self, text: str) -> Dict:
        """
        Extract attributes from text using LLM.
        
        Args:
            text: Source text
            
        Returns:
            Extracted attributes
        """
        # Load the extraction prompt template
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
            return self.normalize_attributes(attributes)
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                attributes = json.loads(repaired_json)
                return self.normalize_attributes(attributes)
            except json.JSONDecodeError:
                # If repair fails, try to extract structured information from text
                return self._parse_attributes_from_text(llm_response)
    
    def _generate_attributes_for_genre_llm(self, genre: str) -> Dict:
        """
        Generate attributes for a genre using LLM.
        
        Args:
            genre: Genre name
            
        Returns:
            Generated attributes
        """
        # Create prompt for LLM
        prompt = f"""
# Task: Generate typical attributes for the '{genre}' genre.

## Instructions:
Please provide typical attributes for the '{genre}' genre across the following dimensions:
1. Function/Purpose: The primary purpose or function of the text
2. Audience/Context: The target audience and context of the text
3. Structure/Organization: The organizational structure of the text
4. Strategy: The rhetorical or communicative strategies used
5. Conventions: The conventions followed in the text
6. Linguistic Features:
   - Information Density: The density of information in the text
   - Interactivity: The degree of interaction with the reader
   - Emotion: The emotional content of the text
   - Tone: The tone of the text

Return the attributes in JSON format.
"""
        
        # Call LLM to generate attributes
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            attributes = json.loads(llm_response)
            return self.normalize_attributes(attributes)
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                attributes = json.loads(repaired_json)
                return self.normalize_attributes(attributes)
            except json.JSONDecodeError:
                # If repair fails, return empty dict
                return {}
    
    def _enhance_attributes_with_llm(self, attrs: Dict) -> Dict:
        """
        Use LLM to enhance attributes.
        
        Args:
            attrs: Attribute set
            
        Returns:
            Enhanced attributes
        """
        # Create prompt for LLM
        prompt = f"""
# Task: Enhance the following attribute set.

## Input Attributes:
{json.dumps(attrs, indent=2)}

## Instructions:
Please enhance the attribute set by:
1. Filling in any missing dimensions
2. Adding more detail to existing dimensions
3. Ensuring consistency across dimensions
4. Adding any additional relevant attributes

Return the enhanced attributes in JSON format.
"""
        
        # Call LLM to enhance attributes
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            enhanced = json.loads(llm_response)
            return self.normalize_attributes(enhanced)
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                enhanced = json.loads(repaired_json)
                return self.normalize_attributes(enhanced)
            except json.JSONDecodeError:
                # If repair fails, return original attributes
                return self.normalize_attributes(attrs)
    
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
    
    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """
        Deep merge two dictionaries.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Merged dictionary
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_dimension_weights(self, attrs: Dict) -> Dict:
        """
        Apply dimension weights from configuration.
        
        Args:
            attrs: Attribute set
            
        Returns:
            Attribute set with weights applied
        """
        # Get dimension weights from configuration
        weights = self.dimension_config.get("weights", {})
        
        # If no weights defined, return original attributes
        if not weights:
            return attrs
        
        # Create a copy to avoid modifying the original
        weighted = attrs.copy()
        
        # Add weights to attributes
        if "weights" not in weighted:
            weighted["weights"] = {}
        
        # Apply weights from configuration
        for dim, weight in weights.items():
            if dim in weighted:
                weighted["weights"][dim] = weight
        
        return weighted
    
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
        Call LLM with prompt using OpenAI-compatible API.
        
        Args:
            prompt: Formatted prompt string
            expect_json: Whether to expect JSON response
            
        Returns:
            Generated text from LLM
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
        system_message = "You are an attribute analysis assistant that helps with text attribute management."
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
