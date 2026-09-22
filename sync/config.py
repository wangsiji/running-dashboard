"""所有数据路径的唯一定义处。

目录约定：
    <repo>/sync/   代码（同步管线）
    <repo>/data/   数据（全部生成物，随仓库一起提交）
"""

import os
from collections import namedtuple

# sync/ 的上一级就是项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

# ---- 数据文件 ----
SQL_FILE = os.path.join(DATA_DIR, "activities.db")  # 活动库 (sqlite)
JSON_FILE = os.path.join(DATA_DIR, "activities.json")  # 站点数据源
SYNCED_FILE = os.path.join(DATA_DIR, "imported.json")  # 已同步 id 记录
PLACES_FILE = os.path.join(DATA_DIR, "places.json")  # 坐标(~100m网格) → 地点名

# ---- 轨迹原始文件 ----
FIT_FOLDER = os.path.join(DATA_DIR, "fit")
GPX_FOLDER = os.path.join(DATA_DIR, "gpx")
TCX_FOLDER = os.path.join(DATA_DIR, "tcx")

FOLDER_DICT = {
    "gpx": GPX_FOLDER,
    "tcx": TCX_FOLDER,
    "fit": FIT_FOLDER,
}

# 目录不存在会让 os.listdir 直接抛错，这里统一建好
for _folder in (DATA_DIR, FIT_FOLDER, GPX_FOLDER, TCX_FOLDER):
    os.makedirs(_folder, exist_ok=True)

BASE_TIMEZONE = "Asia/Shanghai"
UTC_TIMEZONE = "UTC"

start_point = namedtuple("start_point", "lat lon")
run_map = namedtuple("polyline", "summary_polyline")
