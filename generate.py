#!/usr/bin/env python3
"""跑步数据可视化站 — COROS → docs/index.html（从 9 月 1 日起累计，含地理散点）。"""
import sys, os, json, re, datetime, asyncio
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
import coros_official as co

HERE = os.path.dirname(os.path.abspath(__file__))


def collect_runs(start_date="2026-09-01"):
    runs = []
    today = datetime.date.today()
    start = datetime.date.fromisoformat(start_date)
    cur = today
    while cur >= start:
        d = cur.isoformat()
        rec = co.fetch_day(d)
        r = rec[0] if isinstance(rec, (list, tuple)) and rec else rec
        if isinstance(r, list):
            for it in r:
                runs.append({
                    "date": it.get("date", d),
                    "dur_s": it.get("dur_s"),
                    "dist_km": it.get("dist_km"),
                    "pace": it.get("pace"),
                    "hr": it.get("hr"),
                })
        cur -= datetime.timedelta(days=1)
    return runs


def collect_geo(start_date="2026-09-01"):
    today = datetime.date.today().isoformat()
    raw = asyncio.run(co.get_sport_records_raw(start_date, today))
    text = raw if isinstance(raw, str) else str(raw)
    text = text.replace('\\n', '\n').replace('\r', '')   # coros 返回字面 \n
    out = {}
    pat = re.compile(
        r'\d+\. Outdoor Run — (\d{4}-\d{2}-\d{2})\s*\n\s*Location:\s*(.*?)\n'
        r'\s*Start Coordinates:\s*([-\d.]+),\s*([-\d.]+)', re.S)
    for m in pat.finditer(text):
        date, loc, lat, lng = m.group(1), m.group(2).strip(), float(m.group(3)), float(m.group(4))
        out[date] = {"lat": lat, "lng": lng, "location": loc}
    return out


def collect_sleep():
    rec = co.fetch_sleep(datetime.date.today().isoformat())
    r = rec[0] if isinstance(rec, (list, tuple)) and rec else rec
    return r if isinstance(r, list) else []


