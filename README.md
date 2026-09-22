# 思己 · Running

跑步数据站。数据源：**高驰 COROS** → 自动同步 → GitHub Pages。

**站点**：https://wangsiji.github.io/running-dashboard/

---

## 结构

```
├── sync/          ① 数据同步（Python）
│   ├── coros.py       高驰拉取入口
│   ├── gpx.py         本地轨迹导入入口
│   ├── config.py      所有数据路径的唯一定义处  ← 找路径看这里
│   ├── utils.py       运动类型映射、合并成 activities.json
│   ├── polyline_processor.py     轨迹裁剪（IGNORE_* 环境变量）
│   ├── synced_data_file_logger.py 已下载 id 的记录
│   ├── generator/     轨迹落库 + 生成站点数据
│   └── tracks/        轨迹模型与解析（gpx / fit）
│
├── data/          ② 全部数据（生成物，随仓库提交）
│   ├── activities.json    站点数据源（前端唯一读这个）
│   ├── activities.db      活动库 (sqlite)
│   ├── imported.json      已同步记录
│   ├── places.json  坐标→地点名缓存（反查限流时兜底）
│   └── fit/  gpx/   轨迹原始文件（高驰只用 fit/）
│
├── src/           ③ 前端源码（Vite + React + TS）
│   ├── core/          config / types / i18n / theme + hooks（数据加载）
│   ├── components/    页面组件（图表、地图、轨迹墙…）
│   ├── themes/dashboard/  页面主题
│   ├── assets/        地图 geojson
│   ├── utils/         汇总计算、导出卡片
│   └── workers/       轨迹聚类 worker
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

**密码只走 GitHub Secret**（`COROS_ACCOUNT` / `COROS_PASSWORD`），不入库不入命令行。

## 两个不那么显然的地方

**地点**：高驰接口不给地点，得拿坐标反查 OSM。而 Nominatim 限速约 1 req/s，
CI 对 267 条逐个查必被限流。所以整了 `data/places.json` 当缓存 —— 坐标按 ~100m 网格去重
（102 个起点就够了），命中直接用，未命中才联网。它随仓库提交，会自己长大。

**个人最佳**：按**最好分段**算（和高驰 App 同口径），从 FIT 每秒的
`(timestamp, distance)` 双指针滑出 5k/10k/半马/全马的最快区间。所以全马里跑出的最快
21.0975km 就是半马成绩 —— 别改成「活动总距离落在某个距离窗口内」，那样只会把日常
20km 训练跑当成 PB。

---

## 日常

```bash
# 手动触发一次同步（在 GitHub 上跑）
gh workflow run run_data_sync.yml

# 本地跑同步（密码建议先 export，别留在 shell history）
export COROS_ACCOUNT=xxx COROS_PASSWORD=xxx
python3 sync/coros.py --only-run        # 只要跑步数据，过滤骑行

# 只重算 JSON，不联网
python3 -c "
import sys; sys.path.insert(0, 'sync')
from config import FIT_FOLDER, SQL_FILE
from utils import make_activities_file
make_activities_file(SQL_FILE, FIT_FOLDER, '/tmp/out.json', 'fit', only_run=True)"

# 本地预览前端
pnpm install
PATH_PREFIX=/ pnpm dev

# 跑自检（CI 也会跑 sync/test_*.py）
for t in sync/test_*.py; do python3 "$t"; done

# 清空数据重来（places.json 缓存会保留，别手动删它）
pnpm run data:clean
```

## 「加载 0 tracks」怎么办

新加了要重算的字段（像 `best_efforts`）时，解析器只处理 `data/imported.json` 里**没有**的
文件 —— 历史记录全是"已处理"，新字段永远是空的。这时：

```bash
echo '[]' > data/imported.json   # 清空，触发全量重解析
```

同步日志**不要只看有没有报错**，要看 `load N tracks` 那个数字是不是 280。

## 说明

基于 [running_page](https://github.com/yihong0618/running_page) 精简而来：只保留高驰（COROS）
一条数据链路。删掉的东西：其它数据源同步脚本、TUI、Docker/Vercel 部署、classic 主题（及其专用
SVG 绘制代码）、strava 上传逻辑、兼容垫片、重复的 `city.ts`、**整条 TCX 解析链路**（无入口无数据，
`data/tcx/` 一直是空的）。

依赖用 AST 扫 `sync/` 的真实 import 算出来的（不是凭记忆列的），每次改完 import 值得重跑一遍；
`colour`、`tcxreader` 这类遗留正是这么揪出来的。
需要时都能从 git 历史或上游仓库取回。地图默认走 CARTO 免费瓦片；想要 Mapbox 就配 `MAPBOX_TOKEN` secret。
