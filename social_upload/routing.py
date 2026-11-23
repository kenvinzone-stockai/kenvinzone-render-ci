"""Định tuyến video → kênh YouTube (3 kênh, 3 bộ token OAuth).

  @kechuyen.chungkhoan  (nhóm "kechuyen")   VNINDEX bản tin ngày, Giải Mã tin tức
  @kenvinzone           (nhóm "kenvinzone") Vàng bias, Cổ phiếu Mỹ, Liên thị trường, Aurora Explainer
  @KenvinZone.tradequy  (nhóm "prop")       Trade Quỹ Future (Prop Promo & Prop Explainer)

Secrets:
  SOCIAL_UPLOAD_JSON        token OAuth kênh @kechuyen.chungkhoan
  YT_CHANNEL_ID             id kênh @kechuyen.chungkhoan
  SOCIAL_UPLOAD_JSON_KZ     token OAuth kênh @kenvinzone
  KENVINZONE_YT_CHANNEL_ID  id kênh @kenvinzone
  SOCIAL_UPLOAD_JSON_PROP   token OAuth kênh @KenvinZone.tradequy
  PROP_YT_CHANNEL_ID        id kênh @KenvinZone.tradequy
"""
from __future__ import annotations

import json
import os

KENVINZONE = "kenvinzone"
KECHUYEN = "kechuyen"
PROP = "prop"

KENVINZONE_PREFIXES = ("gold-", "equity-", "intermarket-", "giai-ma-trading-", "explainer-")
KENVINZONE_TEMPLATES = ("gold-daily-bias-hf", "equity-bias-hf", "intermarket-weekly-hf",
                        "aurora-trading-explainer-hf")
PROP_PREFIXES = ("prop-promo-", "prop-exp-")
PROP_TEMPLATES = ("prop-promo-hf", "prop-explainer-hf")

LABEL = {
    KENVINZONE: "@kenvinzone",
    KECHUYEN: "@kechuyen.chungkhoan",
    PROP: "@KenvinZone.tradequy",
}


def channel_group(project: str = "", template: str = "") -> str:
    """Nhóm kênh của 1 video. Biến YT_CHANNEL_GROUP (kenvinzone|kechuyen|prop) ép tay nếu cần."""
    forced = os.environ.get("YT_CHANNEL_GROUP", "").strip().lower()
    if forced in (KENVINZONE, KECHUYEN, PROP):
        return forced
    p = (project or "").strip().lower()
    t = (template or "").strip()
    if p.startswith(PROP_PREFIXES) or t in PROP_TEMPLATES:
        return PROP
    if p.startswith(KENVINZONE_PREFIXES) or t in KENVINZONE_TEMPLATES:
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

    if group == PROP:
        prop_raw = os.environ.get("SOCIAL_UPLOAD_JSON_PROP", "").strip()
        if prop_raw:
            ids = _channel_ids(prop_raw)
            cand = os.environ.get("PROP_YT_CHANNEL_ID", "").strip()
            return prop_raw, (cand if cand and cand in ids else ""), PROP
        print("  [cảnh báo kênh] Video thuộc @KenvinZone.tradequy nhưng chưa có SOCIAL_UPLOAD_JSON_PROP "
              "→ hãy bật --no-upload hoặc bổ sung secret.", flush=True)
        return "", "", PROP

    if group != KENVINZONE:
        return main_raw, main_chan, KECHUYEN

    kz_raw = os.environ.get("SOCIAL_UPLOAD_JSON_KZ", "").strip()
    if not kz_raw:
        print("  [cảnh báo kênh] Video thuộc @kenvinzone nhưng chưa có secret SOCIAL_UPLOAD_JSON_KZ "
              "→ TẠM đăng lên kênh mặc định (@kechuyen.chungkhoan).", flush=True)
        return main_raw, main_chan, KECHUYEN

    ids = _channel_ids(kz_raw)
    for cand in (os.environ.get("KENVINZONE_YT_CHANNEL_ID", "").strip(), main_chan):
        if cand and cand in ids:
            return kz_raw, cand, KENVINZONE
    return kz_raw, "", KENVINZONE
