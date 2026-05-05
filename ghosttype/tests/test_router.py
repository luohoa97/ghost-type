import pytest
from ghosttype.ramblerouter.router import Router, RouterOutput, Action, Route


class MockLLMProvider:
    def __init__(self, available=True):
        self._available = available
    
    def is_available(self):
        return self._available
    
    def complete(self, request):
        return {"content": '{"route": "dictation", "actions": [{"type": "insert_text", "text": "test"}], "confidence": 0.9}'}


class TestRouter:
    def test_router_initialization(self):
        router = Router()
        assert router is not None
        assert router.config == {}
    
    def test_router_with_llm(self):
        mock_llm = MockLLMProvider()
        router = Router(fast_llm=mock_llm)
        assert router.fast_llm is mock_llm
    
    def test_deterministic_route_dictation(self):
        router = Router()
        result = router.route("Hello world")
        
        assert isinstance(result, RouterOutput)
        assert result.route == Route.DICTATION
        assert len(result.actions) > 0
        assert result.actions[0].type == "insert_text"
    
    def test_deterministic_route_local_command(self):
        router = Router()
        
        result = router.route("new line")
        assert result.route == Route.LOCAL
        assert len(result.actions) > 0
    
    def test_deterministic_route_scrap_that(self):
        router = Router()
        
        result = router.route("scrap that")
        assert result.route == Route.LOCAL
    
    def test_deterministic_route_tab(self):
        router = Router()
        
        result = router.route("tab")
        assert result.route == Route.LOCAL
    
    def test_deterministic_route_enter(self):
        router = Router()
        
        result = router.route("enter")
        assert result.route == Route.LOCAL
    
    def test_smart_router_disabled(self):
        router = Router(config={"features": {"smart_router": False}})
        result = router.route("Hello world")
        
        assert result.route == Route.DICTATION
    
    def test_llm_route_when_available(self):
        mock_llm = MockLLMProvider()
        router = Router(fast_llm=mock_llm)
        
        result = router.route("Hello world")
        
        assert isinstance(result, RouterOutput)
    
    def test_diagnostics(self):
        mock_llm = MockLLMProvider()
        router = Router(fast_llm=mock_llm)
        
        diag = router.diagnostics()
        
        assert "fast_llm_available" in diag
        assert diag["fast_llm_available"] is True
        assert "smart_router_enabled" in diag
        assert "local_commands_available" in diag


class TestAction:
    def test_action_to_dict(self):
        action = Action(type="insert_text", text="Hello")
        result = action.to_dict()
        
        assert result["type"] == "insert_text"
        assert result["text"] == "Hello"
    
    def test_action_from_dict(self):
        data = {"type": "insert_text", "text": "Hello", "key": "enter"}
        action = Action.from_dict(data)
        
        assert action.type == "insert_text"
        assert action.text == "Hello"
        assert action.key == "enter"
    
    def test_action_with_route(self):
        action = Action(type="route", route="strong_llm")
        result = action.to_dict()
        
        assert result["route"] == "strong_llm"


class TestRouterOutput:
    def test_output_to_dict(self):
        action = Action(type="insert_text", text="test")
        output = RouterOutput(
            route=Route.DICTATION,
            actions=[action],
            confidence=0.9,
            raw_text="test",
        )
        
        result = output.to_dict()
        
        assert result["route"] == "dictation"
        assert result["confidence"] == 0.9
        assert len(result["actions"]) == 1
    
    def test_output_from_dict(self):
        data = {
            "route": "dictation",
            "actions": [{"type": "insert_text", "text": "test"}],
            "confidence": 0.9,
            "raw_text": "test",
        }
        
        output = RouterOutput.from_dict(data)
        
        assert output.route == Route.DICTATION
        assert len(output.actions) == 1
        assert output.confidence == 0.9


class TestRoute:
    def test_route_values(self):
        assert Route.DICTATION.value == "dictation"
        assert Route.LOCAL.value == "local"
        assert Route.FAST_LLM.value == "fast_llm"
        assert Route.STRONG_LLM.value == "strong_llm"
        assert Route.ESCALATION_LLM.value == "escalation_llm"
        assert Route.PRIVATE_LLM.value == "private_llm"
        assert Route.AGENT.value == "agent"
