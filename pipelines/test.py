"""冒烟自检：验证 transform 产物 schema 完整且数值合理。无框架。"""
import os, sys, json, math

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)


def main():
    from pipelines.transform import transform
    out = transform()
    d = json.load(open(out, encoding='utf-8'))

    assert 'stats' in d and 'days' in d and 'geo' in d, "schema 缺键"
    st = d['stats']
    assert st['total_runs'] == len(d['days']), f"runs 数不一致: {st['total_runs']} vs {len(d['days'])}"
    assert st['total_km'] > 0, "累计距离异常"
    for day in d['days']:
        assert day['dist_km'] >= 0, f"负距离 {day}"
        if day.get('pace'):
            assert 3 <= day['pace'] <= 12, f"配速越界 {day['pace']} (3–12分/km)"
    print(f"自检通过: {len(d['days'])} 天, 累计 {st['total_km']} km, {len(d['geo'])} 个坐标点")
    return 0


if __name__ == '__main__':
    sys.exit(main())