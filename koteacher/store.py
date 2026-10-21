"""앱 기록 (SQLite). 볼트 밖 앱 데이터 폴더에 둔다."""
import json
import sqlite3
import threading
import time

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts(
  id INTEGER PRIMARY KEY, problem_id TEXT, mode TEXT, started REAL, ended REAL,
  result TEXT, hints_opened INTEGER DEFAULT 0, solution_viewed INTEGER DEFAULT 0, code TEXT);
CREATE TABLE IF NOT EXISTS snapshots(
  id INTEGER PRIMARY KEY, attempt_id INTEGER, t REAL, code TEXT, summary TEXT, passed INTEGER);
CREATE TABLE IF NOT EXISTS coach_msgs(
  id INTEGER PRIMARY KEY, attempt_id INTEGER, t REAL, signal TEXT, tier TEXT, hint_level INTEGER,
  message TEXT, line INTEGER, ms INTEGER, rating TEXT);
CREATE TABLE IF NOT EXISTS doc_notes(
  id INTEGER PRIMARY KEY, doc TEXT, quote TEXT, prefix TEXT, question TEXT, answer TEXT, t REAL);
CREATE TABLE IF NOT EXISTS mistakes(
  id INTEGER PRIMARY KEY, attempt_id INTEGER, problem_id TEXT, t REAL, concepts TEXT, category TEXT,
  name TEXT, signal TEXT, evidence TEXT, line INTEGER, code_before TEXT, code_after TEXT, diff TEXT,
  detected_by TEXT, fixed INTEGER, time_to_fix REAL, hints_at_detection INTEGER, note TEXT);
"""


class Store:
    def __init__(self, path=None):
        config.ensure_dirs()
        self.db = sqlite3.connect(str(path or config.DB), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.db.executescript(SCHEMA)

    def _ex(self, sql, args=()):
        with self.lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur

    def rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    # 시도
    def start_attempt(self, pid, mode="practice"):
        return self._ex("INSERT INTO attempts(problem_id, mode, started) VALUES(?,?,?)", (pid, mode, time.time())).lastrowid

    def update_attempt(self, aid, **kw):
        if kw:
            cols = ", ".join(f"{k}=?" for k in kw)
            self._ex(f"UPDATE attempts SET {cols} WHERE id=?", (*kw.values(), aid))

    def snapshot(self, aid, code, summary, passed):
        return self._ex("INSERT INTO snapshots(attempt_id, t, code, summary, passed) VALUES(?,?,?,?,?)",
                        (aid, time.time(), code, json.dumps(summary, ensure_ascii=False), int(passed))).lastrowid

    def coach_msg(self, aid, **kw):
        kw.setdefault("t", time.time())
        cols = ", ".join(kw)
        return self._ex(f"INSERT INTO coach_msgs(attempt_id, {cols}) VALUES(?{', ?' * len(kw)})", (aid, *kw.values())).lastrowid

    def rate(self, mid, rating):
        self._ex("UPDATE coach_msgs SET rating=? WHERE id=?", (rating, mid))

    # 오답 기록
    def add_mistake(self, **kw):
        kw.setdefault("t", time.time())
        cols = ", ".join(kw)
        return self._ex(f"INSERT INTO mistakes({cols}) VALUES({', '.join('?' * len(kw))})", tuple(kw.values())).lastrowid

    def set_note(self, mid, note):
        self._ex("UPDATE mistakes SET note=? WHERE id=?", (note, mid))

    def mistakes(self, pid=None, limit=200):
        if pid:
            return self.rows("SELECT * FROM mistakes WHERE problem_id=? ORDER BY t DESC LIMIT ?", (pid, limit))
        return self.rows("SELECT * FROM mistakes ORDER BY t DESC LIMIT ?", (limit,))

    def weak_categories(self, n=3):
        return self.rows("SELECT category, COUNT(*) c FROM mistakes WHERE category IS NOT NULL "
                         "GROUP BY category ORDER BY c DESC LIMIT ?", (n,))

    def problem_status(self):
        """문제별 상태: solved(힌트 1개 이하로 통과), helped(힌트 2개 이상·풀이 봄), tried."""
        out = {}
        for r in self.rows("SELECT problem_id, result, hints_opened, solution_viewed FROM attempts"):
            cur = out.get(r["problem_id"], "tried")
            if r["result"] == "pass":
                s = "helped" if (r["hints_opened"] or 0) >= 2 or r["solution_viewed"] else "solved"
                cur = "solved" if "solved" in (cur, s) else s
            out[r["problem_id"]] = cur
        return out

    def last_code(self, pid):
        r = self.rows("SELECT s.code FROM snapshots s JOIN attempts a ON a.id=s.attempt_id "
                      "WHERE a.problem_id=? ORDER BY s.t DESC LIMIT 1", (pid,))
        return r[0]["code"] if r else None

    # 문서에서 골라 물은 기록
    def add_note(self, doc, quote, prefix, question, answer):
        return self._ex("INSERT INTO doc_notes(doc, quote, prefix, question, answer, t) VALUES(?,?,?,?,?,?)",
                        (doc, quote, prefix, question, answer, time.time())).lastrowid

    def notes(self, doc):
        return self.rows("SELECT * FROM doc_notes WHERE doc=? ORDER BY t", (doc,))

    def delete_note(self, nid):
        self._ex("DELETE FROM doc_notes WHERE id=?", (nid,))

    # 풀이 기록: 한 번이라도 실행한 시도만
    def history(self, pid=None):
        where = "WHERE a.problem_id=?" if pid else ""
        return self.rows(f"""
            SELECT a.id, a.problem_id, a.mode, a.started, a.ended, a.result, a.hints_opened, a.solution_viewed,
                   COUNT(s.id) AS runs, MAX(s.t) AS last_t, SUM(s.passed) AS passes,
                   (SELECT COUNT(*) FROM mistakes m WHERE m.attempt_id=a.id) AS mistakes,
                   (SELECT COUNT(*) FROM coach_msgs c WHERE c.attempt_id=a.id) AS coach
            FROM attempts a JOIN snapshots s ON s.attempt_id=a.id {where}
            GROUP BY a.id ORDER BY MAX(s.t) DESC LIMIT 500""", (pid,) if pid else ())

    def attempt_detail(self, aid):
        att = self.rows("SELECT * FROM attempts WHERE id=?", (aid,))
        snaps = self.rows("SELECT id, t, passed, summary, code FROM snapshots WHERE attempt_id=? ORDER BY t", (aid,))
        msgs = self.rows("SELECT t, signal, tier, message, line FROM coach_msgs WHERE attempt_id=? ORDER BY t", (aid,))
        mis = self.rows("SELECT * FROM mistakes WHERE attempt_id=? ORDER BY t", (aid,))
        return {"attempt": att[0] if att else None, "snapshots": snaps, "coach": msgs, "mistakes": mis}
