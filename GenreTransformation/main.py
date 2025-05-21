"""
Main entry point for the text transformation framework.

This script provides a command-line interface to the text transformation framework.
"""

import os
import sys
import json
import argparse
from src.pipeline import TransformationPipeline


def main():
    """Main entry point for the text transformation framework."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Text Transformation Framework")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--input", type=str, required=True, help="Path to input text file")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--instruction", type=str, help="User instruction for transformation")
    parser.add_argument("--plan-index", type=int, help="Index of transformation plan to use")
    parser.add_argument("--list-plans", action="store_true", help="List transformation plans and exit")
    parser.add_argument("--save-all", action="store_true", help="Save all intermediate results")
    parser.add_argument("--api-key", type=str, help="OpenAI API key (overrides config and env var)")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    # Read input text
    with open(args.input, 'r', encoding='utf-8') as f:
        source_text = f.read()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set API key if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    
    # Initialize pipeline
    pipeline = TransformationPipeline(args.config)
    
    try:
        # Step 1: Extract semantic core and attributes
        print("Step 1: Extracting semantic core and attributes...")
        extraction_result = pipeline.extract(source_text)
        
        if args.save_all:
            # Save extraction results
            with open(os.path.join(args.output_dir, "semantic_core.json"), 'w') as f:
                if isinstance(extraction_result["semantic_core"], dict):
                    json.dump(extraction_result["semantic_core"], f, indent=2)
                else:
                    f.write(extraction_result["semantic_core"])
            
            with open(os.path.join(args.output_dir, "original_attributes.json"), 'w') as f:
                json.dump(extraction_result["attributes"], f, indent=2)
        
        # Step 2: Generate transformation plans
        print("Step 2: Generating transformation plans...")
        transformation_plans = pipeline.explore(args.instruction)
        
        if args.list_plans:
            # Print plans and exit
            print("\nTransformation Plans:")
            for i, plan in enumerate(transformation_plans):
                print(f"\nPlan {i}:")
                print(f"  Target Genre: {plan.get('target_genre', 'N/A')}")
                print(f"  Instruction: {plan.get('instruction', 'N/A')}")
                if "evaluation" in plan:
                    print(f"  Overall Score: {plan['evaluation'].get('overall_score', 'N/A')}")
                    print(f"  Recommendation: {plan['evaluation'].get('recommendation', 'N/A')}")
            sys.exit(0)
        
        if args.save_all:
            # Save transformation plans
            with open(os.path.join(args.output_dir, "transformation_plans.json"), 'w') as f:
                json.dump(transformation_plans, f, indent=2)
        
        # Select plan
        if args.plan_index is not None:
            selected_plan = pipeline.select_plan(args.plan_index)
        else:
            selected_plan = pipeline.select_plan(0)  # Default to first plan
        
        print(f"\nSelected Plan:")
        print(f"  Target Genre: {selected_plan.get('target_genre', 'N/A')}")
        print(f"  Instruction: {selected_plan.get('instruction', 'N/A')}")
        
        if args.save_all:
            # Save selected plan
            with open(os.path.join(args.output_dir, "selected_plan.json"), 'w') as f:
                json.dump(selected_plan, f, indent=2)
        
        # Step 3: Generate final text
        print("\nStep 3: Generating final text...")
        final_text = pipeline.generate()
        
        # Save final text
        output_path = os.path.join(args.output_dir, "final_text.md")
        with open(output_path, 'w') as f:
            f.write(final_text)
        
        print(f"\nTransformation complete. Output saved to {output_path}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
