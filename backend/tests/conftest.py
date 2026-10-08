import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Testlar Claude API'ga murojaat qilmaydi va vaqtinchalik SQLite bazasida ishlaydi
os.environ["LLM_ENABLED"] = "false"
os.environ["DEV_MODE"] = "true"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:TEST"
os.environ["ADMIN_TOKEN"] = "secret"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).parent / 'test.db'}"

import pytest  # noqa: E402


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.db import Base, engine
    from app.main import app

    Base.metadata.drop_all(engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(engine)
