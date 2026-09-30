import json
from datetime import datetime, timezone
from app.db import connect

ACTIVE = "active"
VOIDED = "voided"

def insert_run(box_id, overlap, result, note=""):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(box_id,overlap,result_json,note,created_at,status) VALUES (?,?,?,?,?,?)",
            (box_id, overlap, json.dumps(result, ensure_ascii=False), note,
             datetime.now(timezone.utc).isoformat(), ACTIVE),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()

def _row_to_dict(row):
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    return d

_LIST_SQL = """SELECT r.*, b.name box_name FROM calc_runs r
LEFT JOIN boxes b ON b.id=r.box_id {where} ORDER BY r.id DESC LIMIT ?"""

def list_runs(limit=50, include_voided=False):
    """用纸档列表。默认只列活跃单；include_voided=True 时含作废单（带作废态）。"""
    c = connect()
    try:
        if include_voided:
            rows = c.execute(_LIST_SQL.format(where=""), (limit,)).fetchall()
        else:
            rows = c.execute(_LIST_SQL.format(where="WHERE r.status=?"), (ACTIVE, limit)).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        c.close()

def get_run(run_id):
    c = connect()
    try:
        row = c.execute(
            """SELECT r.*, b.name box_name FROM calc_runs r
            LEFT JOIN boxes b ON b.id=r.box_id WHERE r.id=?""",
            (run_id,),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        c.close()

def active_totals():
    """活跃合计：只统计 status=active 的单，作废单一律不计。

    面积取落库 result_json 中的 paper_m2（即列表/详情展示的同一数字），
    Python 端求和后按 3 位小数四舍五入，保证列表过滤与合计口径一致、可测。
    返回 (条数, 面积合计)。
    """
    c = connect()
    try:
        rows = c.execute(
            "SELECT result_json FROM calc_runs WHERE status=?", (ACTIVE,)
        ).fetchall()
    finally:
        c.close()
    total = 0.0
    for r in rows:
        total += float(json.loads(r["result_json"]).get("paper_m2") or 0.0)
    return len(rows), round(total, 3)

class VoidError(Exception):
    def __init__(self, code, detail):
        self.code = code
        self.detail = detail

def void_run(run_id, reason):
    """作废冲正：只附加作废元数据，绝不改写 result_json/overlap 等原测算数字。

    - 单不存在 -> VoidError(404)
    - 已作废再次作废 -> VoidError(409)
    """
    reason = (reason or "").strip()
    if not reason:
        raise VoidError(422, "void reason required")
    c = connect()
    try:
        row = c.execute("SELECT status FROM calc_runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise VoidError(404, "run not found")
        if row["status"] == VOIDED:
            raise VoidError(409, "run already voided")
        cur = c.execute(
            "UPDATE calc_runs SET status=?, void_reason=?, voided_at=? WHERE id=? AND status=?",
            (VOIDED, reason, datetime.now(timezone.utc).isoformat(), run_id, ACTIVE),
        )
        if cur.rowcount == 0:
            # 并发下被其他请求抢先作废
            raise VoidError(409, "run already voided")
        c.commit()
    finally:
        c.close()
    return get_run(run_id)
