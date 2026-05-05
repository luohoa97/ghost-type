"""Prompt builders for router."""
from typing import List, Dict, Any, Optional


class PromptBuilder:
    """Builds prompts for LLM routing."""
    
    def __init__(self):
        self._system_prompts = self._create_system_prompts()
    
    def _create_system_prompts(self) -> Dict[str, str]:
        """Create system prompts for different routes."""
        return {
            "routing": """You are a voice command router. Your task is to analyze transcribed text and determine the appropriate action.

Available routes:
- dictation: Simple text insertion
- local: Local commands like "new line", "tab", "scrap that"
- fast_llm: Quick LLM operations
- strong_llm: Complex LLM operations
- private_llm: Private LLM operations
- agent: Agent operations

Return a JSON object with:
- route: The selected route
- actions: Array of actions to execute
- confidence: Your confidence level (0-1)
- context_required: Whether context is needed
- output_action: Optional output action
- safety_metadata: Any safety considerations

Return ONLY valid JSON.""",
            
            "strong_llm": """You are a powerful language model assistant. Your task is to complete the user's request.

Available modes:
- summarize: Summarize the given text
- rewrite: Rewrite the given text
- prompt: Generate a prompt
- table: Generate a Markdown table
- code: Generate code
- terminal: Generate a terminal command (never execute)

Return ONLY the requested output, nothing else.""",
            
            "private_llm": """You are a private language model assistant. Your task is to complete the user's request while maintaining privacy.

Return ONLY the requested output, nothing else.""",
            
            "agent": """You are an intelligent agent. Your task is to complete the user's request using available tools.

Return ONLY the requested output, nothing else.""",
        }
    
    def build_routing_prompt(self, text: str) -> str:
        """Build routing prompt."""
        return f"""{self._system_prompts["routing"]}

Transcribed text: "{text}"

Return ONLY valid JSON."""
    
    def build_strong_llm_prompt(
        self,
        text: str,
        mode: str = "summarize",
        context: Optional[str] = None
    ) -> str:
        """Build strong LLM prompt."""
        system = self._system_prompts["strong_llm"]
        
        if context:
            return f"""{system}

Mode: {mode}
Context: {context}
Text: "{text}"

Return ONLY the requested output."""
        else:
            return f"""{system}

Mode: {mode}
Text: "{text}"

Return ONLY the requested output."""
    
    def build_private_llm_prompt(self, text: str) -> str:
        """Build private LLM prompt."""
        return f"""{self._system_prompts["private_llm"]}

Text: "{text}"

Return ONLY the requested output."""
    
    def build_agent_prompt(
        self,
        text: str,
        tools: Optional[List[str]] = None
    ) -> str:
        """Build agent prompt."""
        system = self._system_prompts["agent"]
        
        if tools:
            tools_str = ", ".join(tools)
            return f"""{system}

Available tools: {tools_str}
Request: "{text}"

Return ONLY the requested output."""
        else:
            return f"""{system}

Request: "{text}"

Return ONLY the requested output."""
    
    def build_summarize_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build summarize prompt."""
        return self.build_strong_llm_prompt(text, "summarize", context)
    
    def build_rewrite_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build rewrite prompt."""
        return self.build_strong_llm_prompt(text, "rewrite", context)
    
    def build_table_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build table generation prompt."""
        return self.build_strong_llm_prompt(text, "table", context)
    
    def build_code_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build code generation prompt."""
        return self.build_strong_llm_prompt(text, "code", context)
    
    def build_terminal_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build terminal command generation prompt."""
        return self.build_strong_llm_prompt(text, "terminal", context)
