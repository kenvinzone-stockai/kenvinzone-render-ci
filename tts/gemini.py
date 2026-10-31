"""Gemini TTS engine — generates per-slide or full voiceover audio via Google Gemini API.

Uses the Gemini TTS models (gemini-2.5-flash-preview-tts or gemini-2.5-pro-preview-tts)
to synthesize speech from script text.  Output is PCM 24 kHz mono → converted to MP3.

Config lives in config/tts.json under the "gemini" key:
    {
        "gemini": {
            "api_key": "...",
            "model": "gemini-2.5-flash-preview-tts",
            "voice": "Kore",
            "style_prompt": "",
            "cooldown": 2.0
        }
    }

Environment variable GEMINI_API_KEY takes precedence over config file.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any

from .common import generate_project_tts

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_VOICE = "Kore"
DEFAULT_COOLDOWN = 2.0
SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2  # 16-bit
CHANNELS = 1

MAX_RETRIES = 3
BASE_DELAY = 5.0

# All 30 available voices with style descriptions
VOICES = {
    "Zephyr": "Bright",
    "Puck": "Upbeat",
    "Charon": "Informative",
    "Kore": "Firm",
    "Fenrir": "Excitable",
    "Leda": "Youthful",
    "Orus": "Firm",
    "Aoede": "Breezy",
    "Callirrhoe": "Easy-going",
    "Autonoe": "Bright",
    "Enceladus": "Breathy",
    "Iapetus": "Clear",
    "Umbriel": "Easy-going",
    "Algieba": "Smooth",
    "Despina": "Smooth",
    "Erinome": "Clear",
    "Algenib": "Gravelly",
    "Rasalgethi": "Informative",
    "Laomedeia": "Upbeat",
    "Achernar": "Soft",
    "Alnilam": "Firm",
    "Schedar": "Even",
    "Gacrux": "Mature",
    "Pulcherrima": "Forward",
    "Achird": "Friendly",
    "Zubenelgenubi": "Casual",
    "Vindemiatrix": "Gentle",
    "Sadachbia": "Lively",
    "Sadaltager": "Knowledgeable",
    "Sulafat": "Warm",
}

MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-pro-preview-tts",
    "gemini-3.8-flash-tts",
    "gemini-3.8-flash-lite-tts",
]

# Fallback order when a model hits 429 quota limit
FALLBACK_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-pro-preview-tts",
]

# ---------------------------------------------------------------------------
# Cloned (replicated) voice support - Gemini 3.8 interactions API
# ---------------------------------------------------------------------------
import re as _re
CLONE_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
CLONE_MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"]
AUTO_CLONE_VOICE = "auto-clone"
CLONE_DEFAULT_STYLE = {
    "vi": "giọng dẫn bản tin tài chính, rõ ràng, tự tin, nhịp vừa phải",
    "en": "calm, confident market-analyst delivery, measured pace",
}
_VI_RE = _re.compile("[ăâđêôơưĂÂĐÊÔƠƯẠ-ỿ]")


# ---------------------------------------------------------------------------
# Style Presets — Advanced TTS Prompting (Gemini Prompting Guide format)
# ---------------------------------------------------------------------------
STYLE_PRESETS: dict[str, dict[str, str]] = {
    "under-the-button-en": {
        "label": "Under the Button — EN Market Analyst",
        "voice": "Orus",
        "prompt": """# AUDIO PROFILE: The Desk Analyst

A calm, precise English-speaking market analyst who explains derivatives mechanics to people who already trade. He does not hype. He earns attention by showing the reader something they had not noticed in a thing they use every day.

## THE SCENE: Trading Desk, After the Close
A quiet desk after the US session. Screens still on, nobody shouting. He is talking one professional to another, not lecturing a beginner.

### DIRECTOR'S NOTES

Style:
* Measured authority. Never salesy, never breathless. Confidence comes from precision, not volume.
* Deliver the reveal lines with a slight drop in pace and pitch, as if letting the listener catch it themselves.
* Numbers, percentages and formula terms get crisp enunciation and a short beat before and after.
* Dry, understated wit is allowed on the "everyone reads it wrong" beats. Never mocking.

Pacing:
* Default pace: unhurried, conversational, clear.
* Slow down noticeably on the mechanism explanation and on any risk or cost warning.
* Natural breathing pauses between sentences. Never robotic.

Accent: Neutral international English. Clear enunciation of financial terminology.

IMPORTANT: Read ONLY the transcript below. Do not read these notes aloud. Output English only.

