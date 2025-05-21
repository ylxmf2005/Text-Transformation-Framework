"""
Generation Processor Module

This module implements the GenerationEngine class which produces high-quality final text
based on the semantic core, final attributes, and instructions.
"""

import os
import json
import requests
import re
from typing import Dict, Any, Optional, Union


class GenerationEngine:
    """
    Produces high-quality final text based on the semantic core, final attributes, and instructions.
    
    Supports:
    - Different LLM models through configuration
    - Configurable prompt templates
    - Human review and decision integration
    - Optional post-processing for quality assessment and optimization
    """
    
    def __init__(self, config_manager, attribute_manager):
        """
        Initialize the GenerationEngine with configuration and attribute manager.
        
        Args:
            config_manager: Configuration manager instance
            attribute_manager: Attribute manager instance
        """
        self.config_manager = config_manager
        self.attribute_manager = attribute_manager
        
        # Get LLM configuration
        self.llm_config = config_manager.get_value("generation_engine.llm_config", {})
        self.post_processing = config_manager.get_value("generation_engine.post_processing", True)
        self.quality_threshold = config_manager.get_value("generation_engine.quality_threshold", 0.7)
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
    
    def generate(self, semantic_core: Union[str, Dict], final_attributes: Dict, 
                instruction: str) -> str:
        """
        Generate final text.
        
        Args:
            semantic_core: Semantic core content (string or structured object)
            final_attributes: Final attributes dictionary
            instruction: High-level instruction
            
        Returns:
            Generated text
        """
        # Prepare prompt for LLM
        prompt = self.prepare_prompt(semantic_core, final_attributes, instruction)
        
        # Call LLM with prompt
        generated_text = self.call_llm(prompt)
        
        # Perform optional post-processing
        if self.post_processing:
            generated_text = self.post_process(
                generated_text, semantic_core, final_attributes, instruction)
        
        return generated_text
    
    def prepare_prompt(self, semantic_core: Union[str, Dict], final_attributes: Dict, 
                      instruction: str) -> str:
        """
        Prepare prompt for LLM.
        
        Args:
            semantic_core: Semantic core content
            final_attributes: Final attributes dictionary
            instruction: High-level instruction
            
        Returns:
            Formatted prompt string
        """
        # Convert semantic core to string if it's a structured object
        if isinstance(semantic_core, dict):
            semantic_core_str = json.dumps(semantic_core, indent=2)
        else:
            semantic_core_str = semantic_core
        
        # Extract specific attributes for prompt
        target_genre = final_attributes.get("target_genre", "")
        function_purpose = final_attributes.get("function_purpose", "")
        audience_context = final_attributes.get("audience_context", "")
        structure_organization = final_attributes.get("structure_organization", "")
        strategy = final_attributes.get("strategy", "")
        conventions = final_attributes.get("conventions", "")
        
        # Extract linguistic features
        ling_features = final_attributes.get("linguistic_features", {})
        information_density = ling_features.get("information_density", "medium")
        interactivity = ling_features.get("interactivity", "medium")
        formality = ling_features.get("tone", "semi_formal")  # Using tone as formality
        tone = ling_features.get("tone", "neutral")
        sentiment = ling_features.get("emotion", "neutral")  # Using emotion as sentiment
        
        # Format the prompt using the template
        prompt = self.prompt_template.format(
            semantic_core=semantic_core_str,
            target_genre=target_genre,
            function_purpose=function_purpose,
            audience_context=audience_context,
            structure_organization=structure_organization,
            strategy=strategy,
            conventions=conventions,
            information_density=information_density,
            interactivity=interactivity,
            formality=formality,
            tone=tone,
            sentiment=sentiment,
            instruction=instruction
        )
        
        return prompt
    
    def call_llm(self, prompt: str, expect_json: bool = False) -> str:
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
        temperature = self.llm_config.get("temperature", 1.0)
        max_tokens = self.llm_config.get("max_tokens", 2000)
        top_p = self.llm_config.get("top_p", 1.0)
        frequency_penalty = self.llm_config.get("frequency_penalty", 0.0)
        presence_penalty = self.llm_config.get("presence_penalty", 0.0)
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Prepare system message based on whether we expect JSON
        system_message = "You are a text transformation assistant that generates high-quality content based on provided semantic core, attributes, and instructions."
        if expect_json:
            system_message += " Always respond with valid JSON. Do not include any explanations, markdown formatting, or text outside of the JSON structure."
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty
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
            return "{}" if expect_json else self._generate_fallback_response(prompt)
    
    def post_process(self, text: str, semantic_core: Union[str, Dict], 
                    final_attributes: Dict, instruction: str) -> str:
        """
        Perform optional post-processing.
        
        Args:
            text: Generated text
            semantic_core: Original semantic core
            final_attributes: Final attributes used for generation
            instruction: High-level instruction used for generation
            
        Returns:
            Post-processed text
        """
        # Evaluate quality
        quality = self.evaluate_quality(text, semantic_core, final_attributes, instruction)
        
        # If quality is below threshold, attempt improvements
        if quality["overall_score"] < self.quality_threshold:
            # Call LLM again with refined instructions
            refinement_prompt = self._create_refinement_prompt(text, semantic_core, final_attributes, instruction, quality)
            refined_text = self.call_llm(refinement_prompt)
            
            # If refinement succeeded, use refined text
            if refined_text and len(refined_text) > len(text) * 0.5:
                return refined_text
        
        return text
    
    def evaluate_quality(self, text: str, semantic_core: Union[str, Dict], 
                        final_attributes: Dict, instruction: str) -> Dict:
        """
        Evaluate quality of generated text.
        
        Args:
            text: Generated text
            semantic_core: Original semantic core
            final_attributes: Final attributes used for generation
            instruction: High-level instruction used for generation
            
        Returns:
            Dictionary with quality evaluation scores
        """
        # Load the evaluation prompt template
        template_path = os.path.join("prompts", "generation", "evaluate_quality.txt")
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
            target_attributes=json.dumps(final_attributes, indent=2),
            instruction=instruction,
            text=text
        )
        
        try:
            # Call LLM for evaluation
            eval_result = self.call_llm(prompt, expect_json=True)
            
            # Parse evaluation result
            try:
                # First, clean any potential markdown or extra text
                cleaned_response = self._clean_json_response(eval_result)
                # Try to parse as JSON
                scores = json.loads(cleaned_response)
                
                # Ensure all required scores are present
                required_scores = ["semantic_fidelity", "attribute_conformity", "instruction_adherence", "fluency"]
                for score in required_scores:
                    if score not in scores:
                        scores[score] = 0.7  # Default score
                
                # Calculate overall score if not provided
                if "overall_score" not in scores:
                    scores["overall_score"] = sum(scores[score] for score in required_scores) / len(required_scores)
                
                return scores
            except json.JSONDecodeError:
                # If parsing fails, try to repair JSON
                repaired_json = self._repair_json(eval_result)
                try:
                    scores = json.loads(repaired_json)
                    
                    # Ensure all required scores are present
                    required_scores = ["semantic_fidelity", "attribute_conformity", "instruction_adherence", "fluency"]
                    for score in required_scores:
                        if score not in scores:
                            scores[score] = 0.7  # Default score
                    
                    # Calculate overall score if not provided
                    if "overall_score" not in scores:
                        scores["overall_score"] = sum(scores[score] for score in required_scores) / len(required_scores)
                    
                    return scores
                except json.JSONDecodeError:
                    # If repair fails, use default scores
                    print("Failed to parse evaluation result as JSON")
                    return self._default_evaluation_scores()
        except Exception as e:
            # If evaluation fails, use default scores
            print(f"Evaluation failed: {e}")
            return self._default_evaluation_scores()
    
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
    
    def _default_evaluation_scores(self) -> Dict:
        """Return default evaluation scores."""
        return {
            "semantic_fidelity": 0.75,
            "attribute_conformity": 0.75,
            "instruction_adherence": 0.75,
            "fluency": 0.8,
            "overall_score": 0.75
        }
    
    def _create_refinement_prompt(self, text: str, semantic_core: Union[str, Dict], 
                                final_attributes: Dict, instruction: str, quality: Dict) -> str:
        """Create prompt for text refinement."""
        # Load the refinement prompt template
        template_path = os.path.join("prompts", "generation", "refine_text.txt")
        with open(template_path, 'r') as f:
            prompt_template = f.read()
        
        # Convert semantic core to string if it's a structured object
        if isinstance(semantic_core, dict):
            semantic_core_str = json.dumps(semantic_core, indent=2)
        else:
            semantic_core_str = semantic_core
        
        # Identify areas for improvement
        improvements = []
        if quality.get("semantic_fidelity", 1.0) < 0.7:
            improvements.append("Improve semantic fidelity by ensuring all key information from the semantic core is included")
        if quality.get("attribute_conformity", 1.0) < 0.7:
            improvements.append("Better align with target attributes, especially regarding tone, style, and structure")
        if quality.get("instruction_adherence", 1.0) < 0.7:
            improvements.append(f"Follow the instruction more closely: '{instruction}'")
        if quality.get("fluency", 1.0) < 0.7:
            improvements.append("Improve overall fluency, coherence, and readability")
        
        improvements_str = "\n".join(f"- {imp}" for imp in improvements)
        
        # Format the prompt
        prompt = prompt_template.format(
            semantic_core=semantic_core_str,
            target_attributes=json.dumps(final_attributes, indent=2),
            instruction=instruction,
            text=text,
            quality_issues=quality.get("comments", ""),
            improvements=improvements_str
        )
        
        return prompt
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """
        Generate a fallback response when API call fails.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Fallback generated text
        """
        # Extract key information from prompt to create a relevant response
        lines = prompt.split('\n')
        genre = ""
        audience = ""
        tone = ""
        instruction = ""
        
        for line in lines:
            if "Target Genre:" in line:
                genre = line.split('"')[1]
            elif "Audience/Context:" in line:
                audience = line.split('"')[1]
            elif "Tone:" in line:
                tone = line.split('"')[1]
            elif "Instruction:" in line:
                instruction = line.split('"')[1]
        
        # Create a simple fallback response
        fallback = f"[This is a fallback response due to API failure]\n\n"
        
        if genre:
            fallback += f"Content in {genre} format"
        if audience:
            fallback += f" for {audience}"
        if tone:
            fallback += f" with a {tone} tone"
        fallback += ".\n\n"
        
        if instruction:
            fallback += f"Following the instruction: {instruction}\n\n"
        
        fallback += "The system was unable to generate the full content due to an API error. Please try again later."
        
        return fallback
    
    def _load_prompt_template(self) -> str:
        """Load the generation prompt template."""
        template_path = os.path.join("prompts", "generation", "default_template.txt")
        
        with open(template_path, 'r') as f:
            return f.read()
        