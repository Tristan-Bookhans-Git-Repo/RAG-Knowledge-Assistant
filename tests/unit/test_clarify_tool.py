from app.services.clarify_tool import clarify_tool


def test_clarify_tool_returns_question_text() -> None:
    result = clarify_tool.invoke({"question_to_user": "Could you be more specific?"})
    assert result == "Could you be more specific?"


def test_clarify_tool_return_direct_is_set() -> None:
    assert clarify_tool.return_direct is True
