import datetime
import json
import random
import string

from config import PLACES_FILE
from geopy.geocoders import Nominatim, options
from sqlalchemy import (
    JSON,
    Column,
    Float,
    Integer,
    Interval,
    String,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


# random user name 8 letters
def randomword():
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(4))


options.default_user_agent = "running_page"
# reverse the location (lat, lon) -> location detail
g = Nominatim(user_agent=randomword())

_places = None


def lookup_place(start_point):
    """查本地坐标缓存（~100m 网格）。

    仓库里带一份 data/places.json：同一个起点只查一次 Nominatim，CI 里既不必
    为 267 条活动打 267 次（会被限流、还会整批失败），也不再依赖 runner 能连上
    OSM。没命中再回落到 Nominatim。
    """
    global _places
    if _places is None:
        try:
            with open(PLACES_FILE, encoding="utf-8") as f:
                _places = json.load(f)
        except Exception:  # noqa: BLE001
            _places = {}
    if not start_point:
        return ""
    key = f"{round(start_point.lat, 3):.3f},{round(start_point.lon, 3):.3f}"
    return _places.get(key, "")


def reverse_geocode(start_point):
    """Nominatim 反查（缓存未命中时才走）。"""
    if not start_point:
        return ""
    for _ in range(2):  # 一次失败重试一次，仍失败就放弃
        try:
            return str(
                g.reverse(
                    f"{start_point.lat}, {start_point.lon}",
                    language="zh-CN",  # type: ignore
                    timeout=15,
                )
            )
        except Exception:  # noqa: BLE001, S112
            continue
    return ""


ACTIVITY_KEYS = [
    "run_id",
    "name",
    "distance",
    "moving_time",
    "type",
    "subtype",
    "start_date",
    "start_date_local",
    "location_country",
    "summary_polyline",
    "average_heartrate",
    "average_speed",
    "elevation_gain",
    "best_efforts",
]


class Activity(Base):
    __tablename__ = "activities"

    run_id = Column(Integer, primary_key=True)
    name = Column(String)
    distance = Column(Float)
    moving_time = Column(Interval)
    elapsed_time = Column(Interval)
    type = Column(String)
    subtype = Column(String)
    start_date = Column(String)
    start_date_local = Column(String)
    location_country = Column(String)
    summary_polyline = Column(String)
    average_heartrate = Column(Float)
    average_speed = Column(Float)
    elevation_gain = Column(Float)
    best_efforts = Column(JSON)
    streak = None

    def to_dict(self):
        out = {}
        for key in ACTIVITY_KEYS:
            attr = getattr(self, key)
            if isinstance(attr, (datetime.timedelta, datetime.datetime)):
                out[key] = str(attr)
            else:
                out[key] = attr

        if self.streak:
            out["streak"] = self.streak

        return out


def update_or_create_activity(session, run_activity):
    created = False
    try:
        activity = (
            session.query(Activity).filter_by(run_id=int(run_activity.id)).first()
        )

        current_elevation_gain = 0.0  # default value

        # https://github.com/stravalib/stravalib/blob/main/src/stravalib/strava_model.py#L639C1-L643C41
        if (
            hasattr(run_activity, "total_elevation_gain")
            and run_activity.total_elevation_gain is not None
        ):
            current_elevation_gain = float(run_activity.total_elevation_gain)
        elif (
            hasattr(run_activity, "elevation_gain")
            and run_activity.elevation_gain is not None
        ):
            current_elevation_gain = float(run_activity.elevation_gain)

        # 地点要在「新建」和「更新」两条路径上都补：以前这段只写在新建分支里，
        # 于是历史记录一旦是空的就永远是空的（重新同步也不会回填）。
        start_point = getattr(run_activity, "start_latlng", None)
        location_country = getattr(run_activity, "location_country", "") or ""
        if not location_country and activity:
            location_country = activity.location_country or ""
        if location_country == "China":  # 历史脏值，重查
            location_country = ""
        if not location_country:
            location_country = lookup_place(start_point) or reverse_geocode(start_point)

        if not activity:
            activity = Activity(
                run_id=run_activity.id,
                name=run_activity.name,
                distance=run_activity.distance,
                moving_time=run_activity.moving_time,
                elapsed_time=run_activity.elapsed_time,
                type=run_activity.type,
                subtype=run_activity.subtype,
                start_date=run_activity.start_date,
                start_date_local=run_activity.start_date_local,
                location_country=location_country,
                average_heartrate=run_activity.average_heartrate,
                average_speed=float(run_activity.average_speed),
                elevation_gain=current_elevation_gain,
                summary_polyline=(
                    run_activity.map and run_activity.map.summary_polyline or ""
                ),
                best_efforts=getattr(run_activity, "best_efforts", None) or None,
            )
            session.add(activity)
            created = True
        else:
            activity.name = run_activity.name
            activity.distance = float(run_activity.distance)
            activity.moving_time = run_activity.moving_time
            activity.elapsed_time = run_activity.elapsed_time
            activity.type = run_activity.type
            activity.subtype = run_activity.subtype
            activity.average_heartrate = run_activity.average_heartrate
            activity.average_speed = float(run_activity.average_speed)
            activity.elevation_gain = current_elevation_gain
            activity.summary_polyline = (
                run_activity.map and run_activity.map.summary_polyline or ""
            )
            activity.best_efforts = (
                getattr(run_activity, "best_efforts", None) or activity.best_efforts
            )
            if location_country:
                activity.location_country = location_country
    except Exception as e:  # noqa: BLE001
        print(f"something wrong with {run_activity.id}")
        print(str(e))

    return created


def add_missing_columns(engine, model):
    inspector = inspect(engine)
    table_name = model.__tablename__
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    missing_columns = []

    for column in model.__table__.columns:
        if column.name not in columns:
            missing_columns.append(column)
    if missing_columns:
        with engine.connect() as conn:
            for column in missing_columns:
                column_type = str(column.type)
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type}"
                    )
                )


def init_db(db_path):
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)

    # check missing columns
    add_missing_columns(engine, Activity)

    sm = sessionmaker(bind=engine)
    session = sm()
    # apply the changes
    session.commit()
    return session
