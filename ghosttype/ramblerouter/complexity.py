"""Complexity analyzer for router."""
from typing import List, Dict, Any, Optional
import re


class ComplexityAnalyzer:
    """Analyzes text complexity for routing decisions."""
    
    def __init__(self):
        self._complexity_threshold = 0.5
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text complexity."""
        return {
            "length": len(text),
            "word_count": len(text.split()),
            "sentence_count": self._count_sentences(text),
            "complexity_score": self._calculate_complexity(text),
            "requires_llm": self._requires_llm(text),
            "has_commands": self._has_commands(text),
        }
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score (0-1)."""
        if not text:
            return 0.0
        
        # Factors:
        # 1. Sentence length
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        # 2. Sentence complexity
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len(sentences) if sentences else 0
        
        # 3. Vocabulary complexity (simplified)
        complex_words = sum(1 for w in words if len(w) > 6)
        complex_word_ratio = complex_words / len(words) if words else 0
        
        # Calculate score
        score = (
            0.3 * min(avg_word_length / 10, 1.0) +
            0.3 * min(avg_sentence_length / 20, 1.0) +
            0.4 * complex_word_ratio
        )
        
        return min(max(score, 0.0), 1.0)
    
    def _requires_llm(self, text: str) -> bool:
        """Determine if text requires LLM processing."""
        # Simple heuristics
        if len(text) > 200:
            return True
        
        # Check for complex patterns
        complex_patterns = [
            r'\b(summarize|rewrite|generate|create|explain|analyze)\b',
            r'\b(table|code|prompt|terminal)\b',
            r'\b[0-9]+\s*[+\-*/]\s*[0-9]+',  # Math expressions
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _has_commands(self, text: str) -> bool:
        """Check if text contains voice commands."""
        command_patterns = [
            r'\b(new\s+line|tab|backspace)\b',
            r'\b(scrap|scratch|undo)\s+that\b',
            r'\bdelete\s+last\s+word\b',
            r'\bliteral\s+',
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def classify(self, text: str) -> str:
        """Classify text complexity."""
        analysis = self.analyze(text)
        
        if analysis["complexity_score"] < 0.3:
            return "simple"
        elif analysis["complexity_score"] < 0.7:
            return "moderate"
        else:
            return "complex"
    
    def get_route_recommendation(self, text: str) -> str:
        """Get recommended route based on complexity."""
        analysis = self.analyze(text)
        
        if analysis["has_commands"]:
            return "local"
        elif analysis["requires_llm"]:
            if analysis["complexity_score"] > 0.7:
                return "strong_llm"
            else:
                return "fast_llm"
        else:
            return "dictation"
