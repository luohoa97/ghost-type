from typing import Dict, Any, List
import re


class ComplexityAnalyzer:
    """Analyzes text complexity for routing decisions."""
    
    def __init__(self):
        self._complexity_threshold = 0.5
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text complexity."""
        words = text.split()
        word_count = len(words)
        
        # Calculate complexity score
        score = self._calculate_complexity(text)
        
        return {
            "word_count": word_count,
            "complexity_score": score,
            "is_complex": score > self._complexity_threshold,
            "recommendation": "strong_llm" if score > self._complexity_threshold else "fast_llm",
        }
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate complexity score."""
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return 0.0
        
        # Factor 1: Word count (0-0.3)
        word_score = min(word_count / 20, 1.0) * 0.3
        
        # Factor 2: Sentence complexity (0-0.3)
        sentences = re.split(r"[.!?]+", text)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s) / max(len(sentences), 1)
        sentence_score = min(avg_sentence_length / 15, 1.0) * 0.3
        
        # Factor 3: Command presence (0-0.4)
        commands = self._count_commands(text)
        command_score = min(commands / 5, 1.0) * 0.4
        
        return word_score + sentence_score + command_score
    
    def _count_commands(self, text: str) -> int:
        """Count command-like patterns."""
        patterns = [
            r"\bnew\s+line\b",
            r"\btab\b",
            r"\bbackspace\b",
            r"\b(scrap|scratch|undo)\s+that\b",
            r"\bdelete\s+last\s+word\b",
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return count
