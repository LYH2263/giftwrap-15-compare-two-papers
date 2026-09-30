import pytest
from app import seed
from app.db import connect
from app.repositories import history as repo


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setattr("app.db.DB_PATH", path)
    seed.init_db()
    return path


def _insert(db, paper_m2):
    """直接插一单，result_json 带指定 paper_m2，返回 run_id。"""
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(box_id,overlap,result_json,note,created_at,status)"
            " VALUES (1,1.15,?,'','t','active')",
            ('{"paper_m2": %s}' % paper_m2,),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def test_void_sets_status_reason_and_time(db):
    rid = _insert(db, 0.31)
    out = repo.void_run(rid, "客户取消订单")
    assert out["status"] == "voided"
    assert out["void_reason"] == "客户取消订单"
    assert out["voided_at"]
    # 原测算数字不得被改写
    assert out["result"]["paper_m2"] == 0.31
    assert out["overlap"] == 1.15


def test_double_void_fails(db):
    rid = _insert(db, 0.31)
    repo.void_run(rid, "第一次作废")
    with pytest.raises(repo.VoidError) as ei:
        repo.void_run(rid, "再次作废")
    assert ei.value.code == 409
    # 首次原因与原数字保持不变
    again = repo.get_run(rid)
    assert again["void_reason"] == "第一次作废"
    assert again["result"]["paper_m2"] == 0.31


def test_void_unknown_run_404(db):
    with pytest.raises(repo.VoidError) as ei:
        repo.void_run(999, "不存在")
    assert ei.value.code == 404


def test_void_requires_reason(db):
    rid = _insert(db, 0.31)
    with pytest.raises(repo.VoidError) as ei:
        repo.void_run(rid, "   ")
    assert ei.value.code == 422
    assert repo.get_run(rid)["status"] == "active"


def test_list_default_excludes_voided_with_toggle(db):
    a = _insert(db, 0.31)
    b = _insert(db, 0.42)
    repo.void_run(b, "重复测算")
    default_ids = [r["id"] for r in repo.list_runs()]
    assert a in default_ids and b not in default_ids
    all_ids = [r["id"] for r in repo.list_runs(include_voided=True)]
    assert set(all_ids) == {a, b}
    voided_row = next(r for r in all_ids if r["id"] == b)
    assert voided_row["status"] == "voided"


def test_active_totals_exclude_voided(db):
    _insert(db, 0.31)
    _insert(db, 0.42)
    rid3 = _insert(db, 0.27)
    count, area = repo.active_totals()
    assert count == 3
    assert area == pytest.approx(1.0)
    repo.void_run(rid3, "作废一单")
    count, area = repo.active_totals()
    assert count == 2
    assert area == pytest.approx(0.73)
    # 与默认列表（不含作废）口径一致
    listed = repo.list_runs(include_voided=False)
    assert count == len(listed)
    assert area == pytest.approx(round(sum(r["result"]["paper_m2"] for r in listed), 3))
