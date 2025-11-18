"""Chain prompting utilities for complex multi-step tasks."""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ChainStepType(Enum):
    """Types of chain steps."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    GENERATION = "generation"
    VALIDATION = "validation"
    REFINEMENT = "refinement"


@dataclass
class ChainStep:
    """Represents a step in a prompt chain."""
    name: str
    step_type: ChainStepType
    prompt_template: str
    dependencies: List[str] = None
    validation_fn: Optional[Callable] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class PromptChain:
    """Manages a chain of prompts for complex tasks."""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: Dict[str, ChainStep] = {}
        self.execution_order: List[str] = []
        self.results: Dict[str, Any] = {}
    
    def add_step(self, step: ChainStep):
        """Add a step to the chain."""
        self.steps[step.name] = step
        self._update_execution_order()
    
    def _update_execution_order(self):
        """Update the execution order based on dependencies."""
        # Simple topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(step_name):
            if step_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {step_name}")
            if step_name in visited:
                return
            
            temp_visited.add(step_name)
            step = self.steps[step_name]
            
            for dep in step.dependencies:
                if dep in self.steps:
                    visit(dep)
            
            temp_visited.remove(step_name)
            visited.add(step_name)
            order.append(step_name)
        
        for step_name in self.steps:
            if step_name not in visited:
                visit(step_name)
        
        self.execution_order = order
    
    def format_step_prompt(self, step_name: str, context: Dict[str, Any] = None) -> str:
        """Format a step's prompt with context and previous results."""
        if step_name not in self.steps:
            raise ValueError(f"Step {step_name} not found")
        
        step = self.steps[step_name]
        format_context = {
            "results": self.results,
            "context": context or {},
        }
        
        # Add dependency results
        for dep in step.dependencies:
            if dep in self.results:
                format_context[f"{dep}_result"] = self.results[dep]
        
        try:
            return step.prompt_template.format(**format_context)
        except KeyError as e:
            raise ValueError(f"Missing format variable {e} for step {step_name}")
    
    def execute_step(self, step_name: str, result: Any, context: Dict[str, Any] = None):
        """Execute a step and store its result."""
        if step_name not in self.steps:
            raise ValueError(f"Step {step_name} not found")
        
        step = self.steps[step_name]
        
        # Validate dependencies
        for dep in step.dependencies:
            if dep not in self.results:
                raise ValueError(f"Dependency {dep} not executed for step {step_name}")
        
        # Validate result if validation function provided
        if step.validation_fn and not step.validation_fn(result):
            raise ValueError(f"Validation failed for step {step_name}")
        
        self.results[step_name] = result
    
    def get_next_step(self) -> Optional[str]:
        """Get the next step to execute."""
        for step_name in self.execution_order:
            if step_name not in self.results:
                # Check if all dependencies are satisfied
                step = self.steps[step_name]
                if all(dep in self.results for dep in step.dependencies):
                    return step_name
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps have been executed."""
        return len(self.results) == len(self.steps)
    
    def get_final_result(self) -> Any:
        """Get the final result of the chain."""
        if not self.is_complete():
            raise ValueError("Chain is not complete")
        
        # Return the result of the last step in execution order
        if self.execution_order:
            return self.results[self.execution_order[-1]]
        return None


# Pre-defined chain for code generation
def create_code_generation_chain() -> PromptChain:
    """Create a standard code generation chain."""
    chain = PromptChain("code_generation")
    
    # Step 1: Analyze requirements
    analysis_step = ChainStep(
        name="analysis",
        step_type=ChainStepType.ANALYSIS,
        prompt_template="""Analyze the following code generation request:

Request: {context[user_request]}

Please provide:
1. Programming language required
2. Key functionality needed
3. Input/output requirements
4. Any constraints or special considerations
5. Complexity level (basic/intermediate/advanced)

Analysis:"""
    )
    
    # Step 2: Create implementation plan
    planning_step = ChainStep(
        name="planning",
        step_type=ChainStepType.PLANNING,
        prompt_template="""Based on the analysis:

{analysis_result}

Create a detailed implementation plan:
1. Main components/functions needed
2. Data structures required
3. Algorithm approach
4. Error handling strategy
5. Testing considerations

Implementation Plan:""",
        dependencies=["analysis"]
    )
    
    # Step 3: Generate code
    generation_step = ChainStep(
        name="generation",
        step_type=ChainStepType.GENERATION,
        prompt_template="""Based on the analysis and plan:

Analysis: {analysis_result}
Plan: {planning_result}

Generate the complete, production-ready code with:
1. Proper error handling
2. Clear documentation/comments
3. Appropriate variable names
4. Efficient implementation

Code:""",
        dependencies=["analysis", "planning"]
    )
    
    # Step 4: Validate and refine
    validation_step = ChainStep(
        name="validation",
        step_type=ChainStepType.VALIDATION,
        prompt_template="""Review the generated code:

{generation_result}

Check for:
1. Syntax correctness
2. Logic errors
3. Edge cases handling
4. Code quality and best practices
5. Performance considerations

Provide validation results and any necessary improvements:""",
        dependencies=["generation"]
    )
    
    chain.add_step(analysis_step)
    chain.add_step(planning_step)
    chain.add_step(generation_step)
    chain.add_step(validation_step)
    
    return chain