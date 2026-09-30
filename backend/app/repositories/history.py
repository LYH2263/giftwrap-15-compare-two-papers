import json
from datetime import datetime, timezone
from app.db import connect

STATUS_ACTIVE = "active"
STATUS_VOIDED = "voided"


class RunNotFound(LookupError):
    pass


class RunAlreadyVoided(ValueError):
    pass


def insert_run(box_id, overlap, result, note=""):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(box_id,overlap,result_json,note,created_at,status) VALUES (?,?,?,?,?,?)",
            (box_id, overlap, json.dumps(result, ensure_ascii=False), note,
             datetime.now(timezone.utc).isoformat(), STATUS_ACTIVE),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def _row_to_run(row):
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    return d


def list_runs(limit=50, include_voided=False):
    c = connect()
    try:
        sql = (
            "SELECT r.*, b.name box_name FROM calc_runs r "
            "LEFT JOIN boxes b ON b.id=r.box_id "
        )
        params = ()
        if not include_voided:
            sql += "WHERE r.status = ? "
            params = (STATUS_ACTIVE,)
        sql += "ORDER BY r.id DESC LIMIT ?"
        rows = c.execute(sql, (*params, limit)).fetchall()
        return [_row_to_run(r) for r in rows]
    finally:
        c.close()


def get_run(run_id):
    c = connect()
    try:
        row = c.execute(
            "SELECT r.*, b.name box_name FROM calc_runs r "
            "LEFT JOIN boxes b ON b.id=r.box_id WHERE r.id=?",
            (run_id,),
        ).fetchone()
        return _row_to_run(row) if row else None
    finally:
        c.close()


def void_run(run_id, reason):
    """作废冲正：只附加作废元数据，result_json/overlap 等原测算数字一律不动。"""
    c = connect()
    try:
        row = c.execute("SELECT id, status FROM calc_runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise RunNotFound(run_id)
        if row["status"] == STATUS_VOIDED:
            raise RunAlreadyVoided(run_id)
        voided_at = datetime.now(timezone.utc).isoformat()
        cur = c.execute(
            "UPDATE calc_runs SET status=?, voided_at=?, void_reason=? "
            "WHERE id=? AND status=?",
            (STATUS_VOIDED, voided_at, reason, run_id, STATUS_ACTIVE),
        )
        if cur.rowcount == 0:
            # 并发兜底：读时活跃、更新时已被他处作废
            raise RunAlreadyVoided(run_id)
        c.commit()
        row = c.execute(
            "SELECT r.*, b.name box_name FROM calc_runs r "
            "LEFT JOIN boxes b ON b.id=r.box_id WHERE r.id=?",
            (run_id,),
        ).fetchone()
        return _row_to_run(row)
    finally:
        c.close()


def active_summary():
    """活跃合计：口径与默认列表一致，只统计 status='active' 的单。"""
    c = connect()
    try:
        rows = c.execute(
            "SELECT result_json FROM calc_runs WHERE status=?", (STATUS_ACTIVE,)
        ).fetchall()
        total_m2 = 0.0
        for row in rows:
            total_m2 += float(json.loads(row["result_json"]).get("paper_m2") or 0.0)
        return {"active_count": len(rows), "paper_m2_total": round(total_m2, 3)}
    finally:
        c.close()
