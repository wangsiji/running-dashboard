"""数据处理层（Transform）：读最近的 raw 快照 → 清洗、规整、聚合 → data/processed/run_data.json。

职责：把 COROS 原始字段规整成图表稳定的统一 schema，剔除脏数据，产出累计统计。
后续 render 层 & 前端 app.js 只认 processed 的 schema，不关心 COROS 长什么样。

产出 schema（run_data.json）：
{
  "updated_at": "2026-09-21",
  "stats": {total_km, total_runs, avg_pace, avg_hr, best_pace},
  "days": [{date, dist_km, pace, hr, sleep_min, sleep_quality, lat, lng, location}, ...],  # 有活动或有记录
  "geo": [{date, lat, lng, location}, ...],          # 仅有点的活动（散点图）
  "weight": {date, kg} | null
}
"""
import os, json, glob, re, datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(HERE, 'data', 'raw')
OUT_DIR = os.path.join(HERE, 'data', 'processed')


def _latest_raw():
    """最近的 raw 快照；无则报错。支持旧名 corpus_ / 新名 coros_。"""
    files = glob.glob(os.path.join(RAW_DIR, 'coros_*.json')) + \
            glob.glob(os.path.join(RAW_DIR, 'corpus_*.json'))
    if not files:
        raise FileNotFoundError("data/raw/ 下没有快照，先跑 pipelines/extract.py")
    return max(files, key=lambda p: os.path.basename(p))


def _parse_pace(pace):
    """COROS pace 形如 '5:58' 或 '05:58' → 分钟/千米 (float)。缺失/异常→None。"""
    if not pace:
        return None
    if isinstance(pace, (int, float)):
        return float(pace)
    s = str(pace).strip()
    m = re.match(r'(\d+):(\d{2})', s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60
    return None


def transform():
    """读最新 raw 快照 → processed/run_data.json。返回输出路径。"""
    raw_path = _latest_raw()
    with open(raw_path, encoding='utf-8') as f:
        raw = json.load(f)

    sleep_by_date = {}
    for s in raw.get('sleep', []):
        d = s.get('date')
        if d:
            sleep_by_date[d] = {
                'bed_min': s.get('sumBedMinutes') or s.get('bed_min') or 0,
                'quality': s.get('sleepQuality') or s.get('quality'),
            }

    days = []   # 按日规整（只有跑步那天）
    for r in sorted(raw.get('runs', []), key=lambda x: x.get('date', '')):
        date = r.get('date') or r.get('startTime', '')[:10]
        if not date:
            continue
        dist = r.get('dist_km') or r.get('distance') or 0
        rec = {
            'date': date,
            'dist_km': round(float(dist), 2) if dist else 0,
            'pace': _parse_pace(r.get('pace')),
            'hr': r.get('hr'),
        }
        # 合并同日睡眠（如需分开则让 render 读 raw 的 sleep 数组）
        if date in sleep_by_date:
            rec['bed_min'] = sleep_by_date[date]['bed_min']
            rec['sleep_quality'] = sleep_by_date[date]['quality']
        # 坐标合并
        g = raw.get('geo', {}).get(date)
        if g:
            rec['lat'], rec['lng'], rec['location'] = g['lat'], g['lng'], g['location']
        days.append(rec)

    # ---- 聚合统计（跳过无距离的占位当天）----
    active = [d for d in days if d['dist_km'] > 0]
    total_km = round(sum(d['dist_km'] for d in active), 2)
    total_runs = len(active)
    pace_list = [d['pace'] for d in active if d['pace']]
    hr_list = [d['hr'] for d in active if d['hr']]
    stats = {
        'total_km': total_km,
        'total_runs': total_runs,
        'avg_pace': round(sum(pace_list) / len(pace_list), 2) if pace_list else None,
        'avg_hr': round(sum(hr_list) / len(hr_list)) if hr_list else None,
        'best_pace': min(pace_list) if pace_list else None,
    }

    geo = [{'date': d['date'], 'lat': d['lat'], 'lng': d['lng'], 'location': d['location']}
           for d in days if d.get('lat') is not None]

    out = {
        'updated_at': datetime.date.today().isoformat(),
        'stats': stats,
        'days': days,
        'geo': geo,
        'weight': raw.get('weight'),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'run_data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out_path


if __name__ == '__main__':
    print('PROCESSED ->', transform())