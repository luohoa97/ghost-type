from typing import Dict, Any, List


class Prompts:
    """Manages prompts for routing and processing."""
    
    def __init__(self):
        self._prompts = self._build_prompts()
    
    def _build_prompts(self) -> Dict[str, str]:
        """Build prompt templates."""
        return {
            "router": """You are a voice command router. Convert the following voice transcript into a JSON array of actions.

Available actions:
- insert_text: {"type": "insert_text", "text": "text to insert"}
- press_key: {"type": "press_key", "key": "key name"}
- undo_last_chunk: {"type": "undo_last_chunk"}
- delete_last_word: {"type": "delete_last_word"}

Rules:
- Convert "new line" to press_key with key "Enter"
- Convert "tab" to press_key with key "Tab"
- Convert "backspace" to press_key with key "BackSpace"
- Convert "scrap that", "scratch that", "undo that" to undo_last_chunk
- Convert "delete last word" to delete_last_word
- Keep all other text as insert_text actions
- Return only valid JSON

Transcript:
{transcript}""",
            "strong_llm": """You are a powerful assistant. Process the following request:

{request}

Context:
{context}

Instructions:
{instructions}""",
            "code_generation": """Generate code for the following request:

{request}

Language: {language}
Context: {context}

Return only the code, no explanations.""",
            "table_generation": """Generate a Markdown table for the following request:

{request}

Context: {context}

Return only the table, no explanations.""",
            "summarize": """Summarize the following text:

{text}

Return only the summary, no explanations.""",
            "rewrite": """Rewrite the following text:

{text}

Style: {style}
Return only the rewritten text, no explanations.""",
        }
    
    def get_router_prompt(self, transcript: str) -> str:
        """Get router prompt."""
        return self._prompts["router"].format(transcript=transcript)
    
    def get_strong_llm_prompt(self, request: str, context: str, instructions: str) -> str:
        """Get strong LLM prompt."""
        return self._prompts["strong_llm"].format(
            request=request,
            context=context,
            instructions=instructions
        )
    
    def get_code_prompt(self, request: str, language: str, context: str) -> str:
        """Get code generation prompt."""
        return self._prompts["code_generation"].format(
            request=request,
            language=language,
            context=context
        )
    
    def get_table_prompt(self, request: str, context: str) -> str:
        """Get table generation prompt."""
        return self._prompts["table_generation"].format(
            request=request,
            context=context
        )
    
    def get_summarize_prompt(self, text: str) -> str:
        """Get summarize prompt."""
        return self._prompts["summarize"].format(text=text)
    
    def get_rewrite_prompt(self, text: str, style: str) -> str:
        """Get rewrite prompt."""
        return self._prompts["rewrite"].format(
            text=text,
            style=style
        )