#### TRANSCRIPT""",
    },
    "giai-ma-nganh": {
        "label": "Giải Mã Ngành — Financial Storyteller",
        "voice": "Sulafat",
        "prompt": """# AUDIO PROFILE: Minh Khôi
## "The Financial Storyteller"

Minh Khôi is a trusted Vietnamese financial narrator who explains complex stock market sector analysis in a warm, relatable way. He speaks like a knowledgeable neighbor sharing insider wisdom over coffee — authoritative but never condescending, using vivid everyday metaphors that Vietnamese retail investors instantly understand.

## THE SCENE: Evening Podcast Studio
A cozy, acoustically treated home studio in Ho Chi Minh City. Warm amber desk lamp, a single microphone, and the faint glow of stock charts on a monitor behind. It's 8 PM — the market has closed, and Minh Khôi is recording his weekly sector deep-dive for retail investors who want to understand what's really happening beneath the surface.

### DIRECTOR'S NOTES

Style:
* Warm authority — the listener should feel like they're getting privileged insight from a trusted friend who genuinely cares about their financial wellbeing.
* Use a "vocal smile" on positive data points and opportunities — the listener should hear genuine enthusiasm when discussing good metrics.
* Shift to a grave, measured tone for risk warnings and red flags — slow down noticeably, lower pitch slightly, create weight.
* Numbers and statistics should be delivered with crisp emphasis — pronounce each digit clearly with a brief beat before and after key figures.
* Vietnamese metaphors and colloquialisms should sound natural and conversational, not rehearsed.

Pacing:
* Default pace: moderate, like telling a story to a friend — not rushed, not dragging.
* Speed up slightly when building excitement about opportunities or positive data.
* Slow down significantly for risk warnings, disclaimers, and "bài học xương máu" moments.
* Natural breathing pauses between sentences — never sound robotic or mechanical.
* Brief dramatic pause before revealing key numbers or verdicts.

Accent: Native Vietnamese, standard Northern accent with slight Hanoi warmth. Clear enunciation for financial terms.

#### TRANSCRIPT""",
    },
    "ban-tin-vnindex": {
        "label": "Bản Tin VNINDEX — MC Truyền Hình",
        "voice": "Charon",
        "prompt": """# AUDIO PROFILE: Bảo Minh
## "The Market Anchor"

Bảo Minh is a professional Vietnamese financial news anchor delivering the daily/weekly VNINDEX market report. His tone is informative, measured, and trustworthy — like a seasoned TV anchor who respects the audience's intelligence.

## THE SCENE: Broadcast Studio
A sleek, modern financial news studio with multiple screens showing live market data. The red ON AIR light is on. Bảo Minh delivers the report with the precision of a trained broadcaster.

### DIRECTOR'S NOTES

Style:
* Professional broadcast quality — clear, authoritative, informative.
* Emphasize key numbers and index levels with deliberate precision.
* Shift between analytical segments (data delivery) and strategic segments (advice) with clear tonal transitions.
* Maintain gravitas throughout — this is serious financial reporting, not entertainment.

Pacing:
* Steady, measured broadcast pace — neither too fast nor too slow.
* Slight acceleration during data-heavy segments to maintain energy.
* Deliberate slowdown for strategic advice and risk warnings.
* Clean pauses between major sections.

Accent: Standard Vietnamese broadcast accent, clear and professional.

#### TRANSCRIPT""",
    },
    "giai-ma-tin-tuc": {
        "label": "Giải Mã Tin Tức — Storyteller Phân Tích",
        "voice": "Sulafat",
        "prompt": """# AUDIO PROFILE: Minh Khôi
## "The News Decoder"

Minh Khôi breaks down complex financial news into digestible stories. He's the friend who reads all the boring reports so you don't have to, then tells you what actually matters in plain Vietnamese.

## THE SCENE: Late Night Analysis
Minh Khôi sits at his desk surrounded by news printouts and financial reports. He's figured out the real story behind the headlines and can't wait to share it.

### DIRECTOR'S NOTES

Style:
* Curious and investigative — like uncovering a mystery together with the listener.
* Build narrative tension when revealing hidden connections between news events.
* Warm and reassuring when the news is positive, serious and protective when warning about risks.
* Use a conspiratorial whisper effect when sharing "insider perspective" moments.

Pacing:
* Energetic but controlled — faster when building excitement, slower for revelations.
* Dramatic pauses before key insights.
* Natural conversational rhythm throughout.

Accent: Native Vietnamese, Northern standard with conversational warmth.

#### TRANSCRIPT""",
    },
    "simple": {
        "label": "Đơn giản — Prefix style",
        "voice": "",
        "prompt": "",
    },
}


