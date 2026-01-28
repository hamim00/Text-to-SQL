import pytest
from t2s.sql.safety import validate_and_rewrite_select, SQLSafetyError

def test_allows_select_adds_limit():
    out = validate_and_rewrite_select("SELECT * FROM STUDENT", dialect="sqlite", default_limit=50)
    assert "LIMIT 50" in out.sql.upper()
    assert out.limit_added is True

def test_blocks_multi_statement():
    with pytest.raises(SQLSafetyError):
        validate_and_rewrite_select("SELECT 1; DROP TABLE STUDENT", dialect="sqlite")

def test_blocks_non_select():
    with pytest.raises(SQLSafetyError):
        validate_and_rewrite_select("DELETE FROM STUDENT", dialect="sqlite")

def test_keeps_existing_limit():
    out = validate_and_rewrite_select("SELECT * FROM STUDENT LIMIT 10", dialect="sqlite", default_limit=50)
    assert "LIMIT 10" in out.sql.upper()
    assert out.limit_added is False
