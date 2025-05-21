# Self-Exploratory and Customizable Text Transformation Framework

This repository contains a comprehensive implementation of a self-exploratory and customizable text transformation framework. The system is designed to receive a source text's semantic core and its original multi-dimensional attributes, autonomously explore and generate diverse transformation plans, and produce high-quality target text based on selected plans.

## Overview

The framework operates on the fundamental principle expressed by the formula:
$$ \mathcal{S}_{\text{final}} = \text{GenerateText}(\mathcal{C}_{\text{sem}}, \mathcal{A}_{\text{final}}, \mathcal{I}) $$

Where:
- $\mathcal{C}_{sem}$ represents the semantic core extracted from the original text
- $\mathcal{A}_{final}$ represents the final target attributes, calculated as $\mathcal{A}_{\text{final}} = \text{CalFinalAttrs}(\mathcal{A}_{\text{base}}, \Delta\mathcal{A}_{\text{instruct}}, \mathcal{G}_{\text{target}})$
- $\mathcal{I}$ represents the high-level instructions for text generation

## Features

- **Highly Configurable**: All aspects of the system can be configured through external YAML files
- **Modular Architecture**: Clear separation of concerns with well-defined interfaces between components
- **Multiple Input Processing Methods**: Support for different approaches to handling semantic core and attributes
- **Diverse Exploration Strategies**: Different strategies for generating transformation plans
- **Customizable Generation**: Flexible text generation with support for human review and adjustments
- **Multi-dimensional Attribute Framework**: Comprehensive attribute system based on seven dimensions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text-transformation-framework.git
cd text-transformation-framework
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
project_root/
├── main.py                     # Main program entry
├── configs/                    # All configuration files
│   └── default_config.yaml     # Default configuration
├── src/                        # Core source code
│   ├── __init__.py
│   ├── pipeline.py             # Core pipeline
│   ├── input_handler/          # Handle C_sem and A_orig
│   │   ├── __init__.py
│   │   └── input_processor.py
│   ├── exploration_engine/     # Step 2: Exploration module
│   │   ├── __init__.py
│   │   └── exploration_processor.py
│   ├── generation_engine/      # Step 3: Generation module
│   │   ├── __init__.py
│   │   └── generation_processor.py
│   ├── attribute_manager/      # Manage dimensional attributes
│   │   ├── __init__.py
│   │   └── dimensions.py
│   └── utils/                  # Common tools
│       ├── __init__.py
│       └── config_manager.py
├── prompts/                    # Prompt template files
│   ├── extraction/
│   ├── exploration/
│   └── generation/
├── data/                       # Experimental data
├── notebooks/                  # Analysis and visualization
├── tests/                      # Tests
└── requirements.txt            # Project dependencies
```

## Usage

### Basic Usage

```bash
python main.py --input input.json --output output.json
```

### With Human Review

```bash
python main.py --input input.json --output output.json --human-review
```

### With Custom Configuration

```bash
python main.py --input input.json --output output.json --config configs/custom_config.yaml
```

### Input Format

The input JSON file should contain one or more of the following fields:

```json
{
  "original_text": "Text content to transform",
  "semantic_core": "Extracted semantic core (optional)",
  "original_attributes": {
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
  },
  "user_instruction": "Optional instruction for transformation"
}
```

### Output Format

The output JSON file will contain:

```json
{
  "semantic_core": "Extracted or provided semantic core",
  "original_attributes": "Original attributes",
  "transformation_plans": [
    {
      "target_genre": "blog_post",
      "target_attributes": { ... },
      "instruction": "Transform into a blog post...",
      "evaluation": {
        "consistency_score": 0.8,
        "feasibility_score": 0.7,
        "value_score": 0.75,
        "overall_score": 0.75,
        "recommendation": "Recommended"
      }
    },
    ...
  ],
  "selected_plan": { ... },
  "final_text": "Generated text based on selected plan"
}
```

## Configuration Options

The framework is highly configurable through YAML configuration files. Here are the main configuration options:

### Input Handler Configuration

```yaml
input_handler:
  semantic_core_method: "option_a"  # option_a, option_b, option_c
  attributes_method: "option_b"     # option_a, option_b
```

- **semantic_core_method**:
  - **option_a**: Direct acceptance of user-provided plain text as semantic core
  - **option_b**: Support for receiving or generating structured semantic core
  - **option_c**: Accept original text and extract both semantic core and attributes

- **attributes_method**:
  - **option_a**: Direct user provision of structured attributes
  - **option_b**: Extract or validate attributes from text or semantic core

### Exploration Engine Configuration

```yaml
exploration_engine:
  strategy: "strategy_2"            # strategy_1, strategy_2
  evaluation:
    consistency_weight: 0.3
    feasibility_weight: 0.4
    value_weight: 0.3
    threshold: 0.6
  num_plans: 3
```

- **strategy**:
  - **strategy_1**: Direct suggestion of target genres and instructions
  - **strategy_2**: Explicit dimension transformation

- **evaluation**: Weights and threshold for evaluating transformation plans

- **num_plans**: Number of transformation plans to generate

### Generation Engine Configuration

```yaml
generation_engine:
  llm_model: "gpt-4"
  post_processing: true
  quality_threshold: 0.7
```

- **llm_model**: Language model to use for text generation
- **post_processing**: Whether to perform post-processing on generated text
- **quality_threshold**: Threshold for quality evaluation

### Attribute Manager Configuration

```yaml
attribute_manager:
  dimensions:
    function_purpose:
      active: true
      weight: 1.0
    audience_context:
      active: true
      weight: 1.0
    # ... other dimensions
```

- **dimensions**: Configuration for each dimension, including activation and weight

## Experimental Results

The framework has been evaluated on a diverse set of input texts, with experiments focusing on:

1. **Semantic Core Representation Methods**: Comparing different approaches to handling semantic core
2. **Exploration Strategies**: Comparing different strategies for generating transformation plans
3. **Dimension Weighting**: Evaluating the impact of different dimension weightings
4. **LLM Model Comparison**: Comparing different language models for text generation
5. **End-to-End System Evaluation**: Evaluating the complete system with optimal configurations

Detailed results and analysis can be found in the research report.

## Future Work

- Improved semantic core extraction with more sophisticated NLP techniques
- Enhanced exploration strategies with reinforcement learning
- More comprehensive evaluation metrics for generated text
- Integration with additional language models
- User interface for interactive exploration and customization

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This research was conducted as part of a study on self-exploratory and customizable text transformation frameworks.
- Special thanks to the research team for their guidance and support.
