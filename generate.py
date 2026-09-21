#!/usr/bin/env python3
"""跑步数据可视化 — COROS → docs/index.html（七日半马专项）。"""
import sys, os, json, datetime
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
import coros_official as co

HERE = os.path.dirname(os.path.abspath(__file__))

def collect_runs(days=15):
    runs = []
    today = datetime.date.today()
    for i in range(days, -1, -1):
        d = (today - datetime.timedelta(days=i)).isoformat()
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
    return runs

def collect_sleep(days=15):
    rec = co.fetch_sleep(datetime.date.today().isoformat())
    r = rec[0] if isinstance(rec, (list, tuple)) and rec else rec
    return r if isinstance(r, list) else []

def main():
    runs  = collect_runs()
    sleep = collect_sleep()
    runs.sort(key=lambda x: x["date"])
    if not runs:
        print("NO RUN DATA"); sys.exit(1)

    labels = [r["date"] for r in runs]
    dist   = [r["dist_km"] for r in runs]
    pace_s = [r["pace"] for r in runs]           # "5:58"
    hr     = [r["hr"] for r in runs]
    durmin = [round(r["dur_s"]/60, 1) for r in runs]
    pace_min = []
    for p in pace_s:
        if p and ":" in p:
            a, b = p.split(":"); pace_min.append(round(float(a) + float(b)/60, 2))
        else:
            pace_min.append(None)

    slp_map = {s["date"]: {"total": s.get("total"), "quality": s.get("quality")} for s in sleep}
    slp_total = [ (slp_map.get(l) or {}).get("total") for l in labels ]

    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    out = os.path.join(HERE, "docs", "index.html")
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>思己 · 跑步数据</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
body{{font-family:-apple-system,'PingFang SC',system-ui,sans-serif;background:#f2f4f8;margin:0;color:#1f2430}}
.wrap{{max-width:1000px;margin:0 auto;padding:24px}}
h1{{font-size:20px;margin-bottom:2px}} .sub{{color:#8a93a6;margin-bottom:22px}}
h2{{font-size:15px;color:#3a4152;margin:18px 0 8px}}
.chart{{background:#fff;border-radius:14px;padding:14px;box-shadow:0 1px 6px rgba(20,30,70,.08)}}
</style></head><body><div class="wrap">
<h1>🏃 思己 · 跑步数据</h1>
<p class="sub">七日半马 · 每日距离 / 配速 / 心率 / 睡眠</p>
<div class="chart" id="c1" style="height:300px"></div>
<div class="chart" id="c2" style="height:300px"></div>
<div class="chart" id="c3" style="height:300px"></div>
<script>
const LABELS={json.dumps(labels,ensure_ascii=False)};
const DIST={json.dumps(dist)};
const PACE={json.dumps(pace_min)};
const HR={json.dumps(hr)};
const DUR={json.dumps(durmin)};
const SLPT={json.dumps(slp_total)};

function mk(el,opt){{echarts.init(document.getElementById(el)).setOption(opt)}}
const X={{type:'category',data:LABELS}};
const base=X;

mk('c1',{{tooltip:{{trigger:'axis'}},legend:{{}},grid:{{left:46,right:46,top:30,bottom:26}},
  xAxis:X,yAxis:[{{type:'value',name:'km'}},{{type:'value',name:'分钟'}}],
  series:[
    {{name:'距离(km)',type:'bar',data:DIST,itemStyle:{{color:'#3b82f6',borderRadius:[6,6,0,0]}},
      label:{{show:true,position:'top',fontSize:11}}}},
    {{name:'时长(min)',type:'line',yAxisIndex:1,data:DUR,smooth:true,color:'#e67e22'}}
  ]}});

mk('c2',{{tooltip:{{trigger:'axis'}},legend:{{data:['配速(min/km)','心率(bpm)']}},grid:{{left:46,right:46,top:40,bottom:40}},
  xAxis:base,
  yAxis:[{{type:'value',name:'min/km',inverse:true}},{{type:'value',name:'bpm'}}],
  series:[
    {{name:'配速',type:'line',data:PACE,smooth:true,color:'#e11d48'}},
    {{name:'心率',type:'line',yAxisIndex:1,data:HR,smooth:true,color:'#8e44ad'}}
  ]}});

mk('c3',{{tooltip:{{trigger:'axis'}},legend:{{}},grid:{{left:46,right:46,top:40,bottom:40}},
  xAxis:base,yAxis:{{type:'value',name:'分钟'}},
  series:[{{name:'睡眠(分钟)',type:'bar',data:SLPT,itemStyle:{{color:'#1abc9c'}}}}]}});
</script></div></body></html>"""
    open(out, "w").write(html)
    print("WROTE", out)
    print("runs:", len(runs), labels)

if __name__ == "__main__":
    main()