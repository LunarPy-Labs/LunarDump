"""Unit tests for LunarDump Web UI Dashboard endpoints & application factory."""

import pytest
from fastapi.testclient import TestClient

from lunardump.ui.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_ui_system_info(client):
    response = client.get("/api/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "119.1 MB" in data["peak_ram"]


def test_ui_health_check_nonexistent(client):
    response = client.get("/api/health?config_path=nonexistent.yaml")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "warning"
    assert "does not exist" in data["message"]


def test_ui_generate_templates(client, tmp_path):
    cfg = tmp_path / "ui_config.yaml"
    mig = tmp_path / "ui_migration.yaml"
    env = tmp_path / "ui.env"

    payload = {
        "db_type": "postgres",
        "storage": "s3",
        "config_path": str(cfg),
        "migrate_path": str(mig),
        "env_path": str(env),
        "force": True,
    }

    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert cfg.exists()
    assert mig.exists()
    assert env.exists()


def test_ui_serve_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "LunarDump" in response.text


def test_ui_backup_run_dryrun(client, tmp_path):
    cfg = tmp_path / "run_config.yaml"
    mig = tmp_path / "run_migration.yaml"
    env = tmp_path / "run.env"

    client.post("/api/generate", json={
        "db_type": "postgres",
        "storage": "local",
        "config_path": str(cfg),
        "migrate_path": str(mig),
        "env_path": str(env),
        "force": True,
    })

    res = client.post("/api/backup/run", json={
        "config_path": str(cfg),
        "dry_run": True
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "Dry-run test passed" in res.json()["message"]


def test_ui_health_check_valid(client, tmp_path, monkeypatch):
    cfg = tmp_path / "valid_config.yaml"
    mig = tmp_path / "valid_migration.yaml"
    env = tmp_path / "valid.env"

    client.post("/api/generate", json={
        "db_type": "postgres",
        "storage": "local",
        "config_path": str(cfg),
        "migrate_path": str(mig),
        "env_path": str(env),
        "force": True,
    })

    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("LUNARDUMP_ENCRYPTION_KEY", "894fec11371555b89d8520af8d3da8af6c2fac5b4d5364e17900d46cffa15060")

    monkeypatch.setattr("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_tool", lambda self: True)
    monkeypatch.setattr("lunardump.core.dumpers.postgres.PostgreSQLDumper.check_connection", lambda self: True)

    res = client.get(f"/api/health?config_path={cfg}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert len(data["components"]) >= 3


def test_ui_storage_files_valid(client, tmp_path, monkeypatch):
    cfg = tmp_path / "storage_config.yaml"
    mig = tmp_path / "storage_migration.yaml"
    env = tmp_path / "storage.env"

    client.post("/api/generate", json={
        "db_type": "postgres",
        "storage": "local",
        "config_path": str(cfg),
        "migrate_path": str(mig),
        "env_path": str(env),
        "force": True,
    })

    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("LUNARDUMP_ENCRYPTION_KEY", "894fec11371555b89d8520af8d3da8af6c2fac5b4d5364e17900d46cffa15060")

    res = client.get(f"/api/storage/files?config_path={cfg}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_ui_backup_run_full(client, tmp_path, monkeypatch):
    cfg = tmp_path / "full_config.yaml"
    mig = tmp_path / "full_migration.yaml"
    env = tmp_path / "full.env"

    client.post("/api/generate", json={
        "db_type": "postgres",
        "storage": "local",
        "config_path": str(cfg),
        "migrate_path": str(mig),
        "env_path": str(env),
        "force": True,
    })

    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("LUNARDUMP_ENCRYPTION_KEY", "894fec11371555b89d8520af8d3da8af6c2fac5b4d5364e17900d46cffa15060")

    # Mock dumper to yield mock stream
    class MockDumper:
        def dump_stream(self):
            yield b"MOCK_DUMP_DATA"

    monkeypatch.setattr("lunardump.ui.routes.get_dumper", lambda db: MockDumper())

    res = client.post("/api/backup/run", json={
        "config_path": str(cfg),
        "dry_run": False
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_ui_migration_run_mock(client, monkeypatch):
    class MockMigrator:
        def __init__(self, src, tgt):
            pass
        def check_prerequisites(self):
            return True
        def execute_migration(self):
            return True

    monkeypatch.setattr("lunardump.ui.routes.DatabaseMigrator", MockMigrator)

    payload = {
        "source_type": "postgres",
        "source_host": "localhost",
        "source_port": 5432,
        "source_name": "db_a",
        "source_user": "user_a",
        "source_password": "pass_a",
        "target_type": "postgres",
        "target_host": "localhost",
        "target_port": 5432,
        "target_name": "db_b",
        "target_user": "user_b",
        "target_password": "pass_b",
    }

    res = client.post("/api/migration/run", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"


@pytest.mark.anyio
async def test_connection_manager():
    from lunardump.ui.app import ConnectionManager
    manager = ConnectionManager()

    class DummyWS:
        def __init__(self, fail=False):
            self.fail = fail
            self.accepted = False
            self.sent = []
        async def accept(self):
            self.accepted = True
        async def send_text(self, text):
            if self.fail:
                raise Exception("WS Fail")
            self.sent.append(text)

    ws1 = DummyWS()
    ws2 = DummyWS(fail=True)

    await manager.connect(ws1)
    await manager.connect(ws2)
    assert ws1 in manager.active_connections
    assert ws2 in manager.active_connections

    await manager.broadcast("Hello")
    assert "Hello" in ws1.sent
    assert ws2 not in manager.active_connections

    manager.disconnect(ws1)
    assert ws1 not in manager.active_connections


def test_start_ui_server(monkeypatch):
    from lunardump.ui.app import start_ui_server

    ran = {}
    def mock_run(app, host, port, log_level):
        ran["host"] = host
        ran["port"] = port

    monkeypatch.setattr("uvicorn.run", mock_run)
    monkeypatch.setattr("webbrowser.open", lambda url: True)

    start_ui_server("127.0.0.1", 9090, open_browser=True)
    assert ran["host"] == "127.0.0.1"
    assert ran["port"] == 9090


def test_ui_parse_cron(client):
    res = client.get("/api/cron/parse?expression=day-14.5")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["cron_expr"] == "5 14 * * *"
    assert "14:05" in data["description"]
    assert len(data["next_runs"]) == 5

    # Error case
    res_bad = client.get("/api/cron/parse?expression=invalid-expr")
    assert res_bad.status_code == 200
    assert res_bad.json()["status"] == "error"


