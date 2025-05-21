"""
Exploration Processor Module

This module implements the ExplorationEngine class which generates multiple transformation
plans based on the semantic core and original attributes.
"""

import json
import os
import requests
import re
from typing import Dict, List, Any, Optional, Union


class ExplorationEngine:
    """
    Generates multiple transformation plans based on the semantic core and original attributes.
    
    Supports different exploration strategies:
    - Strategy 2.2.1: Direct suggestion of target genres and instructions
    - Strategy 2.2.2: Explicit dimension transformation
    
    Handles scenarios with and without user instructions.
    """
    
    def __init__(self, config_manager, attribute_manager):
        """
        Initialize the ExplorationEngine with configuration and attribute manager.
        
        Args:
            config_manager: Configuration manager instance
            attribute_manager: Attribute manager instance
        """
        self.config_manager = config_manager
        self.attribute_manager = attribute_manager
        
        # Get configuration
        self.strategy = config_manager.get_value(
            "exploration_engine.strategy", "strategy_2")
        self.num_plans = config_manager.get_value(
            "exploration_engine.num_plans", 3)
        
        # Get evaluation weights
        eval_config = config_manager.get_value("exploration_engine.evaluation", {})
        self.consistency_weight = eval_config.get("consistency_weight", 0.3)
        self.feasibility_weight = eval_config.get("feasibility_weight", 0.4)
        self.value_weight = eval_config.get("value_weight", 0.3)
        self.threshold = eval_config.get("threshold", 0.6)
        
        # Get LLM configuration
        self.llm_config = config_manager.get_value("generation_engine.llm_config", {})
        
        # Define genre compatibility for reference (not used directly, but provided to LLM)
        self.genre_compatibility_reference = {
            "news_article": ["blog_post", "persuasive_essay"],
            "blog_post": ["news_article", "persuasive_essay", "story"],
            "academic_paper": ["technical_manual", "persuasive_essay"],
            "story": ["blog_post"],
            "technical_manual": ["academic_paper"],
            "persuasive_essay": ["blog_post", "news_article", "academic_paper"]
        }
    
    def explore(self, semantic_core: Union[str, Dict], original_attributes: Dict, 
               user_instruction: str = None) -> List[Dict]:
        """
        Generate transformation plans.
        
        Args:
            semantic_core: Semantic core content
            original_attributes: Original attributes dictionary
            user_instruction: Optional user instruction
            
        Returns:
            List of plan dictionaries
        """
        # Generate plans based on selected strategy
        if self.strategy == "strategy_1":
            plans = self.generate_plans_strategy_1(
                semantic_core, original_attributes, user_instruction)
        else:  # Default to strategy_2
            plans = self.generate_plans_strategy_2(
                semantic_core, original_attributes, user_instruction)
        
        # Evaluate and filter plans
        evaluated_plans = []
        for plan in plans:
            evaluated_plan = self.evaluate_plan_llm(plan, semantic_core, original_attributes)
            evaluated_plans.append(evaluated_plan)
        
        # Filter plans based on evaluation scores
        filtered_plans = self.filter_plans(evaluated_plans, self.threshold)
        
        # Ensure we have at least one plan
        if not filtered_plans and evaluated_plans:
            # If no plans meet threshold, return the best one
            filtered_plans = [max(evaluated_plans, 
                                 key=lambda p: p.get("evaluation", {}).get("overall_score", 0))]
        
        return filtered_plans
    
    def generate_plans_strategy_1(self, semantic_core: Union[str, Dict], original_attributes: Dict,
                                 user_instruction: str = None) -> List[Dict]:
        """
        Generate plans using Strategy 2.2.1 (Genre and Instruction Priority).
        
        This strategy directly suggests target genres and corresponding high-level
        instructions without explicitly outputting A_temp.
        
        Args:
            semantic_core: Semantic core content
            original_attributes: Original attributes dictionary
            user_instruction: Optional user instruction
            
        Returns:
            List of plan dictionaries
        """
        # Load the appropriate prompt template based on whether user instruction is provided
        if user_instruction:
            template_path = os.path.join("prompts", "exploration", "strategy_1_with_instruction.txt")
            if not os.path.exists(template_path):
                template_path = os.path.join("prompts", "exploration", "strategy_1.txt")
        else:
            template_path = os.path.join("prompts", "exploration", "strategy_1.txt")
        
        # Load prompt template
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Convert semantic core to string if it's a structured object
        if isinstance(semantic_core, dict):
            semantic_core_str = json.dumps(semantic_core, indent=2)
        else:
            semantic_core_str = semantic_core
        
        # Format the prompt
        prompt = prompt_template.format(
            semantic_core=semantic_core_str,
            original_attributes=json.dumps(original_attributes, indent=2),
            user_instruction=user_instruction or "",
            num_plans=self.num_plans
        )
        
        # Call LLM to generate plans
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            # First, clean any potential markdown or extra text
            cleaned_response = self._clean_json_response(llm_response)
            plans = json.loads(cleaned_response)
            
            # Ensure plans is a list
            if not isinstance(plans, list):
                if isinstance(plans, dict) and "plans" in plans:
                    plans = plans["plans"]
                else:
                    plans = [plans]
            
            # Process each plan to ensure it has the required fields
            processed_plans = []
            for plan in plans:
                if isinstance(plan, dict):
                    # Ensure plan has target_genre and instruction
                    if "target_genre" not in plan:
                        plan["target_genre"] = "blog_post"  # Default genre
                    if "instruction" not in plan:
                        plan["instruction"] = "Transform the content into the target genre."
                    
                    # Add target_attributes if not present
                    if "target_attributes" not in plan:
                        plan["target_attributes"] = self.attribute_manager.get_base_attributes(plan["target_genre"])
                    
                    processed_plans.append(plan)
            
            return processed_plans[:self.num_plans]
        
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                plans = json.loads(repaired_json)
                
                # Ensure plans is a list
                if not isinstance(plans, list):
                    if isinstance(plans, dict) and "plans" in plans:
                        plans = plans["plans"]
                    else:
                        plans = [plans]
                
                # Process each plan to ensure it has the required fields
                processed_plans = []
                for plan in plans:
                    if isinstance(plan, dict):
                        # Ensure plan has target_genre and instruction
                        if "target_genre" not in plan:
                            plan["target_genre"] = "blog_post"  # Default genre
                        if "instruction" not in plan:
                            plan["instruction"] = "Transform the content into the target genre."
                        
                        # Add target_attributes if not present
                        if "target_attributes" not in plan:
                            plan["target_attributes"] = self.attribute_manager.get_base_attributes(plan["target_genre"])
                        
                        processed_plans.append(plan)
                
                return processed_plans[:self.num_plans]
            except json.JSONDecodeError:
                # If repair fails, create default plans
                return self._create_default_plans(semantic_core, original_attributes, user_instruction)
    
    def generate_plans_strategy_2(self, semantic_core: Union[str, Dict], original_attributes: Dict,
                                 user_instruction: str = None) -> List[Dict]:
        """
        Generate plans using Strategy 2.2.2 (Explicit Dimension Transformation).
        
        This strategy explicitly defines dimension space transformation (A_orig → A_temp)
        and generates high-level instructions.
        
        Args:
            semantic_core: Semantic core content
            original_attributes: Original attributes dictionary
            user_instruction: Optional user instruction
            
        Returns:
            List of plan dictionaries
        """
        # Load the appropriate prompt template based on whether user instruction is provided
        if user_instruction:
            template_path = os.path.join("prompts", "exploration", "strategy_2_with_instruction.txt")
            if not os.path.exists(template_path):
                template_path = os.path.join("prompts", "exploration", "strategy_2.txt")
        else:
            template_path = os.path.join("prompts", "exploration", "strategy_2.txt")
        
        # Load prompt template
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Convert semantic core to string if it's a structured object
        if isinstance(semantic_core, dict):
            semantic_core_str = json.dumps(semantic_core, indent=2)
        else:
            semantic_core_str = semantic_core
        
        # Format the prompt
        prompt = prompt_template.format(
            semantic_core=semantic_core_str,
            original_attributes=json.dumps(original_attributes, indent=2),
            user_instruction=user_instruction or "",
            num_plans=self.num_plans
        )
        
        # Call LLM to generate plans
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            # First, clean any potential markdown or extra text
            cleaned_response = self._clean_json_response(llm_response)
            plans = json.loads(cleaned_response)
            
            # Ensure plans is a list
            if not isinstance(plans, list):
                if isinstance(plans, dict) and "plans" in plans:
                    plans = plans["plans"]
                else:
                    plans = [plans]
            
            # Process each plan to ensure it has the required fields
            processed_plans = []
            for plan in plans:
                if isinstance(plan, dict):
                    # Ensure plan has target_genre, target_attributes, and instruction
                    if "target_genre" not in plan:
                        plan["target_genre"] = "blog_post"  # Default genre
                    if "target_attributes" not in plan:
                        plan["target_attributes"] = self.attribute_manager.get_base_attributes(plan["target_genre"])
                    if "instruction" not in plan:
                        plan["instruction"] = "Transform the content into the target genre."
                    
                    processed_plans.append(plan)
            
            return processed_plans[:self.num_plans]
        
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                plans = json.loads(repaired_json)
                
                # Ensure plans is a list
                if not isinstance(plans, list):
                    if isinstance(plans, dict) and "plans" in plans:
                        plans = plans["plans"]
                    else:
                        plans = [plans]
                
                # Process each plan to ensure it has the required fields
                processed_plans = []
                for plan in plans:
                    if isinstance(plan, dict):
                        # Ensure plan has target_genre, target_attributes, and instruction
                        if "target_genre" not in plan:
                            plan["target_genre"] = "blog_post"  # Default genre
                        if "target_attributes" not in plan:
                            plan["target_attributes"] = self.attribute_manager.get_base_attributes(plan["target_genre"])
                        if "instruction" not in plan:
                            plan["instruction"] = "Transform the content into the target genre."
                        
                        processed_plans.append(plan)
                
                return processed_plans[:self.num_plans]
            except json.JSONDecodeError:
                # If repair fails, create default plans
                return self._create_default_plans(semantic_core, original_attributes, user_instruction)
    
    def evaluate_plan_llm(self, plan: Dict, semantic_core: Union[str, Dict], 
                        original_attributes: Dict) -> Dict:
        """
        Evaluate a transformation plan using LLM.
        
        Args:
            plan: Transformation plan
            semantic_core: Semantic core content
            original_attributes: Original attributes dictionary
            
        Returns:
            Plan with evaluation added
        """
        # Load the evaluation prompt template
        template_path = os.path.join("prompts", "exploration", "evaluate_plan.txt")
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Convert semantic core to string if it's a structured object
        if isinstance(semantic_core, dict):
            semantic_core_str = json.dumps(semantic_core, indent=2)
        else:
            semantic_core_str = semantic_core
        
        # Format the prompt
        prompt = prompt_template.format(
            semantic_core=semantic_core_str,
            original_attributes=json.dumps(original_attributes, indent=2),
            plan=json.dumps(plan, indent=2)
        )
        
        # Call LLM to evaluate plan
        llm_response = self._call_llm(prompt, expect_json=True)
        
        try:
            # Try to parse as JSON
            # First, clean any potential markdown or extra text
            cleaned_response = self._clean_json_response(llm_response)
            evaluation = json.loads(cleaned_response)
            
            # Calculate overall score if not provided
            if "overall_score" not in evaluation:
                consistency_score = evaluation.get("consistency_score", 0.7)
                feasibility_score = evaluation.get("feasibility_score", 0.7)
                value_score = evaluation.get("value_score", 0.7)
                
                overall_score = (
                    consistency_score * self.consistency_weight +
                    feasibility_score * self.feasibility_weight +
                    value_score * self.value_weight
                )
                
                evaluation["overall_score"] = overall_score
            
            # Add evaluation to plan
            plan_copy = plan.copy()
            plan_copy["evaluation"] = evaluation
            
            return plan_copy
        
        except json.JSONDecodeError:
            # If parsing fails, try to repair JSON
            repaired_json = self._repair_json(llm_response)
            try:
                evaluation = json.loads(repaired_json)
                
                # Calculate overall score if not provided
                if "overall_score" not in evaluation:
                    consistency_score = evaluation.get("consistency_score", 0.7)
                    feasibility_score = evaluation.get("feasibility_score", 0.7)
                    value_score = evaluation.get("value_score", 0.7)
                    
                    overall_score = (
                        consistency_score * self.consistency_weight +
                        feasibility_score * self.feasibility_weight +
                        value_score * self.value_weight
                    )
                    
                    evaluation["overall_score"] = overall_score
                
                # Add evaluation to plan
                plan_copy = plan.copy()
                plan_copy["evaluation"] = evaluation
                
                return plan_copy
            except json.JSONDecodeError:
                # If repair fails, add default evaluation
                plan_copy = plan.copy()
                plan_copy["evaluation"] = {
                    "consistency_score": 0.7,
                    "feasibility_score": 0.7,
                    "value_score": 0.7,
                    "overall_score": 0.7,
                    "recommendation": "Proceed with caution"
                }
                
                return plan_copy
    
    def filter_plans(self, plans: List[Dict], threshold: float) -> List[Dict]:
        """
        Filter plans based on evaluation scores.
        
        Args:
            plans: List of evaluated plans
            threshold: Minimum overall score threshold
            
        Returns:
            Filtered list of plans
        """
        filtered_plans = []
        
        for plan in plans:
            overall_score = plan.get("evaluation", {}).get("overall_score", 0)
            if overall_score >= threshold:
                filtered_plans.append(plan)
        
        # Sort by overall score (descending)
        filtered_plans.sort(
            key=lambda p: p.get("evaluation", {}).get("overall_score", 0),
            reverse=True
        )
        
        return filtered_plans
    
    def _create_default_plans(self, semantic_core: Union[str, Dict], original_attributes: Dict,
                             user_instruction: str = None) -> List[Dict]:
        """
        Create default plans when LLM generation fails.
        
        Args:
            semantic_core: Semantic core content
            original_attributes: Original attributes dictionary
            user_instruction: Optional user instruction
            
        Returns:
            List of default plans
        """
        default_genres = ["blog_post", "news_article", "story"]
        default_plans = []
        
        for genre in default_genres[:self.num_plans]:
            # Create a basic instruction
            if user_instruction:
                instruction = f"Transform the content into a {genre} format while following this instruction: {user_instruction}"
            else:
                instruction = f"Transform the content into a {genre} format."
            
            # Create plan
            plan = {
                "target_genre": genre,
                "instruction": instruction,
                "target_attributes": self.attribute_manager.get_base_attributes(genre)
            }
            
            default_plans.append(plan)
        
        return default_plans
    
    def _clean_json_response(self, text: str) -> str:
        """
        Clean LLM response to extract only the JSON content.
        
        Args:
            text: LLM response text
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks if present
        text = re.sub(r'```(?:json)?\s*([\s\S]*?)\s*```', r'\1', text)
        
        # Remove any text before the first { or [ and after the last } or ]
        json_start = text.find('{')
        if json_start == -1:
            json_start = text.find('[')
        
        json_end = text.rfind('}')
        if json_end == -1 or text.rfind(']') > json_end:
            json_end = text.rfind(']')
        
        if json_start != -1 and json_end != -1:
            text = text[json_start:json_end + 1]
        
        return text
    
    def _repair_json(self, text: str) -> str:
        """
        Attempt to repair malformed JSON.
        
        Args:
            text: Potentially malformed JSON string
            
        Returns:
            Repaired JSON string
        """
        # First clean the response to extract only JSON content
        text = self._clean_json_response(text)
        
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
        
        # Fix JavaScript-style comments
        text = re.sub(r'//.*?\n', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        # Fix unquoted values that should be strings
        text = re.sub(r':(\s*)([a-zA-Z][a-zA-Z0-9_]*)(\s*[,}])', r':\1"\2"\3', text)
        
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
        system_message = "You are an exploration assistant that generates transformation plans."
        if expect_json:
            system_message += " Always respond with valid JSON. Do not include any explanations, markdown formatting, or text outside of the JSON structure."
        
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
