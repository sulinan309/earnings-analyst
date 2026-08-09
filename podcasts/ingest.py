#!/usr/bin/env python3
"""
本周电波 · 自动收录脚本

扫描 transcripts/ 目录：
  1. 对内容重复的文稿（与已收录的某集完全相同）自动跳过（去重）；
  2. 对尚未登记、且非重复的新 .md，解析文头，自动在 manifest.json 里生成一条
     「草稿」条目（标 needsReview:true / 卡片显示「待整理」）；
  3. 按日期倒序排好，最后调用 build.py 重新生成 index.html。

分类(cats)、要点(hl)、导语(blurb) 这类需要判断的字段留空，事后再润色即可——
不影响先把文稿读起来。

用法:
    python3 ingest.py            # 收录 + 构建
    python3 ingest.py --dry-run  # 只报告会发生什么，不写文件
"""
import io
import os
import re
import sys
import json
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
TDIR = os.path.join(HERE, "transcripts")
MANIFEST = os.path.join(HERE, "manifest.json")

# 同一节目沿用同一强调色；未知节目从后备色板轮换取色
SHOW_COLORS = {
    "Odd Lots": "#2F9E93",
    "Hard Fork": "#CF8A3A",
    "ChinaTalk": "#7E8B44",
    "20VC": "#8B6FC7",
    "Invest Like the Best": "#C05A44",
    "All-In": "#5E7C88",
    "Latent Space": "#C15F8A",
    "Sinica": "#9E4E5E",
    "No Priors": "#4E8B57",
    "Interconnects": "#5D6BC0",
}
FALLBACK_COLORS = ["#4F7DC9", "#B07C3A", "#4C8C9E", "#9A5CB0", "#3F8F6B", "#B5643E"]


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def norm(text):
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def digest(text):
    return hashlib.sha1(norm(text).encode("utf-8")).hexdigest()


def base_show(show):
    return re.split(r"[·（(]", show)[0].strip()


def parse_header(md):
    lines = md.splitlines()
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    def field(*keys):
        for line in lines[:60]:
            m = re.match(r"^\*\*\s*([^：:*]+?)\s*[：:]\s*\*\*\s*(.+)$", line)
            if m and m.group(1).strip() in keys:
                return m.group(2).strip()
        return ""

    show = field("节目", "播客")
    date = field("日期", "播出", "发布")
    host = field("主持", "主持人", "主持/引入", "主持/制作")
    guest = field("嘉宾", "受访者")
    return title, show, date, host, guest


def norm_date(s):
    nums = re.findall(r"\d+", s)
    if len(nums) >= 3:
        return f"{nums[0]}·{int(nums[1]):02d}·{int(nums[2]):02d}"
    if len(nums) >= 2:
        return f"{nums[0]}·{int(nums[1]):02d}"
    if len(nums) >= 1:
        return nums[0]
    return ""


def date_key(d):
    nums = re.findall(r"\d+", d or "")
    y = int(nums[0]) if len(nums) >= 1 else 0
    m = int(nums[1]) if len(nums) >= 2 else 0
    day = int(nums[2]) if len(nums) >= 3 else 0
    return (y, m, day)


def main(dry_run=False):
    manifest = json.loads(read(MANIFEST))
    episodes = manifest["episodes"]
    by_id = {e["id"]: e for e in episodes}

    # 已收录文稿的内容指纹 -> id（用于内容级去重）
    seen = {}
    for e in episodes:
        fp = os.path.join(TDIR, e["file"])
        if os.path.exists(fp):
            seen[digest(read(fp))] = e["id"]

    files = sorted(f for f in os.listdir(TDIR) if f.endswith(".md"))
    added, dups = [], []
    pal = 0

    for fname in files:
        eid = fname[:-3]
        content = read(os.path.join(TDIR, fname))
        d = digest(content)
        if eid in by_id:
            continue  # 已登记
        if d in seen:
            dups.append((fname, seen[d]))  # 内容与某集重复 -> 跳过
            continue
        title, show, date, host, guest = parse_header(content)
        show = show or "未分类"
        color = SHOW_COLORS.get(base_show(show))
        if not color:
            color = FALLBACK_COLORS[pal % len(FALLBACK_COLORS)]
            pal += 1
        entry = {
            "id": eid, "file": fname, "ep": color,
            "show": show, "eyebrow": "",
            "title": title or eid, "date": norm_date(date),
            "dur": "", "host": host, "guest": guest,
            "tags": [], "cats": [], "blurb": "", "hl": [],
            "needsReview": True,
        }
        episodes.append(entry)
        by_id[eid] = entry
        seen[d] = eid
        added.append(entry)

    episodes.sort(key=lambda e: date_key(e.get("date", "")), reverse=True)

    print(f"扫描 {len(files)} 篇文稿：新增 {len(added)}，跳过重复 {len(dups)}")
    for e in added:
        print(f"  + {e['id']}  「{e['title'][:30]}」  {e['show']}  {e['date']}  (待整理)")
    for fname, other in dups:
        print(f"  ~ 跳过重复: {fname}（与已收录的 {other} 内容相同）")

    if dry_run:
        print("(--dry-run：未写文件)")
        return

    with io.open(MANIFEST, "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    # 复用 build.py 生成自包含的 index.html
    import build
    build.build()


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
