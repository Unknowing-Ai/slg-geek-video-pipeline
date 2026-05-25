"""Step E2: 火山 ICL 语音复刻 - 上传训练数据 → 拿 speaker_id
用户给的 cluster=volcano_icl + x-api-key 模式
"""
import base64
import json
import os
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

API_KEY = os.environ["VOLC_ICL_API_KEY"]  # 火山 ICL api-key (env var)
ROOT = Path("pipeline/02-配音")

UPLOAD_URL = "https://openspeech.bytedance.com/api/v1/mega_tts/audio/upload"
STATUS_URL = "https://openspeech.bytedance.com/api/v1/mega_tts/status"

# 训练样本 — 用极客 ROK_头_01 分离后的纯人声
TRAIN_MP3 = ROOT / "vocal_only" / "ROK_头_01_train.mp3"
SPEAKER_ID = "S_geek_clone_v1"  # 自定义 speaker_id，TTS 时作为 voice_type


def post_json(url, body, headers):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
        except Exception:
            err_body = {"raw": str(e)}
        return e.code, err_body


def upload_training():
    mp3 = TRAIN_MP3.read_bytes()
    print(f"[upload] {TRAIN_MP3.name} {len(mp3)/1024:.0f}KB → speaker_id={SPEAKER_ID}")
    body = {
        "speaker_id": SPEAKER_ID,
        "audios": [{
            "audio_bytes": base64.b64encode(mp3).decode(),
            "audio_format": "mp3",
        }],
        "source": 2,
        "language": 0,
        "model_type": 1,
    }
    headers = {
        "Content-Type": "application/json",
        "Resource-Id": "volc.megatts.voiceclone",
        "Authorization": f"Bearer; {API_KEY}",
    }
    status, resp = post_json(UPLOAD_URL, body, headers)
    print(f"[upload resp] HTTP {status}")
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return status, resp


def check_status():
    body = {
        "appid": "",
        "speaker_ids": [SPEAKER_ID],
    }
    headers = {
        "Content-Type": "application/json",
        "Resource-Id": "volc.megatts.voiceclone",
        "Authorization": f"Bearer;{API_KEY}",
        "x-api-key": API_KEY,
    }
    status, resp = post_json(STATUS_URL, body, headers)
    print(f"[status resp] HTTP {status}")
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return status, resp


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "upload"
    if cmd == "upload":
        upload_training()
    elif cmd == "status":
        check_status()
    elif cmd == "both":
        upload_training()
        for i in range(20):
            time.sleep(15)
            print(f"\n[poll #{i+1}]")
            status, resp = check_status()
            # 解析状态字段（可能在 data.status 或 status）
            d = resp.get("data") or resp
            s = d.get("status") or (d.get("statuses", [{}])[0] if isinstance(d.get("statuses"), list) else None)
            if s in ("Success", "success", 2, "Active"):
                print("✅ 训练完成")
                break
            elif s in ("Failed", "failed", -1):
                print("❌ 训练失败")
                break
