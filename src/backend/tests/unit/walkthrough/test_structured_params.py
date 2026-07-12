from app.agent.llm.structured import CALL_PARAMS


def test_call_params_have_no_completion_caps():
    assert CALL_PARAMS
    for call_type, params in CALL_PARAMS.items():
        assert "max_tokens" not in params, (
            f"{call_type} must not set max_tokens — reasoning models starve on caps"
        )
