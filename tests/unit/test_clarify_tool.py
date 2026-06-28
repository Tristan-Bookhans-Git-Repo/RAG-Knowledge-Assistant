from app.services.clarify_tool import clarify_tool


def test_clarify_tool_returns_expected_shape() -> None:
    result = clarify_tool.invoke({"question_to_user": "Could you be more specific?"})
    assert result == {"type": "clarification", "question": "Could you be more specific?"}


def test_clarify_tool_return_direct_is_set() -> None:
    assert clarify_tool.return_direct is True
