"""数据采集层（Extract）：从 COROS 拉取原始数据，原样落盘到 data/raw/。

职责：只负责"拿到数据并保存"，不做任何清洗/计算。
   - 每次运行生成一个带日期的 raw 快照（可回滚、可重放）。
   - 后续 transform 层从最近的 raw 快照读，不直接碰 API。
"""
import sys, os, json, re, datetime, asyncio

sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
import coros_official as co

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(HERE, 'data', 'raw')


def _fetch_day(target_date):
    """单日跑步记录（结构化 dict 列表）。COROS 无当天=返回空列表。"""
    rec = co.fetch_day(target_date)
    r = rec[0] if isinstance(rec, (list, tuple)) and rec else rec
    return r if isinstance(r, list) else []


def _fetch_geo(start_date, end_date):
    """解析 get_sport_records_raw 文本，拿每天跑步的坐标+地点（仅在有坐标时）。"""
    raw = asyncio.run(co.get_sport_records_raw(start_date, end_date))
    text = raw if isinstance(raw, str) else str(raw)
    text = text.replace('\\n', '\n').replace('\r', '')  # coros 返回字面 \n
    out = {}
    pat = re.compile(
        r'\d+\. Outdoor Run — (\d{4}-\d{2}-\d{2})\s*\n\s*Location:\s*(.*?)\n'
        r'\s*Start Coordinates:\s*([-\d.]+),\s*([-\d.]+)', re.S)
    for m in pat.finditer(text):
        date, loc, lat, lng = m.group(1), m.group(2).strip(), float(m.group(3)), float(m.group(4))
        out[date] = {"lat": lat, "lng": lng, "location": loc}
    return out


def extract(force=False):
    """拉取跑步+坐标+睡眠+体重，写入 data/raw/coros_<today>.json。

    Returns: 写入的快照绝对路径。
    """
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=120)   # 留 120 天窗口

    os.makedirs(RAW_DIR, exist_ok=True)
    snapshot = {
        "generated_at": today.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": today.isoformat(),
        "runs": [],          # 逐日收集的跑步（结构化）
        "geo": {},           # {date: {lat, lng, location}}
        "sleep": [],         # 睡眠日列表
        "weight": None,      # 最近一次体重
    }

    # 1) 跑步：逐日拉取（COROS 一次 fetch_day 只回当天，无则空）
    cur = today
    d0 = datetime.date.fromisoformat(start_date.isoformat())
    while cur >= d0:
        for it in _fetch_day(cur.isoformat()):
            # 结构化保留，字段名不动，交给 transform
            snapshot["runs"].append(it)
        cur -= datetime.timedelta(days=1)

    # 2) 坐标 / 地点
    snapshot["geo"] = _fetch_geo(start_date.isoformat(), today.isoformat())

    # 3) 睡眠
    slp = co.fetch_sleep(today.isoformat())
    r = slp[0] if isinstance(slp, (list, tuple)) and slp else slp
    snapshot["sleep"] = r if isinstance(r, list) else []

    # 4) 体重
    snapshot["weight"] = co.fetch_weight()

    # 排序：日期升序
    snapshot["runs"].sort(key=lambda x: x.get("date", ""))
    snapshot["sleep"].sort(key=lambda x: x.get("date", ""))

    fname = os.path.join(RAW_DIR, f"coros_{today.isoformat()}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    return fname


if __name__ == "__main__":
    print("RAW ->", extract())