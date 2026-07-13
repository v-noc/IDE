from app.agent.schemas.parts import ToolEstimate
from app.agent.tools.base import needs_confirmation
from app.agent.harness.confirm import EstimateConfirmMiddleware


def test_estimate_confirm_middleware_limit_default():
    mw = EstimateConfirmMiddleware(auto_run_limit=15)
    assert mw.auto_run_limit == 15


def test_over_cap_skips_confirm():
    estimate = ToolEstimate(
        items=50,
        llm_calls=100,
        label="50 stops",
        over_cap=True,
    )
    # over_cap → refuse path, needs_confirmation returns False
    from app.agent.tools.walkthrough_tool import WALKTHROUGH_SPEC

    assert needs_confirmation(WALKTHROUGH_SPEC, estimate, 15) is False
