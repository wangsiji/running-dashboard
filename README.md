# 思己 · Running

跑步数据站。数据源：**高驰 COROS** → 自动同步 → GitHub Pages。

**站点**：https://wangsiji.github.io/running-dashboard/

---

## 结构

```
├── sync/          ① 数据同步（Python）
│   ├── coros.py       高驰拉取入口
│   ├── gpx.py         本地 GPX 导入入口
│   ├── config.py      所有数据路径的唯一定义处  ← 找路径看这里
│   ├── utils.py       运动类型映射、合并成 activities.json
│   ├── polyline_processor.py  轨迹裁剪（IGNORE_* 环境变量）
│   ├── generator/     轨迹落库 + 生成站点数据
│   └── gpxtrackposter/ 轨迹解析（gpx/fit）
│
├── data/          ② 全部数据（生成物，随仓库提交）
│   ├── activities.json    站点数据源（前端唯一读这个）
│   ├── activities.db      活动库 (sqlite)
│   ├── imported.json      已同步记录
│   ├── fit/  gpx/  tcx/   轨迹原始文件
│
├── src/           ③ 前端源码（Vite + React + TS）
│   ├── core/          数据加载、配置、hooks
│   ├── components/    页面组件（图表、地图、轨迹墙…）
│   ├── themes/dashboard/  页面主题
│   └── static/        纯静态资源（地图 geojson、站点元信息）
│
├── config.yml     ④ 站点配置（标题、主题、单位）
├── public/        ⑤ 不参与打包的静态文件
└── .github/workflows/
    ├── run_data_sync.yml   每天 11:00 同步 + 发布
    ├── gh-pages.yml        构建并部署 Pages
    └── ci.yml              代码检查
```

**一句话数据流**：`sync/coros.py` 拉高驰 → `data/fit/` 存轨迹 → `generator/` 落库 →
生成 `data/activities.json` → 前端读它渲染 → Actions 提交并重新部署。

---

## 日常

```bash
# 手动触发一次同步（在 GitHub 上跑）
gh workflow run run_data_sync.yml

# 本地跑同步
pip install -r requirements.txt
python sync/coros.py <账号> <密码>

# 本地预览前端
pnpm install
PATH_PREFIX=/ pnpm dev

# 清空数据重来
pnpm run data:clean
```

## 说明

基于 [running_page](https://github.com/yihong0618/running_page) 精简而来：只保留高驰（COROS）
一条数据链路。删掉的东西：其它数据源同步脚本、TUI、Docker/Vercel 部署、classic 主题（及其专用
SVG 绘制代码）、strava 上传逻辑、兼容垫片、重复的 `city.ts`。
需要时都能从 git 历史或上游仓库取回。地图默认走 CARTO 免费瓦片；想要 Mapbox 就配 `MAPBOX_TOKEN` secret。
