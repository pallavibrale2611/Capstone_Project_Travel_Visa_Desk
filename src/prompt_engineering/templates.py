"""Prompt templates and management."""

from typing import Dict, Any, List
from config import get_prompt_templates


def get_system_instruction(instruction_type: str = "code_generator") -> str:
    """Get system instruction by type."""
    config = get_prompt_templates()
    return config["system_instructions"].get(instruction_type, "")


def get_prompt_template(template_name: str) -> str:
    """Get a specific prompt template."""
    config = get_prompt_templates()
    templates = config.get("prompt_templates", [])
    
    # For now, return the first template that matches or contains the name
    for template in templates:
        if template_name.lower() in template.lower():
            return template
    
    return templates[0] if templates else ""


def format_prompt_template(template: str, variables: Dict[str, Any]) -> str:
    """Format a prompt template with variables."""
    formatted = template
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        formatted = formatted.replace(placeholder, str(value))
    return formatted


def get_examples() -> List[str]:
    """Get example prompts."""
    config = get_prompt_templates()
    return config.get("examples", [])


class PromptBuilder:
    """Builder class for constructing prompts."""
    
    def __init__(self):
        self.config = get_prompt_templates()
        self.prompt_parts = []
    
    def add_system_instruction(self, instruction_type: str = "code_generator"):
        """Add system instruction to the prompt."""
        instruction = get_system_instruction(instruction_type)
        if instruction:
            self.prompt_parts.append(instruction)
        return self
    
    def add_template(self, template_name: str, variables: Dict[str, Any] = None):
        """Add a formatted template to the prompt."""
        template = get_prompt_template(template_name)
        if template and variables:
            formatted = format_prompt_template(template, variables)
            self.prompt_parts.append(formatted)
        elif template:
            self.prompt_parts.append(template)
        return self
    
    def add_examples(self, count: int = None):
        """Add examples to the prompt."""
        examples = get_examples()
        if count:
            examples = examples[:count]
        
        if examples:
            examples_text = "Examples:\n" + "\n".join(f"- {ex}" for ex in examples)
            self.prompt_parts.append(examples_text)
        return self
    
    def add_custom_text(self, text: str):
        """Add custom text to the prompt."""
        self.prompt_parts.append(text)
        return self
    
    def build(self) -> str:
        """Build the final prompt."""
        return "\n\n".join(self.prompt_parts)
    
    def clear(self):
        """Clear the prompt parts."""
        self.prompt_parts = []
        return self