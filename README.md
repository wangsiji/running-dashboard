# running-dashboard

思己跑步数据可视化站（COROS → GitHub Pages）。部署在 https://wangsiji.github.io/running-dashboard/

## 架构：三层严格分离

```
数据采集(extract) → 数据处理(transform) → 表现渲染(render)
      ↓                    ↓                     ↓
  data/raw/           data/processed/         docs/
  (COROS原始快照)      (标准化schema+统计)     (静态站+assets)
```

| 层 | 位置 | 职责 | 产出 |
|----|------|------|------|
| **数据** | `pipelines/extract.py` | 调 COROS API，原样落盘，不做任何计算 | `data/raw/coros_YYYY-MM-DD.json` |
| **处理** | `pipelines/transform.py` | 清洗、规整字段名、算累计/均值 | `data/processed/run_data.json`（统一 schema） |
| **表现** | `render/site.py` + `render/template.html` + `render/assets/*` | 数据注入 HTML，纯 ECharts 渲染，零业务逻辑 | `docs/index.html` + `assets/` |

`pipelines/build.py` 是编排入口（串起三层），`Makefile` 是一键命令。

## 为什么这样分层（扩展性）

- **新增数据源/指标**（如力量、饮食）：改 `extract.py` 加来源、`transform.py` 加规整，前端不动。
- **新增图表**：`render/template.html` 加一个 `<div>`，`render/assets/app.js` 加一个 `echarts.init` 配置块，数据已由 transform 备好。
- **换可视化库**（ECharts→Chart.js/plotly）：只动 `render/assets/`，pipeline 零改动。
- **新增展示页**：加一个 template，复用同一份 processed 数据。
- **可重跑 / 可审计**：raw 快照落盘，transform/render 随时离线重跑（`make offline`），不重新打 API。

## 命令

```bash
make build     # 全量：拉取→处理→渲染
make offline   # 离线重跑：用已有 raw 快照，不碰 API（调试图表用）
make serve     # 本地预览 http://localhost:8000
make test      # 自检
```

## 数据源（COROS）

- 跑步：`fetch_day(date)` — 结构化 dict 列表
- 坐标/地点：`get_sport_records_raw(start,end)` 文本解析（注意返回字面 `\n`，须 `replace("\\n","\n")`）
- 睡眠：`fetch_sleep(date)`；体重：`fetch_weight()`
- token 存 `~/.hermes/scripts/`，约 30 天需重授权

## 自动化

`cron` 每日 10:00 跑 `~/.hermes/scripts/sync-dashboard.sh`：`git pull → make build → git commit docs/ → push`。无变化静默，失败才报错。`data/` 不入库（可再生+cron 拉全量）。