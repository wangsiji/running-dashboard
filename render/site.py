"""表现层组装（render → 静态站）：processed/run_data.json + template.html → docs/ 站点。

职责：把标准化数据注入 HTML 骨架，把 assets 复制到产物目录。不含任何数据逻辑。
"""
import os, json, shutil

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(HERE, 'data', 'processed', 'run_data.json')
TEMPLATE = os.path.join(HERE, 'render', 'template.html')
ASSETS = os.path.join(HERE, 'render', 'assets')
OUT_DIR = os.path.join(HERE, 'docs')


def render():
    """读 processed 数据 → 写 docs/index.html + assets。返回输出 index 路径。"""
    with open(DATA_JSON, encoding='utf-8') as f:
        data = json.load(f)
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()

    json_str = json.dumps(data, ensure_ascii=False)
    html = html.replace('__DATA__', json_str)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    # assets 同步（每次覆盖，保证与代码一致）
    out_assets = os.path.join(OUT_DIR, 'assets')
    if os.path.isdir(out_assets):
        shutil.rmtree(out_assets)
    shutil.copytree(ASSETS, out_assets)

    return os.path.join(OUT_DIR, 'index.html')


if __name__ == '__main__':
    print('SITE ->', render())