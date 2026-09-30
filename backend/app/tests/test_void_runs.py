import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import app.db as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test_void.db")
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


def _save_run(client, box_id=1):
    r = client.post("/api/estimate", json={"box_id": box_id, "save": True})
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] is not None
    return body


def test_void_requires_reason(client):
    run = _save_run(client)
    r = client.post(f"/api/runs/{run['run_id']}/void", json={"reason": "   "})
    assert r.status_code == 422
    r = client.post(f"/api/runs/{run['run_id']}/void", json={})
    assert r.status_code == 422


def test_void_success_sets_status_and_time_keeps_numbers(client):
    run = _save_run(client)
    rid = run["run_id"]
    r = client.post(f"/api/runs/{rid}/void", json={"reason": "盒型选错，冲正"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "voided"
    assert body["void_reason"] == "盒型选错，冲正"
    assert body["voided_at"]
    # 原测算数字不得被改写
    assert body["result"]["paper_m2"] == run["paper_m2"]
    assert body["overlap"] == run["overlap"]

    detail = client.get(f"/api/runs/{rid}").json()
    assert detail["status"] == "voided"
    assert detail["result"]["paper_m2"] == run["paper_m2"]


def test_double_void_conflicts(client):
    rid = _save_run(client)["run_id"]
    assert client.post(f"/api/runs/{rid}/void", json={"reason": "第一次"}).status_code == 200
    r = client.post(f"/api/runs/{rid}/void", json={"reason": "第二次"})
    assert r.status_code == 409


def test_list_filter_and_summary_exclude_voided(client):
    a = _save_run(client)
    b = _save_run(client, box_id=2)
    client.post(f"/api/runs/{b['run_id']}/void", json={"reason": "重复下单"})

    # 默认列表不含作废单
    items = client.get("/api/runs").json()["items"]
    ids = [i["id"] for i in items]
    assert a["run_id"] in ids
    assert b["run_id"] not in ids

    # 含作废过滤：两路都给
    all_items = client.get("/api/runs?include_voided=true").json()["items"]
    all_ids = [i["id"] for i in all_items]
    assert {a["run_id"], b["run_id"]} <= set(all_ids)
    by_id = {i["id"]: i for i in all_items}
    assert by_id[b["run_id"]]["status"] == "voided"

    # 合计口径与默认列表一致：只计活跃
    summary = client.get("/api/runs").json()["summary"]
    assert summary["active_count"] == 1
    assert summary["paper_m2_total"] == pytest.approx(a["paper_m2"])
    # 含作废视图下合计也不得变
    summary_inc = client.get("/api/runs?include_voided=true").json()["summary"]
    assert summary_inc == summary


def test_void_missing_run_404(client):
    assert client.post("/api/runs/9999/void", json={"reason": "x"}).status_code == 404
    assert client.get("/api/runs/9999").status_code == 404
