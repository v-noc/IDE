from __future__ import annotations

import pytest

from app.agent.llm.providers import (
    models_catalog,
    parse_llm_spec,
    resolve_llm,
    validate_llm_settings,
)
from app.config.settings import Settings


def _settings(**kwargs) -> Settings:
    base = {
        "APP_ENV": "test",
        "TERMINUS_HOST": "http://localhost",
        "TERMINUS_USER": "u",
        "TERMINUS_KEY": "k",
        "TERMINUS_TEAM": "t",
        "TERMINUS_DB": "d",
        "WALKTHROUGH_LLM": "fake",
        "OPENAI_API_KEY": None,
        "AI_GATEWAY_API_KEY": None,
        "CUSTOM_LLM_BASE_URL": None,
        "CUSTOM_LLM_API_KEY": None,
    }
    base.update(kwargs)
    return Settings(**base)


def test_parse_llm_spec_variants():
    assert parse_llm_spec("fake") == ("fake", None)
    assert parse_llm_spec("vercel:zai/glm-4.7") == ("vercel", "zai/glm-4.7")
    assert parse_llm_spec("custom:llama3:8b") == ("custom", "llama3:8b")


def test_resolve_llm_order():
    settings = _settings(WALKTHROUGH_LLM="openai:gpt-4o-mini")
    assert resolve_llm(settings=settings).model == "gpt-4o-mini"
    assert resolve_llm(override="gpt-4o", settings=settings).model == "gpt-4o"

    defaulted = _settings(WALKTHROUGH_LLM="openai")
    assert resolve_llm(settings=defaulted).model_id == "openai:gpt-4o-mini"


def test_resolve_llm_unknown_provider():
    with pytest.raises(ValueError, match="nope"):
        resolve_llm(settings=_settings(WALKTHROUGH_LLM="nope"))


def test_validate_llm_settings_fake_ok():
    assert validate_llm_settings(_settings()).spec.name == "fake"


def test_validate_llm_settings_vercel_needs_key():
    with pytest.raises(ValueError, match="AI_GATEWAY_API_KEY"):
        validate_llm_settings(_settings(WALKTHROUGH_LLM="vercel"))


def test_models_catalog_hides_fake_when_real_active():
    settings = _settings(
        WALKTHROUGH_LLM="openai:gpt-4o-mini",
        OPENAI_API_KEY="sk-test",
    )
    catalog = models_catalog(settings)
    assert catalog["active"] == "openai:gpt-4o-mini"
    names = [p["name"] for p in catalog["providers"]]
    assert "fake" not in names
    assert "openai" in names
    blob = str(catalog)
    assert "sk-test" not in blob
