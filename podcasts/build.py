#!/usr/bin/env python3
"""
本周电波 · 播客文稿库 — 构建脚本

把 manifest.json + transcripts/*.md + template.html 打包成一个
完全自包含（无外部依赖）的 index.html。

用法:
    python3 build.py            # 生成 index.html
    python3 build.py --check    # 只校验、不写文件

新增一集见 README.md。
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read(path):
    with io.open(os.path.join(HERE, path), encoding="utf-8") as f:
        return f.read()


def esc_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(check_only=False):
    manifest = json.loads(read("manifest.json"))
    meta = manifest["meta"]
    episodes = manifest["episodes"]
    template = read("template.html")

    errors = []
    seen_ids, seen_accents = set(), {}
    valid_cats = set(manifest["categories"])

    # ---- validate + load transcripts ----
    transcript_blocks = []
    for e in episodes:
        for field in ("id", "file", "show", "title", "date", "ep"):
            if not e.get(field):
                errors.append(f"[{e.get('id','?')}] 缺少字段: {field}")
        if e["id"] in seen_ids:
            errors.append(f"重复的 id: {e['id']}")
        seen_ids.add(e["id"])
        for c in e.get("cats", []):
            if c not in valid_cats:
                errors.append(f"[{e['id']}] 未知分类: {c}")
        e.setdefault("md", "md-" + e["id"])
        e.setdefault("tags", [])
        e.setdefault("cats", [])
        e.setdefault("hl", [])
        e.setdefault("blurb", "")
        e.setdefault("eyebrow", "")
        e.setdefault("dur", "")

        fp = os.path.join(HERE, "transcripts", e["file"])
        if not os.path.exists(fp):
            errors.append(f"[{e['id']}] 找不到文稿: transcripts/{e['file']}")
            continue
        content = read(os.path.join("transcripts", e["file"])).strip()
        if "</script" in content.lower():
            errors.append(f"[{e['id']}] 文稿含 '</script'，会破坏页面")
        transcript_blocks.append(
            f'<script type="text/markdown" id="{e["md"]}">\n{content}\n</script>'
        )

    if errors:
        print("构建失败：")
        for x in errors:
            print("  ✗ " + x)
        sys.exit(1)

    # ---- derived stats ----
    count = len(episodes)
    producers = len({re.split(r"·", e["show"])[0].strip() for e in episodes})
    stats = [
        (str(count), "档节目"),
        (meta.get("statHours", ""), "小时时长"),
        (str(producers), "档制作方"),
        ("全文", "不删减"),
    ]
    stats_html = "".join(
        f'<div class="stat"><div class="n">{esc_html(n)}</div>'
        f'<div class="l">{esc_html(l)}</div></div>'
        for n, l in stats
    )

    # episodes payload for the app (drop build-only keys)
    payload = [{k: v for k, v in e.items() if k != "file"} for e in episodes]

    out = template
    repl = {
        "<!--TRANSCRIPTS-->": "\n".join(transcript_blocks),
        "__EPISODES__": json.dumps(payload, ensure_ascii=False),
        "__CATLABELS__": json.dumps(manifest["categories"], ensure_ascii=False),
        "__CATORDER__": json.dumps(manifest["categoryOrder"], ensure_ascii=False),
        "__STATS__": stats_html,
        "__COUNT__": str(count),
        "__WEEKLABEL__": esc_html(meta["weekLabel"]),
        "__HEROTITLE__": esc_html(meta["heroTitle"]),
        "__HEROLEAD__": esc_html(meta["heroLead"]),
        "__BRAND__": esc_html(meta["brand"]),
        "__BRANDSUB__": esc_html(meta["brandSub"]),
    }
    for k, v in repl.items():
        if k not in out:
            print(f"警告：模板缺少占位符 {k}")
        out = out.replace(k, v)

    left = re.findall(r"__[A-Z]+__|<!--TRANSCRIPTS-->", out)
    if left:
        print("构建失败：仍有未替换的占位符", left)
        sys.exit(1)

    kb = round(len(out.encode("utf-8")) / 1024)
    print(f"✓ {count} 档节目 · {producers} 档制作方 · {kb} KB")
    if check_only:
        print("(--check：未写文件)")
        return
    with io.open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print("✓ 已生成 index.html")


if __name__ == "__main__":
    build(check_only="--check" in sys.argv)
