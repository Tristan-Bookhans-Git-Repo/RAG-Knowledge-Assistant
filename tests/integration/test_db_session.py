import pytest
from sqlalchemy import text

from app.db.session import get_db


async def test_get_db_yields_working_session() -> None:
    gen = get_db()
    session = await anext(gen)
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1
    await gen.aclose()


async def test_get_db_rolls_back_and_reraises_on_exception() -> None:
    gen = get_db()
    await anext(gen)

    class _Exception(Exception):
        pass

    with pytest.raises(_Exception):
        await gen.athrow(_Exception())
