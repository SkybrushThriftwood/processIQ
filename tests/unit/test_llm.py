"""Tests for processiq.llm utility functions."""

from unittest.mock import MagicMock

from processiq.llm import extract_text_content, is_restricted_openai_model


class TestExtractTextContent:
    def test_plain_string(self):
        response = MagicMock()
        response.content = "Hello world"
        assert extract_text_content(response) == "Hello world"

    def test_list_of_text_blocks(self):
        response = MagicMock()
        response.content = [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
        ]
        # Remove additional_kwargs fallback
        response.additional_kwargs = {}
        result = extract_text_content(response)
        assert "Part 1" in result
        assert "Part 2" in result

    def test_list_of_strings(self):
        response = MagicMock()
        response.content = ["Hello", "World"]
        response.additional_kwargs = {}
        result = extract_text_content(response)
        assert "Hello" in result
        assert "World" in result

    def test_additional_kwargs_reasoning_content(self):
        response = MagicMock()
        response.content = ""
        response.additional_kwargs = {"reasoning_content": "Reasoning output"}
        assert extract_text_content(response) == "Reasoning output"

    def test_empty_response(self):
        response = MagicMock()
        response.content = ""
        response.additional_kwargs = {}
        # Falls back to str(response)
        result = extract_text_content(response)
        assert isinstance(result, str)


class TestIsRestrictedOpenaiModel:
    def test_gpt5(self):
        assert is_restricted_openai_model("gpt-5") is True
        assert is_restricted_openai_model("gpt-5-turbo") is True

    def test_o1(self):
        assert is_restricted_openai_model("o1") is True
        assert is_restricted_openai_model("o1-preview") is True

    def test_o3(self):
        assert is_restricted_openai_model("o3") is True
        assert is_restricted_openai_model("o3-mini") is True

    def test_gpt4o_not_restricted(self):
        assert is_restricted_openai_model("gpt-4o") is False

    def test_gpt4_not_restricted(self):
        assert is_restricted_openai_model("gpt-4") is False

    def test_claude_not_restricted(self):
        assert is_restricted_openai_model("claude-3-opus") is False
