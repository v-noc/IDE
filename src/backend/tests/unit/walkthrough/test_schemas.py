from __future__ import annotations

from app.walkthrough.schemas import PROMPT_VERSION, RunRequest


def test_run_request_defaults():
    request = RunRequest(project_id="p", node_id="n", depth=1)
    assert request.verbosity == "normal"
    assert request.user_query == ""


def test_run_request_accepts_knobs():
    request = RunRequest(
        project_id="p",
        node_id="n",
        depth=1,
        verbosity="detailed",
        user_query="how retries work",
    )
    assert request.verbosity == "detailed"
    assert request.user_query == "how retries work"


def test_prompt_version_bumped():
    assert PROMPT_VERSION == "5"
