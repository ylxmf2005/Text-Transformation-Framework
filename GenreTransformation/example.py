"""
Example script to demonstrate the text transformation framework.

This script shows how to use the framework to transform a sample text.
"""

import os
import sys
import json
from src.pipeline import TransformationPipeline

def main():
    """Run an example transformation."""
    print("Text Transformation Framework - Example")
    print("---------------------------------------")
    
    # Initialize pipeline with default configuration
    pipeline = TransformationPipeline()
    
    # Sample text path
    sample_text_path = os.path.join("example_data", "sample_text.txt")
    
    # Check if sample text exists
    if not os.path.exists(sample_text_path):
        print(f"Error: Sample text not found at {sample_text_path}")
        sys.exit(1)
    
    # Read sample text
    with open(sample_text_path, 'r', encoding='utf-8') as f:
        source_text = f.read()
    
    print(f"\nSource text length: {len(source_text)} characters")
    
    # Create output directory if it doesn't exist
    output_dir = "example_output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Extract semantic core and attributes
        print("\nStep 1: Extracting semantic core and attributes...")
        extraction_result = pipeline.extract(source_text)
        
        # Save extraction results
        with open(os.path.join(output_dir, "semantic_core.json"), 'w') as f:
            if isinstance(extraction_result["semantic_core"], dict):
                json.dump(extraction_result["semantic_core"], f, indent=2)
            else:
                f.write(extraction_result["semantic_core"])
        
        with open(os.path.join(output_dir, "original_attributes.json"), 'w') as f:
            json.dump(extraction_result["attributes"], f, indent=2)
        
        print("Extraction complete. Results saved to example_output directory.")
        
        # Step 2: Generate transformation plans
        print("\nStep 2: Generating transformation plans...")
        user_instruction = "Transform this into a more engaging and persuasive format for a younger audience."
        transformation_plans = pipeline.explore(user_instruction)
        
        # Save transformation plans
        with open(os.path.join(output_dir, "transformation_plans.json"), 'w') as f:
            json.dump(transformation_plans, f, indent=2)
        
        print(f"Generated {len(transformation_plans)} transformation plans.")
        
        # Print plans
        for i, plan in enumerate(transformation_plans):
            print(f"\nPlan {i}:")
            print(f"  Target Genre: {plan.get('target_genre', 'N/A')}")
            print(f"  Instruction: {plan.get('instruction', 'N/A')}")
            if "evaluation" in plan:
                print(f"  Overall Score: {plan['evaluation'].get('overall_score', 'N/A')}")
        
        # Select first plan
        selected_plan = pipeline.select_plan(0)
        
        print(f"\nSelected Plan:")
        print(f"  Target Genre: {selected_plan.get('target_genre', 'N/A')}")
        print(f"  Instruction: {selected_plan.get('instruction', 'N/A')}")
        
        # Save selected plan
        with open(os.path.join(output_dir, "selected_plan.json"), 'w') as f:
            json.dump(selected_plan, f, indent=2)
        
        # Step 3: Generate final text
        print("\nStep 3: Generating final text...")
        final_text = pipeline.generate()
        
        # Save final text
        output_path = os.path.join(output_dir, "final_text.md")
        with open(output_path, 'w') as f:
            f.write(final_text)
        
        print(f"\nTransformation complete. Final text saved to {output_path}")
        print(f"Final text length: {len(final_text)} characters")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
