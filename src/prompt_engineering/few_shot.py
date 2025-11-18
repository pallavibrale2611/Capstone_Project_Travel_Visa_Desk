"""Few-shot learning utilities for prompt engineering."""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class FewShotExample:
    """Represents a few-shot learning example."""
    input: str
    output: str
    context: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FewShotManager:
    """Manages few-shot examples for prompt engineering."""
    
    def __init__(self):
        self.examples: List[FewShotExample] = []
    
    def add_example(self, input_text: str, output_text: str, context: str = "", metadata: Dict[str, Any] = None):
        """Add a few-shot example."""
        example = FewShotExample(
            input=input_text,
            output=output_text,
            context=context,
            metadata=metadata or {}
        )
        self.examples.append(example)
    
    def get_examples(self, count: int = None, filter_by: Dict[str, Any] = None) -> List[FewShotExample]:
        """Get examples with optional filtering and limiting."""
        filtered_examples = self.examples
        
        # Apply filters
        if filter_by:
            filtered_examples = [
                ex for ex in filtered_examples
                if all(ex.metadata.get(k) == v for k, v in filter_by.items())
            ]
        
        # Limit count
        if count:
            filtered_examples = filtered_examples[:count]
        
        return filtered_examples
    
    def format_examples(self, examples: List[FewShotExample] = None, format_template: str = None) -> str:
        """Format examples for inclusion in prompts."""
        if examples is None:
            examples = self.examples
        
        if not examples:
            return ""
        
        if format_template is None:
            format_template = "Input: {input}\nOutput: {output}"
        
        formatted_examples = []
        for example in examples:
            formatted = format_template.format(
                input=example.input,
                output=example.output,
                context=example.context
            )
            formatted_examples.append(formatted)
        
        return "\n\n".join(formatted_examples)
    
    def create_few_shot_prompt(self, 
                              user_input: str, 
                              system_prompt: str = "", 
                              example_count: int = 3,
                              format_template: str = None) -> str:
        """Create a complete few-shot prompt."""
        examples = self.get_examples(count=example_count)
        formatted_examples = self.format_examples(examples, format_template)
        
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(system_prompt)
        
        if formatted_examples:
            prompt_parts.append("Here are some examples:")
            prompt_parts.append(formatted_examples)
        
        prompt_parts.append(f"Now, please process this input:\nInput: {user_input}\nOutput:")
        
        return "\n\n".join(prompt_parts)


# Pre-defined few-shot examples for code generation
CODE_GENERATION_EXAMPLES = FewShotManager()

# Add some default examples
CODE_GENERATION_EXAMPLES.add_example(
    input="Create a Python function to calculate factorial",
    output="""def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)""",
    context="Basic recursion example",
    metadata={"language": "python", "complexity": "basic"}
)

CODE_GENERATION_EXAMPLES.add_example(
    input="Write a JavaScript function to validate email",
    output="""function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}""",
    context="Email validation using regex",
    metadata={"language": "javascript", "complexity": "intermediate"}
)

CODE_GENERATION_EXAMPLES.add_example(
    input="Create a Java class for a simple calculator",
    output="""public class Calculator {
    public double add(double a, double b) {
        return a + b;
    }
    
    public double subtract(double a, double b) {
        return a - b;
    }
    
    public double multiply(double a, double b) {
        return a * b;
    }
    
    public double divide(double a, double b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero");
        }
        return a / b;
    }
}""",
    context="Basic calculator with error handling",
    metadata={"language": "java", "complexity": "intermediate"}
)