class QuotaExhaustedError(RuntimeError):
    """Raised when Gemini API returns HTTP 429 (quota/rate limit)."""
    pass


class ContentFilterError(RuntimeError):
    """Raised when Gemini refuses to generate audio (finishReason=OTHER/SAFETY)."""
    pass


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def gemini_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load Gemini config from config/tts.json."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "tts.json"
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return data.get("gemini", {}) if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def gemini_api_key(explicit: str | None = None, config: dict | None = None) -> str:
    """Resolve the API key: explicit arg > env var > config file."""
    key = (explicit or "").strip()
    if key:
        return key
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    if config:
        key = str(config.get("api_key") or "").strip()
    if not key:
        raise ValueError(
            "Missing Gemini API key. Set GEMINI_API_KEY env var or add to config/tts.json."
        )
    return key


def gemini_public_config() -> dict:
    """Return safe-to-expose config (no API key)."""
    config = gemini_config()
    return {
        "model": config.get("model") or DEFAULT_MODEL,
        "voice": config.get("voice") or config.get("voice_name") or DEFAULT_VOICE,
        "style_prompt": config.get("style_prompt") or "",
        "style_preset": config.get("style_preset") or "",
        "voices": VOICES,
        "models": MODELS,
        "style_presets": {k: {"label": v["label"], "voice": v["voice"]} for k, v in STYLE_PRESETS.items()},
        "has_api_key": bool(
            os.environ.get("GEMINI_API_KEY", "").strip()
            or str(config.get("api_key") or "").strip()
        ),
    }


def update_gemini_config(updates: dict) -> dict:
    """Update gemini config fields in config/tts.json."""
    config_path = Path(__file__).resolve().parent.parent / "config" / "tts.json"
    data: dict = {}
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

    gemini = data.setdefault("gemini", {})
    allowed_fields = {"api_key", "model", "voice", "style_prompt", "style_preset", "cooldown"}
    for k, v in updates.items():
        if k in allowed_fields:
            gemini[k] = v

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return gemini_public_config()


# ---------------------------------------------------------------------------
# Core API call
# ---------------------------------------------------------------------------
def _build_tts_prompt(text: str, style_prompt: str = "", style_preset: str = "") -> str:
    """Build the full TTS prompt from style instructions + transcript text.

    If style_preset is set and exists in STYLE_PRESETS, use the advanced prompt
    format (Audio Profile + Scene + Director's Notes + Transcript).
    If style_prompt is a multi-line string containing '#### TRANSCRIPT' or
    '### DIRECTOR', treat it as an advanced prompt — append transcript.
    Otherwise, use simple prefix format: "style: text".
    """
    # 1. Try preset first
    preset = STYLE_PRESETS.get(style_preset, {}) if style_preset else {}
    advanced_prompt = preset.get("prompt", "").strip()

    # 2. If no preset, check if style_prompt itself is advanced format
    if not advanced_prompt and style_prompt.strip():
        if "TRANSCRIPT" in style_prompt or "DIRECTOR" in style_prompt or "AUDIO PROFILE" in style_prompt:
            advanced_prompt = style_prompt.strip()
        else:
            # Simple prefix mode (backward compatible)
            return f"{style_prompt.strip()}: {text}" if style_prompt.strip() else text

    # 3. Advanced mode — append transcript after the prompt
    if advanced_prompt:
        # Ensure prompt ends with TRANSCRIPT header
        if not advanced_prompt.rstrip().endswith("TRANSCRIPT"):
            if "TRANSCRIPT" not in advanced_prompt:
                advanced_prompt += "\n\n#### TRANSCRIPT"
        return f"{advanced_prompt}\n{text}"

    return text


