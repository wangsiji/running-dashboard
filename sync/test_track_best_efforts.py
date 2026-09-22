import sys

sys.path.insert(0, "/tmp/running_page/sync")

from tracks.track import BEST_EFFORT_TARGETS, best_efforts


def synt(n, pace_s_per_km, start=0.0):
    """匀速假轨迹：n 个点，每点 100m，每公里 pace 秒"""
    return [(start + i * pace_s_per_km / 10, i * 100.0) for i in range(n)]


def demo():
    pts = synt(423, 300)  # 42.2km @ 5:00/km，够全马档（≥ 42195*0.99）
    e = best_efforts(pts)
    assert set(e) == {"5k", "10k", "half", "marathon"}, e
    for k, _ in BEST_EFFORT_TARGETS:
        pass
    assert 1480 < e["5k"] < 1520, e["5k"]  # 5km ≈ 1500s
    assert 2980 < e["10k"] < 3020, e["10k"]  # 10km ≈ 3000s
    assert e["half"] > e["10k"], e
    assert e["marathon"] > e["half"], e
    # 半马 ≈ 21097m / 100m 每点 @30s → ~6329s
    assert 6290 < e["half"] < 6370, e["half"]

    # 变速：前半慢后半快 → 最好分段必须比匀速快
    slow = synt(211, 360)  # 21.0km @ 6:00/km
    off = slow[-1][0]
    fast = [
        (off + t, slow[-1][1] + d)
        for t, d in [(i * 18, i * 100.0) for i in range(1, 211)]
    ]  # 后半 @ 3:00/km
    e2 = best_efforts(slow + fast)
    assert e2["half"] < e["half"], (e2["half"], e["half"])  # 快段的半马更快
    assert e2["half"] < 3900, e2["half"]  # < 65min，取自快段

    # 短距离：不到 5km 的活动不给任何档
    assert best_efforts(synt(30, 300)) == {}
    # 点太少直接空
    assert best_efforts([(0, 0.0), (1, 1.0)]) == {}
    print("best_efforts 自检通过 ✓", e, e2)


demo()
