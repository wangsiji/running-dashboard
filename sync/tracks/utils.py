"""Assorted utility methods for use in creating posters."""

# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import math
from datetime import datetime

import pytz
import s2sphere as s2

try:
    from tzfpy import get_tz

    tf = None
except ImportError:
    # tzfpy is not available, fallback to timezonefinder
    from timezonefinder import TimezoneFinder

    tf = TimezoneFinder()


from .xy import XY


# mercator projection
def latlng2xy(latlng: s2.LatLng) -> XY:
    return XY(lng2x(latlng.lng().degrees), lat2y(latlng.lat().degrees))


def lng2x(lng_deg: float) -> float:
    return lng_deg / 180 + 1


def lat2y(lat_deg: float) -> float:
    return 0.5 - math.log(math.tan(math.pi / 4 * (1 + lat_deg / 90))) / math.pi


def parse_datetime_to_local(start_time, end_time, point):
    if not point:
        timezone = "Asia/Shanghai"
    else:
        # just parse the start time, because start/end maybe different
        offset = start_time.utcoffset()
        if offset:
            return start_time + offset, end_time + offset
        lat, lng = point
        try:
            timezone = get_tz(lng=lng, lat=lat)
        except Exception as e:  # noqa: BLE001
            # just a little trick when tzfpy support windows will delete this
            print(f"tzfpy error: {e} fallback to timezonefinder")
            lat, lng = point
            timezone = tf.timezone_at(lng=lng, lat=lat)
    tc_offset = datetime.now(pytz.timezone(timezone)).utcoffset()
    return start_time + tc_offset, end_time + tc_offset


def get_normalized_sport_type(sport_type):
    if sport_type == "Run":
        return "running"
    elif sport_type == "Walk":
        return "walking"
    elif sport_type == "Ride":
        return "cycling"
    else:
        return sport_type
