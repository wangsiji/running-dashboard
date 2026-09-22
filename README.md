# 思己 · Running

跑步数据站。数据源：**高驰 COROS** → 自动同步 → GitHub Pages。

**站点**：https://wangsiji.github.io/running-dashboard/

## 它怎么工作

```
COROS API ──▶ run_page/coros_sync.py ──▶ run_page/generator/ ──▶ src/static/activities.json
                                                                        │
                                          GitHub Actions (每天 11:00) ────┘
                                                                        ▼
                                                              Pages 重新构建
```

`.github/workflows/run_data_sync.yml` 每天北京时间 11:00 触发：拉取高驰全部运动数据
（跑步/骑行/力量等）→ 生成 `activities.json` + `FIT_OUT/` 轨迹 → 提交回仓库 → 触发 Pages 重建。

## 目录

| 路径 | 作用 |
| --- | --- |
| `run_page/coros_sync.py` | 高驰数据同步入口 |
| `run_page/generator/` | 落库 + 生成 `activities.json` |
| `run_page/utils.py` | 运动类型映射、文件合并 |
| `run_page/polyline_processor.py` | 轨迹裁剪（`IGNORE_*` 环境变量） |
| `src/` | 前端（dashboard 主题） |
| `FIT_OUT/` `GPX_OUT/` `activities/` | 轨迹原始文件（自动生成） |
| `src/static/activities.json` | 站点唯一数据源（自动生成） |

配置在 `config.yml`（页面标题、主题、单位等）。

## 本地跑

```bash
pip install -r requirements.txt
python run_page/coros_sync.py <账号> <密码>

pnpm install
PATH_PREFIX=/ pnpm dev      # 本地预览
```

## 手动触发同步

```bash
gh workflow run run_data_sync.yml
```

## 说明

基于 [running_page](https://github.com/yihong0618/running_page) 精简而来 —— 只保留高驰
（COROS）一条数据链路，移除了其它数据源脚本、TUI、Docker/Vercel 部署和 classic 主题专用的
SVG 生成。地图默认走 CARTO 免费瓦片；如需 Mapbox，配 `MAPBOX_TOKEN` secret。
