import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator import _interpolate, _is_loop, _route_length_m


def demo():
    # 1km 纬度 ≈ 111.19km（haversine 库值）
    km = _route_length_m([(0.0, 0.0), (1.0, 0.0)])
    assert 111_000 < km < 111_400, km

    # 往返 = 单程 x2
    there = _route_length_m([(0.0, 0.0), (0.5, 0.0)])
    back = _route_length_m([(0.0, 0.0), (0.5, 0.0), (0.0, 0.0)])
    assert abs(back - there * 2) < 1, (back, there * 2)

    # 空/单点 = 0
    assert _route_length_m([]) == 0.0
    assert _route_length_m([(1.0, 2.0)]) == 0.0

    # 插值取中点
    assert _interpolate((0.0, 0.0), (2.0, 4.0), 0.5) == (1.0, 2.0)
    assert _interpolate((0.0, 0.0), (2.0, 4.0), 0.0) == (0.0, 0.0)

    # 闭环判定：起终点够近才算环
    assert _is_loop([(0.0, 0.0), (0.1, 0.1), (0.0, 0.0)])
    assert not _is_loop([(0.0, 0.0), (1.0, 1.0)])
    assert not _is_loop([(0.0, 0.0), (0.1, 0.1)])  # 点太少

    print("generator 几何自检通过 ✓", f"{km:.0f}m")


demo()
