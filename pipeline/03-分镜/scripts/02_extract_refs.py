"""
Step 2 · 02 - 抓宿主资产 → 上传 liclick

跨产品通用 - 支持两种资产来源:
  A. 飞书 base 资产库（推荐, 莉莉丝项目通常都有）
     需宿主提供: base_token / table_id / table 当前 rev / 角色清单（含 file_token）
  B. 本地图片文件（无飞书 base 时, 宿主直接给图）
     需宿主提供: 角色清单 + 对应本地图片路径

输入 manifest.json:
{
  "source": "feishu_base" | "local",
  "base_token": "...",       # source=feishu_base 必填
  "table_id": "...",         # source=feishu_base 必填
  "table_rev": 658,          # source=feishu_base 必填（查 base +base-get 拿）
  "assets": {
    "name1": "file_token_or_local_path",
    "name2": "..."
  }
}

输出: rok_asset_map.json（兼容 03_genimg.py 用）, 实际是通用 asset_map.json

Usage:
    python 02_extract_refs.py <manifest.json> <out_dir>
"""
import json, subprocess, sys, re, shutil
from pathlib import Path

MANIFEST = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
OUT_DIR = Path(sys.argv[2])
OUT_DIR.mkdir(parents=True, exist_ok=True)

TMP = Path("/tmp/_skill_refs")
TMP.mkdir(exist_ok=True)
for f in TMP.glob("*"):
    f.unlink()

source = MANIFEST.get("source", "feishu_base")
assets = MANIFEST["assets"]
print(f"Source: {source} | Assets: {len(assets)}")

# === 1. 准备本地图片 ===
local_files = {}
if source == "feishu_base":
    base_token = MANIFEST["base_token"]
    table_id = MANIFEST["table_id"]
    rev = MANIFEST["table_rev"]
    extra = json.dumps({"extra": json.dumps({"bitablePerm": {"tableId": table_id, "rev": rev}})})

    import os
    os.chdir(TMP)
    for name, ft in assets.items():
        r = subprocess.run([
            "lark-cli", "api", "GET", f"/open-apis/drive/v1/medias/{ft}/download",
            "--params", extra, "--output", f"{name}.png"
        ], capture_output=True, text=True, timeout=60)
        if (TMP / f"{name}.png").exists():
            local_files[name] = TMP / f"{name}.png"
            print(f"  Downloaded: {name}")
        else:
            print(f"  ✗ {name}: {r.stderr[:200]}")
elif source == "local":
    for name, path in assets.items():
        src = Path(path)
        if src.exists():
            dst = TMP / f"{name}{src.suffix}"
            shutil.copy(src, dst)
            local_files[name] = dst
            print(f"  Copied local: {name} ({src})")
        else:
            print(f"  ✗ {name}: file not found {path}")
else:
    sys.exit(f"Unknown source: {source}. Must be 'feishu_base' or 'local'")

# === 2. 上传 liclick ===
asset_map = {}
for name, fp in local_files.items():
    r = subprocess.run([
        "atlas-skillhub", "gateway", "call-tool",
        "--service", "liclick", "--tool", "upload_asset",
        "--file", f"file_path={fp}", "asset_type=image",
    ], capture_output=True, text=True, timeout=120)
    out = r.stdout.strip()
    try:
        obj = json.loads(out)
    except Exception:
        m = re.search(r'\{[\s\S]*\}\s*$', out)
        obj = json.loads(m.group(0)) if m else {}
    text = "".join([c.get("text", "") for c in obj.get("content", [])])
    m = re.search(r'asset_id["\s:`]+([a-zA-Z0-9_-]+)', text)
    asset_map[name] = m.group(1) if m else None
    print(f"  Uploaded: {name} -> {asset_map[name]}")

(OUT_DIR / "asset_map.json").write_text(
    json.dumps(asset_map, ensure_ascii=False, indent=2), encoding="utf-8")
# 兼容旧脚本名
(OUT_DIR / "rok_asset_map.json").write_text(
    json.dumps(asset_map, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nOK -> {OUT_DIR}/asset_map.json ({len(asset_map)} assets)")
