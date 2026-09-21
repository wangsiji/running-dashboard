"""编排层：一键串起 采集 → 处理 → 渲染。

用法：
  python3 -m pipelines.build            # 全量：重新拉取 + 转换 + 渲染
  python3 -m pipelines.build --offline  # 用已有 raw 快照，不重新拉取（调试/重跑）
"""
import sys, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)


def main():
    offline = '--offline' in sys.argv

    from pipelines import extract, transform
    from render import site

    if not offline:
        raw = extract.extract()
        print('extract  ->', os.path.relpath(raw, HERE))
    tf = transform.transform()
    print('transform ->', os.path.relpath(tf, HERE))
    out = site.render()
    print('render  ->', os.path.relpath(out, HERE))
    print('OK')


if __name__ == '__main__':
    main()