from langchain_core.tools import tool


@tool(return_direct=True)
def clarify_tool(question_to_user: str) -> dict[str, str]:
    """Ask the user for clarification when the question is ambiguous or incomplete."""
    return {"type": "clarification", "question": question_to_user}