async def _call_gemini_tts(
    text: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    style_prompt: str = "",
    style_preset: str = "",
) -> bytes:
    """Call Gemini TTS REST API and return raw PCM audio bytes."""
    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # Build prompt using advanced format if available
    tts_text = _build_tts_prompt(text, style_prompt, style_preset)

    # Override voice from preset if not explicitly set
    effective_voice = voice
    if style_preset and style_preset in STYLE_PRESETS:
        preset_voice = STYLE_PRESETS[style_preset].get("voice", "")
        if preset_voice and voice == DEFAULT_VOICE:
            effective_voice = preset_voice

    payload = {
        "contents": [{"parts": [{"text": tts_text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": effective_voice}
                }
            },
        },
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    loop = asyncio.get_event_loop()
    response_data = await loop.run_in_executor(None, lambda: _do_request(req))
    result = json.loads(response_data)

    # Check for safety/content filter blocks
    candidates = result.get("candidates", [])
    if candidates:
        finish_reason = candidates[0].get("finishReason", "")
        if finish_reason in ("OTHER", "SAFETY", "RECITATION"):
            raise ContentFilterError(
                f"Gemini TTS blocked (finishReason={finish_reason}). "
                f"Text may have triggered content safety filter."
            )

    # Extract base64 audio
    try:
        audio_b64 = result["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    except (KeyError, IndexError) as exc:
        error_msg = result.get("error", {}).get("message", str(result)[:300])
        raise RuntimeError(f"Gemini TTS error: {error_msg}") from exc

    return base64.b64decode(audio_b64)


def _do_request(req) -> bytes:
    import urllib.request
    import urllib.error

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore")[:500]
        if exc.code == 429:
            raise QuotaExhaustedError(f"Gemini API HTTP 429: {body}") from exc
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {body}") from exc


def _pcm_to_wav(pcm_data: bytes, wav_path: Path) -> None:
    """Write raw PCM (24kHz, 16-bit, mono) to a WAV file."""
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def _wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    """Convert WAV to MP3 using ffmpeg."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mp3_path),
        ],
        check=True,
        capture_output=True,
    )
    wav_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Per-line generation with retry
# ---------------------------------------------------------------------------
def _detect_lang(text):
    # Tieng Viet neu co ky tu dau rieng cua VN, con lai coi la English
    return "vi" if _VI_RE.search(text or "") else "en"


def _resolve_clone_voice_id(voice, text, config):
    v = (voice or "").strip()
    lang = _detect_lang(text)
    if v.startswith("voice_"):
        return v, lang
    vid = config.get("clone_voice_vi") if lang == "vi" else config.get("clone_voice_en")
    if not vid:
        vid = config.get("clone_voice_vi") or config.get("clone_voice_en")
    return (vid or ""), lang


def _extract_interactions_audio(result):
    found = []
    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "audio":
                d = o.get("data") or (o.get("audio") or {}).get("data")
                if isinstance(d, str) and len(d) > 100:
                    found.append(d)
            inl = o.get("inlineData")
            if isinstance(inl, dict) and isinstance(inl.get("data"), str) and len(inl["data"]) > 100:
                found.append(inl["data"])
            for vv in o.values():
                walk(vv)
        elif isinstance(o, list):
            for vv in o:
                walk(vv)
    walk(result)
    return found[-1] if found else None


def _to_pcm24(data):
    # Chuyen audio tu interactions ve PCM 24k mono 16-bit (dung chung contract pipeline)
    if data[:4] == b"RIFF":
        try:
            p = subprocess.run(
                ["ffmpeg", "-y", "-i", "pipe:0", "-f", "s16le", "-acodec", "pcm_s16le",
                 "-ar", "24000", "-ac", "1", "pipe:1"],
                input=data, capture_output=True,
            )
            if p.returncode == 0 and p.stdout:
                return p.stdout
        except Exception:
            pass
        return data[44:]
    return data


async def _call_gemini_tts_cloned(text, api_key, model, voice_id, style=""):
    import urllib.request
    content_text = {"type": "text", "text": text}
    if style:
        content_text["annotations"] = [{"type": "speech_metadata", "style": style}]
    payload = {
        "model": model,
        "input": [{"type": "user_input", "content": [content_text]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice_id}]},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CLONE_INTERACTIONS_URL, data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    loop = asyncio.get_event_loop()
    response_data = await loop.run_in_executor(None, lambda: _do_request(req))
    result = json.loads(response_data)
    b64 = _extract_interactions_audio(result)
    if not b64:
        err = (result.get("error") or {}).get("message", str(result)[:300])
        raise RuntimeError("Gemini clone TTS: khong co audio tra ve: " + str(err))
    return _to_pcm24(base64.b64decode(b64))


async def _call_gemini_tts_with_fallback(
    text: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    style_prompt: str = "",
    style_preset: str = "",
) -> tuple[bytes, str]:
    """Call Gemini TTS with auto-fallback on 429. Returns (pcm_bytes, used_model)."""
    # --- Cloned (replicated) voice path: interactions API + Gemini 3.8 ---
    if voice == AUTO_CLONE_VOICE or (voice or "").startswith("voice_"):
        _cfg = gemini_config()
        _vid, _lang = _resolve_clone_voice_id(voice, text, _cfg)
        if not _vid:
            raise RuntimeError("Chua co voice clone trong config (clone_voice_vi/clone_voice_en). Chay clone_voices.py truoc.")
        _sp = (style_prompt or "").strip()
        if _sp and "TRANSCRIPT" not in _sp and "DIRECTOR" not in _sp and "AUDIO PROFILE" not in _sp and len(_sp) <= 160:
            _style = _sp
        else:
            _style = CLONE_DEFAULT_STYLE.get(_lang, "")
        _cm = ([model] + [m for m in CLONE_MODELS if m != model]) if model in CLONE_MODELS else list(CLONE_MODELS)
        _last = None
        for _m in _cm:
            try:
                _pcm = await _call_gemini_tts_cloned(text, api_key, _m, _vid, _style)
                return _pcm, _m
            except QuotaExhaustedError as exc:
                print("  [!] Clone model " + _m + " het quota (429), thu model tiep...")
                _last = exc
                continue
        raise RuntimeError("Clone TTS: het quota o ca 3.8 Flash va Flash-Lite.") from _last
    # Build fallback order: requested model first, then others
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]

    last_error = None
    for m in models_to_try:
        try:
            pcm = await _call_gemini_tts(text, api_key, m, voice, style_prompt, style_preset)
            if m != model:
                print(f"  ✓ Auto-fallback thành công: {m}")
            return pcm, m
        except QuotaExhaustedError as exc:
            print(f"  ⚠ Model {m} hết quota (429), thử model tiếp theo...")
            last_error = exc
            continue
        except ContentFilterError as exc:
            print(f"  ⚠ Model {m} bị content filter (finishReason=OTHER), thử model tiếp theo...")
            last_error = exc
            continue

    if isinstance(last_error, ContentFilterError):
        raise RuntimeError(
            f"Tất cả {len(models_to_try)} models đều bị content filter chặn. "
            f"Thử rút gọn/sửa text hoặc dùng ElevenLabs. Text: {text[:100]}..."
        ) from last_error
    raise RuntimeError(
        f"Tất cả {len(models_to_try)} models đều hết quota (429). "
        f"Vui lòng chờ quota reset hoặc dùng ElevenLabs."
    ) from last_error


async def generate_line_audio(
    text: str,
    audio_file: Path,
    api_key: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    style_prompt: str = "",
    style_preset: str = "",
) -> None:
    """Generate a single line of TTS audio → MP3 with auto-fallback."""
    pcm, _used_model = await _call_gemini_tts_with_fallback(text, api_key, model, voice, style_prompt, style_preset)
    wav_path = audio_file.with_suffix(".pcm.wav")
    _pcm_to_wav(pcm, wav_path)
    _wav_to_mp3(wav_path, audio_file)


async def generate_line_audio_with_retry(
    text: str,
    audio_file: Path,
    api_key: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    style_prompt: str = "",
    style_preset: str = "",
) -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await generate_line_audio(text, audio_file, api_key, model, voice, style_prompt, style_preset)
            return
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"  ⚠ Gemini TTS attempt {attempt} failed ({exc.__class__.__name__}: {exc}), retrying in {wait:.0f}s...")
            await asyncio.sleep(wait)


# ---------------------------------------------------------------------------
# Full voiceover (one request for entire script)
# ---------------------------------------------------------------------------
async def generate_gemini_full_audio(
    slide_dir: Path,
    output_dir: Path,
    lines: list[str],
    *,
    api_key: str | None = None,
    model: str | None = None,
    voice: str | None = None,
    style_prompt: str | None = None,
    style_preset: str | None = None,
    config_path: Path | None = None,
    full_text: str | None = None,
    force: bool = False,
) -> Path:
    """Generate full voiceover as a single Gemini TTS request."""
    config = gemini_config(config_path)
    resolved_key = gemini_api_key(api_key, config)
    resolved_model = model or config.get("model") or DEFAULT_MODEL
    resolved_voice = voice or config.get("voice") or config.get("voice_name") or DEFAULT_VOICE
    resolved_style = style_prompt if style_prompt is not None else (config.get("style_prompt") or "")
    resolved_preset = style_preset if style_preset is not None else (config.get("style_preset") or "")

    text = full_text if full_text is not None else "\n".join(lines)
    if not text.strip():
        raise ValueError("No script text to send to Gemini TTS.")

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_file = output_dir / "gemini_full_voiceover.mp3"
    meta_file = output_dir / "gemini_full_voiceover.meta.json"

    metadata = {
        "engine": "gemini",
        "mode": "full_voiceover",
        "text": text,
        "lines": lines,
        "model": resolved_model,
        "voice": resolved_voice,
        "style_prompt": resolved_style,
        "style_preset": resolved_preset,
    }

    cache_matches = False
    if meta_file.exists():
        try:
            cache_matches = json.loads(meta_file.read_text(encoding="utf-8")) == metadata
        except json.JSONDecodeError:
            cache_matches = False
    if not force and cache_matches and audio_file.exists() and audio_file.stat().st_size > 0:
        print(f"Full Gemini TTS: {audio_file} (cached)")
        return audio_file

    if audio_file.exists():
        audio_file.unlink()

    # Log preset info
    if resolved_preset and resolved_preset in STYLE_PRESETS:
        preset_info = STYLE_PRESETS[resolved_preset]
        print(f"Style Preset: {resolved_preset} ({preset_info['label']})")
        print(f"Voice: Gemini {resolved_model} / {preset_info.get('voice', resolved_voice)}")
    else:
        print(f"Voice: Gemini {resolved_model} / {resolved_voice}")
        if resolved_style:
            print(f"Style: {resolved_style[:80]}...")
    print(f"Sending full script to Gemini TTS: {len(lines)} slides, {len(text)} chars")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            pcm, used_model = await _call_gemini_tts_with_fallback(
                text, resolved_key, resolved_model, resolved_voice, resolved_style, resolved_preset
            )
            wav_path = audio_file.with_suffix(".pcm.wav")
            _pcm_to_wav(pcm, wav_path)
            _wav_to_mp3(wav_path, audio_file)
            if used_model != resolved_model:
                metadata["model"] = used_model
            break
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"  ⚠ Full Gemini TTS attempt {attempt} failed ({exc}), retrying in {wait:.0f}s...")
            await asyncio.sleep(wait)

    meta_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Full Gemini TTS saved: {audio_file}")
    return audio_file


# ---------------------------------------------------------------------------
# Per-slide generation (uses generate_project_tts harness)
# ---------------------------------------------------------------------------
async def generate_gemini_tts(
    slide_dir: Path,
    output_dir: Path,
    lines: list[str],
    *,
    api_key: str | None = None,
    model: str | None = None,
    voice: str | None = None,
    style_prompt: str | None = None,
    style_preset: str | None = None,
    config_path: Path | None = None,
    force: bool = False,
) -> None:
    """Generate per-slide TTS using the common harness."""
    config = gemini_config(config_path)
    resolved_key = gemini_api_key(api_key, config)
    resolved_model = model or config.get("model") or DEFAULT_MODEL
    resolved_voice = voice or config.get("voice") or config.get("voice_name") or DEFAULT_VOICE
    resolved_style = style_prompt if style_prompt is not None else (config.get("style_prompt") or "")
    resolved_preset = style_preset if style_preset is not None else (config.get("style_preset") or "")
    cooldown = float(config.get("cooldown") or DEFAULT_COOLDOWN)

    if resolved_preset and resolved_preset in STYLE_PRESETS:
        preset_info = STYLE_PRESETS[resolved_preset]
        print(f"Style Preset: {resolved_preset} ({preset_info['label']})")
        print(f"Voice: Gemini {resolved_model} / {preset_info.get('voice', resolved_voice)}")
    else:
        print(f"Voice: Gemini {resolved_model} / {resolved_voice}")
        if resolved_style:
            print(f"Style: {resolved_style[:80]}...")

    def cache_meta(index: int, text: str) -> dict[str, Any]:
        return {
            "engine": "gemini",
            "model": resolved_model,
            "voice": resolved_voice,
            "style_prompt": resolved_style,
            "style_preset": resolved_preset,
        }

    async def line_generator(
        index: int, text: str, audio_file: Path, subtitle_file: Path
    ) -> None:
        await generate_line_audio_with_retry(
            text, audio_file, resolved_key, resolved_model, resolved_voice, resolved_style, resolved_preset
        )

    await generate_project_tts(
        slide_dir,
        output_dir,
        lines,
        line_generator,
        force=force,
        cooldown=cooldown,
        cache_metadata=cache_meta,
    )