# ---- HTML 模板：用 __DATA__ 占位（JSON 字面），其余是纯标准 HTML/JS，避免 f-string 转义 ----
TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>思己 · 跑步数据</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#0b1220;--card:#111a2e;--border:#24314d;--txt:#e2e8f0;--muted:#8fa0bd;--accent:#38bdf8}
  *{box-sizing:border-box}
  body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:0}
  .wrap{max-width:960px;margin:0 auto;padding:30px 16px 70px}
  h1{font-size:26px;margin:0 0 4px}
  .sub{color:var(--muted);font-size:14px;margin-bottom:24px}
  .updated{color:var(--muted);font-size:13px;text-align:right;margin-bottom:6px}
  .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px}
  @media(min-width:700px){.stats{grid-template-columns:repeat(3,1fr)}}
  .stat{background:var(--card);border:1px solid #1e2b44;border-radius:14px;padding:14px}
  .stat b{display:block;font-size:24px;color:#7dd3fc;font-weight:700}
  .stat span{font-size:12px;color:var(--muted)}
  .chart-card{background:var(--card);border:1px solid #1e2b44;border-radius:16px;padding:12px;margin-bottom:16px}
  .chart-card h2{font-size:15px;color:#cbd5e1;margin:6px 8px 10px;font-weight:600}
  .foot{color:var(--muted);font-size:12px;text-align:center;margin-top:24px}
  a{color:var(--accent)}
</style>
</head>
<body>
<div class="wrap">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <div>
      <h1>🏃 思己 · 跑步数据</h1>
      <div class="sub">七日半马挑战 · 从 9 月 1 日起累计 · 自动同步 COROS</div>
    </div>
  </div>
  <div class="updated" id="updated">加载中…</div>

  <div class="stats">
    <div class="stat"><b data-k="totalKm"></b><span>累计跑量 (km)</span></div>
    <div class="stat"><b data-k="runs"></b><span>跑步场次</span></div>
    <div class="stat"><b data-k="bestPace"></b><span>最佳配速 (min/km)</span></div>
    <div class="stat"><b data-k="avgHr"></b><span>平均心率 (bpm)</span></div>
    <div class="stat"><b data-k="avgKm"></b><span>场均距离 (km)</span></div>
    <div class="stat"><b data-k="streak"></b><span>最长连续半马 (天)</span></div>
  </div>

  <div class="chart-card"><h2>距离与时长</h2><div id="c1" style="height:300px"></div></div>
  <div class="chart-card"><h2>配速与心率</h2><div id="c2" style="height:300px"></div></div>
  <div class="chart-card"><h2>睡眠时长与质量</h2><div id="c3" style="height:280px"></div></div>
  <div class="chart-card"><h2>跑步地点分布</h2><div id="c4" style="height:340px"></div></div>

  <div class="foot">数据来源 COROS · 源码 <a href="https://github.com/wangsiji/running-dashboard">github.com/wangsiji/running-dashboard</a></div>
</div>

<script>
const DATA = __DATA__;

document.getElementById('updated').textContent = '更新于 ' + new Date().toLocaleString('zh-CN',{hour12:false}).slice(0,16);
const set = (k,v)=>document.querySelector('[data-k="'+k+'"]').textContent = v;
set('totalKm', DATA.total.toFixed(1));
set('runs',    DATA.runs);
set('bestPace', DATA.bestPace.toFixed(2));
set('avgHr',   DATA.avgHr);
set('avgKm',   DATA.avgKm.toFixed(1));
set('streak',  DATA.streak);

const labels = DATA.labels;
function mk(id,opt){
  const c = echarts.init(document.getElementById(id));
  c.setOption(opt);
  new ResizeObserver(()=>c.resize()).observe(document.getElementById(id));
}
const dark = {darkMode:true};
const lineAxis = o=>({axisLine:{lineStyle:{color:'#3b4a63'}},axisLabel:{color:'#94a3b8'},splitLine:{lineStyle:{color:'#1e2b44'}},...o});

// 1. 距离(bar) + 时长(line, 右轴)
mk('c1',Object.assign({},dark,{
  tooltip:{trigger:'axis'},legend:{textStyle:{color:'#cbd5e1'}},
  grid:{left:48,right:56,top:40,bottom:30},
  xAxis:{type:'category',data:labels,axisLabel:{color:'#94a3b8'}},
  yAxis:[{type:'value',name:'km',nameTextStyle:{color:'#94a3b8'}},{type:'value',name:'min',inverse:false}],
  series:[
    {name:'距离(km)',type:'bar',data:DATA.dist,barWidth:'50%',itemStyle:{borderRadius:[6,6,0,0]}},
    {name:'时长(min)',type:'line',yAxisIndex:1,data:DATA.dur,smooth:true,lineStyle:{width:2},symbolSize:6}
  ]
}));

// 2. 配速(inverse y) + 心率(右轴)
mk('c2',Object.assign({},dark,{
  tooltip:{trigger:'axis'},legend:{textStyle:{color:'#cbd5e1'}},
  grid:{left:48,right:56,top:40,bottom:30},
  xAxis:{type:'category',data:labels,axisLabel:{color:'#94a3b8'}},
  yAxis:[{type:'value',name:'配速 min/km',inverse:true},{type:'value',name:'bpm'}],
  series:[
    {name:'配速',type:'line',data:DATA.pace,smooth:true,lineStyle:{width:2},color:'#fb7185'},
    {name:'心率',type:'line',yAxisIndex:1,data:DATA.hr,smooth:true,lineStyle:{width:2},color:'#a78bfa'}
  ]
}));

// 3. 睡眠(min) + 质量分(右轴)
mk('c3',Object.assign({},dark,{
  tooltip:{trigger:'axis'},legend:{textStyle:{color:'#cbd5e1'}},
  grid:{left:48,right:56,top:40,bottom:30},
  xAxis:{type:'category',data:labels,axisLabel:{color:'#94a3b8'}},
  yAxis:[{type:'value',name:'min'},{type:'value',name:'质量分',min:0,max:100}],
  series:[
    {type:'bar',name:'睡眠',data:DATA.sleepTotal,itemStyle:{borderRadius:[4,4,0,0]},color:'#2dd4bf'},
    {type:'line',name:'质量',yAxisIndex:1,data:DATA.sleepQuality,smooth:true,color:'#fbbf24'}
  ]
}));

// 4. 地理散点（符号大小/颜色按距离分段）
mk('c4',Object.assign({},dark,{
  tooltip:{formatter:p=>{const d=p.data;return '<b>'+d.name+'</b><br/>'+d.d+' km'}},
  grid:{left:50,right:30,top:30,bottom:36},
  xAxis:lineAxis({type:'value',name:'经度'}),yAxis:lineAxis({type:'value',name:'纬度'}),
  series:[{
    type:'scatter',
    data:DATA.geos,
    symbolSize:p=>6+p.data.d*0.6,
    itemStyle:{color:'#38bdf8'},
    label:{show:true,fontSize:12,position:'right',formatter:p=>p.data.name,color:'#cbd5e1'}
  }]
}));
</script>
</body>
</html>"""


def main():
    runs  = collect_runs()
    geo   = collect_geo()
    sleep = collect_sleep()
    runs.sort(key=lambda x: x["date"])
    if not runs:
        print("NO RUN DATA"); sys.exit(1)

    for r in runs:
        g = geo.get(r["date"], {})
        r["lat"] = g.get("lat"); r["lng"] = g.get("lng"); r["location"] = g.get("location")

    labels = [r["date"] for r in runs]
    dist   = [r["dist_km"] for r in runs]
    hr     = [r["hr"] for r in runs]
    durmin = [round(r["dur_s"]/60, 1) for r in runs]
    pace   = []
    for p in [r["pace"] for r in runs]:
        if p and ":" in p:
            a, b = p.split(":"); pace.append(round(float(a)+float(b)/60, 2))
        else:
            pace.append(None)
    # 配速 None 补为 null
    pace = [None if x is None else x for x in pace]

    slp_map = {s["date"]: s for s in sleep}
    slp_total = [(slp_map.get(l) or {}).get("total") for l in labels]
    slp_qual  = [(slp_map.get(l) or {}).get("quality") for l in labels]

    total_km = sum(x for x in dist if x)
    n_runs   = len([x for x in dist if x])
    good_pace= [p for p in pace if p]
    best_p   = min(good_pace) if good_pace else 0
    hrs      = [h for h in hr if h]
    avg_hr   = round(sum(hrs)/len(hrs)) if hrs else 0
    avg_km   = round(total_km/n_runs, 1) if n_runs else 0
    seq = tot = 0
    for r in runs:
        if r["dist_km"] and r["dist_km"] >= 21.0:
            seq += 1; tot = max(tot, seq)
        else:
            seq = 0
    geos = [{"value": [r["lng"], r["lat"]], "name": r["location"] or r["date"], "d": r["dist_km"]}
            for r in runs if r.get("lat")]

    data = {
        "labels": labels,
        "dist": dist, "pace": pace, "hr": hr, "dur": durmin,
        "sleepTotal": slp_total, "sleepQuality": slp_qual,
        "geos": geos,
        "total": total_km, "runs": n_runs, "bestPace": best_p, "avgHr": avg_hr,
        "avgKm": avg_km, "streak": tot,
    }
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    out = os.path.join(HERE, "docs", "index.html")
    open(out, "w").write(html)
    print("WROTE", out, "| runs:", len(runs))


if __name__ == "__main__":
    main()