"""Tests for processiq.prompts."""

import pytest
from jinja2 import TemplateNotFound

from processiq.prompts import (
    get_template_path,
    list_templates,
    render_prompt,
)


class TestRenderPrompt:
    def test_system_template(self):
        result = render_prompt("system")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_analyze_template(self):
        result = render_prompt("analyze", metrics_text="Process: 5 steps, 10h total")
        assert "5 steps" in result

    def test_extraction_template(self):
        result = render_prompt("extraction", content="Some process description")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_invalid_template_raises(self):
        with pytest.raises(TemplateNotFound):
            render_prompt("nonexistent_template")


class TestListTemplates:
    def test_returns_list(self):
        templates = list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_contains_core_templates(self):
        templates = list_templates()
        for name in ["system", "analyze", "extraction", "clarification"]:
            assert name in templates, f"Missing template: {name}"


class TestGetTemplatePath:
    def test_has_j2_extension(self):
        path = get_template_path("system")
        assert str(path).endswith(".j2")

    def test_path_exists(self):
        path = get_template_path("system")
        assert path.exists()
