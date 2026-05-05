from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import asyncio
import json

from ghosttype.ramblerouter.router import Router, RouterOutput, Action, Route
from ghosttype.ramblerouter.prompts import PromptBuilder
from ghosttype.ramblerouter.complexity import ComplexityAnalyzer
from ghosttype.providers.llm.base import LLMProvider
from ghosttype.ghosttype_desktop.context.manager import ContextManager
from ghosttype.policy.engine import PolicyEngine
from ghosttype.core.errors import RouterError, PolicyDenied, TaskExecutionError


@dataclass
class TaskContext:
    text: str
    route: Route
    actions: List[Action] = field(default_factory=list)
    collected_context: Dict[str, str] = field(default_factory=dict)
    policy_result: Dict[str, Any] = field(default_factory=dict)
    mode: str = "fast"
    confidence: float = 1.0


@dataclass
class TaskResult:
    success: bool
    output: str = ""
    error: Optional[str] = None
    actions: List[Action] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StrongTaskExecutor:
    def __init__(
        self,
        router: Router,
        context_manager: ContextManager,
        policy_engine: PolicyEngine,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.router = router
        self.context_manager = context_manager
        self.policy_engine = policy_engine
        self.config = config or {}
        
        self.prompt_builder = PromptBuilder()
        self.complexity_analyzer = ComplexityAnalyzer()
        
        self._max_context_age = self.config.get("max_context_age", 30)
        self._enable_context = self.config.get("enable_context", True)
        self._strict_policy = self.config.get("strict_policy", True)
    
    async def execute(self, text: str) -> TaskResult:
        task_context = await self._prepare_context(text)
        
        if not task_context.policy_result.get("remote_allowed", True):
            return TaskResult(
                success=False,
                error="Remote operations denied by policy",
                metadata={"policy_result": task_context.policy_result},
            )
        
        try:
            if task_context.route == Route.STRONG_LLM:
                return await self._execute_strong_llm(task_context)
            elif task_context.route == Route.ESCALATION_LLM:
                return await self._execute_escalation_llm(task_context)
            elif task_context.route == Route.PRIVATE_LLM:
                return await self._execute_private_llm(task_context)
            elif task_context.route == Route.AGENT:
                return await self._execute_agent(task_context)
            else:
                return TaskResult(
                    success=False,
                    error=f"Unsupported route for strong executor: {task_context.route}",
                )
        except PolicyDenied as e:
            return TaskResult(
                success=False,
                error=f"Policy denied: {e}",
                metadata={"policy_result": task_context.policy_result},
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error=f"Task execution failed: {e}",
                metadata={"route": task_context.route.value},
            )
    
    async def _prepare_context(self, text: str) -> TaskContext:
        route_output = self.router.route(text)
        
        policy_result = self.policy_engine.check(text)
        
        collected_context = {}
        if self._enable_context and route_output.context_required:
            try:
                collected_context = self.context_manager.collect_all()
            except Exception:
                pass
        
        return TaskContext(
            text=text,
            route=route_output.route,
            actions=route_output.actions,
            collected_context=collected_context,
            policy_result=policy_result,
            mode=policy_result.get("mode", "fast"),
            confidence=route_output.confidence,
        )
    
    async def _execute_strong_llm(self, context: TaskContext) -> TaskResult:
        llm = self.router.strong_llm
        if not llm or not llm.is_available():
            return TaskResult(
                success=False,
                error="Strong LLM provider not available",
            )
        
        complexity = self.complexity_analyzer.analyze(context.text)
        
        mode = complexity.get("suggested_mode", "summarize")
        
        if context.collected_context:
            context_str = self._format_context(context.collected_context)
            prompt = self.prompt_builder.build_strong_llm_prompt(
                context.text,
                mode=mode,
                context=context_str,
            )
        else:
            prompt = self.prompt_builder.build_strong_llm_prompt(
                context.text,
                mode=mode,
            )
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.complete({"messages": [{"role": "user", "content": prompt}]})
        )
        
        output = response.get("content", "")
        
        actions = [
            Action(type="insert_text", text=output),
        ]
        
        return TaskResult(
            success=True,
            output=output,
            actions=actions,
            metadata={
                "route": context.route.value,
                "mode": mode,
                "complexity": complexity,
                "context_used": bool(context.collected_context),
            },
        )
    
    async def _execute_escalation_llm(self, context: TaskContext) -> TaskResult:
        llm = self.router.strong_llm
        if not llm or not llm.is_available():
            return TaskResult(
                success=False,
                error="Escalation LLM provider not available",
            )
        
        escalation_prompt = f"""The user has requested an escalation for the following task.
Analyze the request and provide a comprehensive response.

Task: {context.text}

Context:
{self._format_context(context.collected_context) if context.collected_context else "No context available"}

Provide a detailed, accurate response."""
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.complete({"messages": [{"role": "user", "content": escalation_prompt}]})
        )
        
        output = response.get("content", "")
        
        return TaskResult(
            success=True,
            output=output,
            actions=[Action(type="insert_text", text=output)],
            metadata={
                "route": context.route.value,
                "escalation": True,
            },
        )
    
    async def _execute_private_llm(self, context: TaskContext) -> TaskResult:
        local_llm = None
        from ghosttype.providers.llm.ollama import OllamaProvider
        try:
            local_llm = OllamaProvider({"host": "localhost"})
            if not local_llm.is_available():
                return TaskResult(
                    success=False,
                    error="Private LLM not available (Ollama not running)",
                )
        except Exception:
            return TaskResult(
                success=False,
                error="Private LLM not available",
            )
        
        prompt = self.prompt_builder.build_private_llm_prompt(context.text)
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: local_llm.complete({"messages": [{"role": "user", "content": prompt}]})
        )
        
        output = response.get("content", "")
        
        return TaskResult(
            success=True,
            output=output,
            actions=[Action(type="insert_text", text=output)],
            metadata={
                "route": context.route.value,
                "provider": "ollama",
                "privacy_mode": True,
            },
        )
    
    async def _execute_agent(self, context: TaskContext) -> TaskResult:
        llm = self.router.strong_llm or self.router.fast_llm
        if not llm or not llm.is_available():
            return TaskResult(
                success=False,
                error="No LLM provider available for agent mode",
            )
        
        tools = ["clipboard", "context", "execute"]
        prompt = self.prompt_builder.build_agent_prompt(
            context.text,
            tools=tools,
        )
        
        if context.collected_context:
            prompt = f"{prompt}\n\nContext:\n{self._format_context(context.collected_context)}"
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.complete({"messages": [{"role": "user", "content": prompt}]})
        )
        
        output = response.get("content", "")
        
        return TaskResult(
            success=True,
            output=output,
            actions=[Action(type="insert_text", text=output)],
            metadata={
                "route": context.route.value,
                "agent_mode": True,
            },
        )
    
    def _format_context(self, context: Dict[str, str]) -> str:
        parts = []
        for key, value in context.items():
            if value:
                parts.append(f"{key.upper()}:\n{value[:500]}")
        return "\n\n".join(parts)
    
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "strong_llm_available": self.router.strong_llm.is_available() if self.router.strong_llm else False,
            "context_enabled": self._enable_context,
            "strict_policy": self._strict_policy,
            "max_context_age": self._max_context_age,
        }
