"""Định tuyến video → kênh YouTube (2 kênh, 2 bộ token OAuth).

  @kechuyen.chungkhoan  (nhóm "kechuyen")   VNINDEX bản tin ngày, Giải Mã tin tức (link Telegram)
  @kenvinzone           (nhóm "kenvinzone") Vàng bias, Cổ phiếu Mỹ (S&P 500 + Nasdaq), Liên thị trường,
                                            Aurora Trading Explainer

Secrets:
  SOCIAL_UPLOAD_JSON        token OAuth kênh @kechuyen.chungkhoan (như cũ)
  YT_CHANNEL_ID             id kênh @kechuyen.chungkhoan (như cũ)
  SOCIAL_UPLOAD_JSON_KZ     token OAuth kênh @kenvinzone (tạo bằng tools/yt_add_channel.py)
  KENVINZONE_YT_CHANNEL_ID  (tuỳ chọn) id kênh @kenvinzone; bỏ trống = kênh duy nhất trong SOCIAL_UPLOAD_JSON_KZ

Mỗi bộ token có client OAuth riêng, nên KHÔNG gộp 2 file — chỉ chọn 1 file theo nhóm.
Nếu nhóm "kenvinzone" mà chưa có SOCIAL_UPLOAD_JSON_KZ → tạm đăng kênh mặc định + in cảnh báo
(để dây chuyền không dừng trong lúc chưa cấp token).
"""
from __future__ import annotations

import json
import os

KENVINZONE = "kenvinzone"
KECHUYEN = "kechuyen"

# Tiền tố thư mục slide/<project> của các dòng đăng lên @kenvinzone.
KENVINZONE_PREFIXES = ("gold-", "equity-", "intermarket-", "giai-ma-trading-", "explainer-")
# Template của các dòng đó (phòng khi tên project đặt tay).
KENVINZONE_TEMPLATES = ("gold-daily-bias-hf", "equity-bias-hf", "intermarket-weekly-hf",
                        "aurora-trading-explainer-hf")

LABEL = {KENVINZONE: "@kenvinzone", KECHUYEN: "@kechuyen.chungkhoan"}


def channel_group(project: str = "", template: str = "") -> str:
    """Nhóm kênh của 1 video. Biến YT_CHANNEL_GROUP (kenvinzone|kechuyen) ép tay nếu cần."""
    forced = os.environ.get("YT_CHANNEL_GROUP", "").strip().lower()
    if forced in (KENVINZONE, KECHUYEN):
        return forced
    p = (project or "").strip().lower()
    if p.startswith(KENVINZONE_PREFIXES) or (template or "").strip() in KENVINZONE_TEMPLATES:
        return KENVINZONE
    return KECHUYEN


def _channel_ids(raw: str) -> list[str]:
    try:
        yt = (json.loads(raw) or {}).get("youtube") or {}
    except (json.JSONDecodeError, AttributeError):
        return []
    ids = [str(c.get("id") or "").strip() for c in (yt.get("channels") or []) if isinstance(c, dict)]
    return [i for i in ids if i]


def resolve(group: str) -> tuple[str, str, str]:
    """→ (raw_json, channel_id, group_thực_dùng). channel_id "" = kênh active trong file."""
    main_raw = os.environ.get("SOCIAL_UPLOAD_JSON", "").strip()
    main_chan = os.environ.get("YT_CHANNEL_ID", "").strip()
    if group != KENVINZONE:
        return main_raw, main_chan, KECHUYEN

    kz_raw = os.environ.get("SOCIAL_UPLOAD_JSON_KZ", "").strip()
    if not kz_raw:
        print("  [cảnh báo kênh] Video thuộc @kenvinzone nhưng chưa có secret SOCIAL_UPLOAD_JSON_KZ "
              "→ TẠM đăng lên kênh mặc định (@kechuyen.chungkhoan).", flush=True)
        return main_raw, main_chan, KECHUYEN

    ids = _channel_ids(kz_raw)
    # Ưu tiên: KENVINZONE_YT_CHANNEL_ID → YT_CHANNEL_ID của dòng (vd GOLD_YT_CHANNEL_ID) nếu nó
    # nằm trong file KZ → kênh active của file KZ. Không bao giờ dùng id kênh @kechuyen với token KZ.
    for cand in (os.environ.get("KENVINZONE_YT_CHANNEL_ID", "").strip(), main_chan):
        if cand and cand in ids:
            return kz_raw, cand, KENVINZONE
    return kz_raw, "", KENVINZONE
