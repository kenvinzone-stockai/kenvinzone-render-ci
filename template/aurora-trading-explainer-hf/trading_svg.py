# -*- coding: utf-8 -*-
"""KenvinZone — trading_svg.py  (Module 1: aurora-trading-canvas-engine)

Bộ "từ vựng đồ họa" SVG cho dòng template "aurora-trading-explainer-hf".
Chuẩn theo RESEARCH_TRADING_EXPLAINER_MASTER.md của ANTI: 8 hàm render + hệ
tọa độ giá dùng chung (price_to_y), phủ đủ 6 dạng bài Explainer:

  1. Liquidity Sweeps / Stop Hunt .... hàm 1,5,7,3,8
  2. SMC (Order Block, FVG, BOS) ..... hàm 1,5,7,3
  3. Sóng Elliott & Fibonacci ........ hàm 1,6,5(fib)
  4. Trendline & Khối lượng .......... hàm 1,6,3,8
  5. RSI mốc 50 / EMA Cloud .......... hàm 1,4,5(ribbon)
  6. Split-Screen Quiz ............... 2 container A/B chứa hàm 1-8 thu nhỏ

Mọi hàm trả về string SVG `<g class="...">` có class/id ổn định để GSAP
reveal từng lớp (draw-in nến, mọc thanh VP, nhấp nháy spike...).

Lưu ý CI: render_hyperframes copy NGUYÊN thư mục template rồi chạy build.py
với cwd=work, nên file này phải nằm TRONG thư mục template
(bản ở template/common/ là bản gốc dùng chung — build CI copy sang).

Design tokens:
    nến tăng #10b981 · nến giảm #f43f5e · VP thân #8b5cf6 · POC #f59e0b
    RSI curve #a78bfa · midline #eab308 · level line mặc định #3b82f6
"""

# ---------------------------------------------------------------- tokens ---
UP = "#10b981"        # emerald — nến tăng / battery_full / TP
DOWN = "#f43f5e"      # rose    — nến giảm / SL / trapped
VP = "#8b5cf6"        # violet  — thân volume profile
POC = "#f59e0b"       # amber   — POC phình to / spike / hộp dashed
BOX = "#f59e0b"       # alias cũ — khung sideway
RSI_LINE = "#a78bfa"  # tím pastel — đường cong RSI
MIDLINE = "#eab308"   # vàng — mốc 50 / trendline mặc định
LEVEL = "#3b82f6"     # xanh dương — đường thanh khoản
INK = "#0b1220"       # chữ tối trên nền pill sáng

# Hệ tọa độ mặc định (canvas 1080x1920 dọc — chart chính y 280..1080)
DEFAULT_COORD = {
    "price_min": 80.0,
    "price_max": 200.0,
    "chart_height_px": 800,
    "chart_top_y": 280,
    "chart_left_x": 100,
    "chart_width_px": 880,
}


def price_to_y(price, coord):
    """Trục giá dùng chung: giá -> pixel y (giá cao = y nhỏ). Chuẩn ANTI."""
    span = coord["price_max"] - coord["price_min"]
    norm = (price - coord["price_min"]) / (span or 1.0)
    return round(coord["chart_top_y"] + coord["chart_height_px"] * (1.0 - norm), 2)


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ------------------------------------------------------------- HÀM 1 -------
def render_candlesticks(candles, coord, highlight_idx=None):
    """Chuỗi nến Nhật. candles: [{"o","h","l","c","x","width","id"}, ...].

    highlight_idx (int | list): nến được viền sáng dashed amber (nến nhấn
    chìm / rút chân / quét râu). Class GSAP: .candle-item / .candle-body /
    .candle-wick / .candle-glow (vòng highlight).
    """
    if highlight_idx is None:
        hi = set()
    elif isinstance(highlight_idx, (list, tuple, set)):
        hi = set(highlight_idx)
    else:
        hi = {highlight_idx}
    out = ['<g class="candlestick-layer">']
    for i, c in enumerate(candles):
        o, h, l, cl = c["o"], c["h"], c["l"], c["c"]
        x = float(c.get("x", coord["chart_left_x"] + 20 + i * 56))
        w = float(c.get("width", 16))
        cid = c.get("id", "c_%d" % i)
        cx = x + w / 2.0
        yo, yc = price_to_y(o, coord), price_to_y(cl, coord)
        yh, yl = price_to_y(h, coord), price_to_y(l, coord)
        bull = cl >= o
        col = UP if bull else DOWN
        top = min(yo, yc)
        bh = max(abs(yc - yo), 2.0)
        extra = " candle-highlight" if i in hi else ""
        out.append(
            f'<g class="candle-item{extra}" id="{cid}" data-i="{i}" data-dir="{"up" if bull else "down"}">'
            f'<line class="candle-wick" x1="{cx:.2f}" y1="{yh:.2f}" x2="{cx:.2f}" y2="{yl:.2f}"'
            f' stroke="{col}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<rect class="candle-body" x="{x:.2f}" y="{top:.2f}" width="{w:.2f}" height="{bh:.2f}"'
            f' fill="{col}" rx="2.5"/>'
        )
        if i in hi:
            out.append(
                f'<rect class="candle-glow" x="{x-7:.2f}" y="{yh-7:.2f}" width="{w+14:.2f}"'
                f' height="{(yl-yh)+14:.2f}" fill="none" stroke="{POC}" stroke-width="2.6"'
                f' stroke-dasharray="5 4" rx="7" opacity="0.95"/>'
            )
        out.append('</g>')
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 2 -------
def render_volume_profile(bins, coord, poc_price, x_start=100, max_w=140):
    """Volume Profile NGANG, đồng bộ TRỤC GIÁ (y = price_to_y(bin.price)).

    bins: [{"price": 115.0, "volume": 95}, ...]. Bin gần poc_price nhất tô
    amber (bụng phình, data-poc="1"). transformOrigin trái để GSAP scaleX.
    """
    out = ['<g class="volume-profile-layer">']
    if bins:
        maxv = max(b["volume"] for b in bins) or 1
        prices = [b["price"] for b in bins]
        if len(prices) > 1:
            gaps = [abs(price_to_y(prices[k + 1], coord) - price_to_y(prices[k], coord))
                    for k in range(len(prices) - 1)]
            bar_h = max(min(gaps), 6.0) * 0.82
        else:
            bar_h = 24.0
        poc_i = min(range(len(bins)), key=lambda k: abs(bins[k]["price"] - poc_price))
        for i, b in enumerate(bins):
            yy = price_to_y(b["price"], coord)
            w = (b["volume"] / maxv) * max_w
            is_poc = (i == poc_i)
            col = POC if is_poc else VP
            out.append(
                f'<rect class="vp-bar{" vp-poc" if is_poc else ""}" id="vp{i}" data-poc="{1 if is_poc else 0}"'
                f' x="{x_start:.2f}" y="{yy - bar_h/2:.2f}" width="{w:.2f}" height="{bar_h:.2f}"'
                f' fill="{col}" rx="2.5" opacity="{0.97 if is_poc else 0.82}"'
                f' style="transform-origin:{x_start:.0f}px {yy:.0f}px"/>'
            )
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 3 -------
def render_bottom_volume_bars(volumes, x_coords, y_bottom=1100, max_h=120):
    """Cột Volume Histogram dưới đáy chart, thẳng trục X với từng nến.

    volumes: [{"vol": 500, "is_spike": False, "color": "#10b981"}, ...]
    x_coords: tâm X của từng nến. Spike: class .vol-spike + viền cam.
    """
    out = ['<g class="bottom-volume-layer">']
    if volumes:
        maxv = max(v["vol"] for v in volumes) or 1
        if len(x_coords) > 1:
            bw = abs(x_coords[1] - x_coords[0]) * 0.58
        else:
            bw = 22.0
        for i, v in enumerate(volumes):
            x = x_coords[i] if i < len(x_coords) else x_coords[-1] + (i - len(x_coords) + 1) * 30
            h = max((v["vol"] / maxv) * max_h, 3.0)
            col = v.get("color", UP)
            spike = bool(v.get("is_spike", False))
            stroke = f' stroke="{POC}" stroke-width="2.4"' if spike else ""
            out.append(
                f'<rect class="vol-bar{" vol-spike" if spike else ""}" id="vol{i}" data-spike="{1 if spike else 0}"'
                f' x="{x - bw/2:.2f}" y="{y_bottom - h:.2f}" width="{bw:.2f}" height="{h:.2f}"'
                f' fill="{col}" rx="2" opacity="{0.95 if spike else 0.66}"{stroke}'
                f' style="transform-origin:{x:.0f}px {y_bottom:.0f}px"/>'
            )
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 4 -------
def render_subpanel_rsi(rsi_points, coord_sub, midline=50):
    """Sub-panel RSI (Dạng 5). rsi_points: [{"x":100,"rsi":55},...].

    coord_sub: {"top_y","height","left_x","width"}. Mốc midline nét đứt vàng
    + nhãn "MỐC 50"; đường cong RSI tím pastel (.rsi-curve, GSAP draw-in
    bằng stroke-dashoffset).
    """
    ty, hh = float(coord_sub["top_y"]), float(coord_sub["height"])
    lx, ww = float(coord_sub["left_x"]), float(coord_sub["width"])

    def ry(v):
        return ty + hh * (1.0 - float(v) / 100.0)

    my = ry(midline)
    out = ['<g class="subpanel-rsi">']
    out.append(
        f'<rect class="rsi-frame" x="{lx:.1f}" y="{ty:.1f}" width="{ww:.1f}" height="{hh:.1f}"'
        f' fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.08)" rx="10"/>'
    )
    out.append(
        f'<line class="rsi-midline" x1="{lx:.1f}" y1="{my:.1f}" x2="{lx+ww:.1f}" y2="{my:.1f}"'
        f' stroke="{MIDLINE}" stroke-width="2" stroke-dasharray="4 4"/>'
    )
    out.append(
        f'<text class="rsi-midlabel" x="{lx+14:.1f}" y="{my-10:.1f}" fill="{MIDLINE}"'
        f' font-size="22" font-weight="800" font-family="Consolas,monospace">MỐC {midline:g}</text>'
    )
    if rsi_points:
        pts = " ".join(f'{p["x"]:.1f},{ry(p["rsi"]):.1f}' for p in rsi_points)
        out.append(
            f'<polyline class="rsi-curve" points="{pts}" fill="none" stroke="{RSI_LINE}"'
            f' stroke-width="3.4" stroke-linejoin="round" stroke-linecap="round"/>'
        )
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 5 -------
_BOX_SEQ = [0]


def render_price_box(top_price, bottom_price, start_x, end_x, coord,
                     style="dashed", fill_color=None, label=""):
    """Hộp giá đa năng: Sideway/OB ("dashed") · FVG ("fvg") · EMA Ribbon
    ("ribbon") · Fib sọc chéo ("fib"). Phủ ĐÚNG dải giá [bottom, top]."""
    _BOX_SEQ[0] += 1
    uid = f"pbx{_BOX_SEQ[0]}"
    y1 = price_to_y(top_price, coord)
    y2 = price_to_y(bottom_price, coord)
    x, w, h = float(start_x), float(end_x) - float(start_x), (y2 - y1)
    out = [f'<g class="price-box" data-style="{style}" id="{uid}">']
    if style == "fvg":
        col = fill_color or VP
        out.append(
            f'<rect x="{x:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{col}"'
            f' opacity="0.20" stroke="{col}" stroke-width="1.6" stroke-dasharray="2 3" rx="4"/>'
        )
        lab_col = col
    elif style == "ribbon":
        col = fill_color or "#38bdf8"
        out.append(
            f'<defs><linearGradient id="{uid}g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{col}" stop-opacity="0.38"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0.07"/></linearGradient></defs>'
            f'<rect x="{x:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}"'
            f' fill="url(#{uid}g)" rx="12"/>'
        )
        lab_col = col
    elif style == "fib":
        col = fill_color or POC
        out.append(
            f'<defs><pattern id="{uid}p" width="14" height="14" patternUnits="userSpaceOnUse"'
            f' patternTransform="rotate(45)">'
            f'<rect width="14" height="14" fill="{col}" opacity="0.07"/>'
            f'<line x1="0" y1="0" x2="0" y2="14" stroke="{col}" stroke-width="3" opacity="0.5"/>'
            f'</pattern></defs>'
            f'<rect x="{x:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#{uid}p)"'
            f' stroke="{col}" stroke-width="1.6" rx="4"/>'
        )
        lab_col = col
    else:  # "dashed" — Sideway box / Order Block
        col = fill_color or POC
        out.append(
            f'<rect x="{x:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{col}"'
            f' fill-opacity="0.08" stroke="{col}" stroke-width="2.2" stroke-dasharray="6 4" rx="6"/>'
        )
        lab_col = col
    if label:
        out.append(
            f'<text class="box-label" x="{x+10:.1f}" y="{y1-10:.1f}" fill="{lab_col}"'
            f' font-size="23" font-weight="800" font-family="Consolas,monospace">{_esc(label)}</text>'
        )
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 6 -------
def render_polyline(points, coord, mode="trendline", markers=None, stroke_color="#eab308"):
    """Trendline chéo hoặc zig-zag Elliott. points: [{"x","price"},...].

    mode "trendline": nét đứt dài; "elliott": gấp khúc nét liền + chấm đỉnh
    đáy. markers: nhãn tròn tại từng điểm (["1","2","3","4","5"] / A-B-C).
    Class GSAP: .pl-line (draw-in bằng dashoffset), .pl-marker.
    """
    out = [f'<g class="polyline-layer" data-mode="{mode}">']
    if points:
        xy = [(float(p["x"]), price_to_y(p["price"], coord)) for p in points]
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
        dash = ' stroke-dasharray="10 6"' if mode == "trendline" else ""
        out.append(
            f'<polyline class="pl-line" points="{pts}" fill="none" stroke="{stroke_color}"'
            f' stroke-width="3.4" stroke-linejoin="round" stroke-linecap="round"{dash}/>'
        )
        if mode == "elliott":
            for x, y in xy:
                out.append(f'<circle class="pl-dot" cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{stroke_color}"/>')
        if markers:
            for i, (x, y) in enumerate(xy):
                if i < len(markers) and markers[i]:
                    dy = -30 if (i % 2 == 0) else 34
                    out.append(
                        f'<g class="pl-marker"><circle cx="{x:.1f}" cy="{y+dy:.1f}" r="16" fill="{stroke_color}"/>'
                        f'<text x="{x:.1f}" y="{y+dy+7:.1f}" fill="{INK}" font-size="20" font-weight="900"'
                        f' text-anchor="middle" font-family="Arial">{_esc(markers[i])}</text></g>'
                    )
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 7 -------
def render_level_line(price, coord, label="THANH KHOẢN TRÊN", line_style="dashed", color="#3b82f6"):
    """Đường mốc ngang: Liquidity / BOS / CHoCH / SL / TP.

    Nhãn pill bo tròn neo mép phải. Class GSAP: .ll-stroke (draw-in), .ll-label.
    """
    y = price_to_y(price, coord)
    x0 = coord["chart_left_x"]
    x1 = coord["chart_left_x"] + coord["chart_width_px"]
    dash = ' stroke-dasharray="10 6"' if line_style == "dashed" else ""
    out = ['<g class="level-line">']
    out.append(
        f'<line class="ll-stroke" x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}"'
        f' stroke="{color}" stroke-width="2.6"{dash}/>'
    )
    if label:
        w = 26 + len(str(label)) * 12.5
        out.append(
            f'<g class="ll-label"><rect x="{x1-w:.1f}" y="{y-16:.1f}" width="{w:.1f}" height="32"'
            f' rx="16" fill="{color}"/>'
            f'<text x="{x1-w/2:.1f}" y="{y+7:.1f}" fill="{INK}" font-size="19" font-weight="800"'
            f' text-anchor="middle" font-family="Arial">{_esc(label)}</text></g>'
        )
    out.append('</g>')
    return "\n".join(out)


# ------------------------------------------------------------- HÀM 8 -------
def render_icon_avatar(icon_type, x, y, label=None, scale=1.0):
    """Icon chibi kể chuyện. icon_type: buyer_green · trapped_red ·
    bank_vault · market_cart · battery_low · battery_full · face_guess ·
    face_smile. Gốc (0,0) ở tâm icon; label = pill phía trên."""

    def person(color, chest=""):
        return (f'<circle cx="0" cy="-20" r="15" fill="{color}"/>'
                f'<rect x="-14" y="-6" width="28" height="30" rx="8" fill="{color}"/>{chest}')

    if icon_type == "buyer_green":
        inner = person(UP)
    elif icon_type == "trapped_red":
        xm = ('<path d="M-9 2 L9 20 M9 2 L-9 20" stroke="#f43f5e" stroke-width="4.5"'
              ' stroke-linecap="round"/>')
        inner = person("#64748b", xm)
    elif icon_type == "bank_vault":
        cols = "".join(f'<rect x="{bx}" y="-4" width="7" height="26" fill="#94a3b8"/>'
                       for bx in (-26, -11, 4, 19))
        inner = (f'<polygon points="-38,-8 0,-32 38,-8" fill="#e2e8f0"/>'
                 f'<rect x="-32" y="-8" width="64" height="34" fill="#cbd5e1"/>{cols}'
                 f'<rect x="-32" y="24" width="64" height="6" fill="#e2e8f0"/>')
    elif icon_type == "market_cart":
        inner = ('<path d="M-28 -20 H-17 L-10 12 H20" stroke="#38bdf8" stroke-width="4.2"'
                 ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                 '<rect x="-13" y="-10" width="36" height="20" rx="3" fill="#38bdf8" opacity="0.85"/>'
                 '<circle cx="-5" cy="21" r="5.5" fill="#38bdf8"/>'
                 '<circle cx="15" cy="21" r="5.5" fill="#38bdf8"/>')
    elif icon_type == "battery_low":
        inner = ('<rect x="-28" y="-15" width="52" height="30" rx="5" fill="none"'
                 ' stroke="#cbd5e1" stroke-width="3"/>'
                 '<rect x="26" y="-7" width="6" height="14" rx="2" fill="#cbd5e1"/>'
                 f'<rect class="bat-fill" x="-24" y="-11" width="12" height="22" rx="2" fill="{DOWN}"/>')
    elif icon_type == "battery_full":
        inner = ('<rect x="-28" y="-15" width="52" height="30" rx="5" fill="none"'
                 ' stroke="#cbd5e1" stroke-width="3"/>'
                 '<rect x="26" y="-7" width="6" height="14" rx="2" fill="#cbd5e1"/>'
                 f'<rect class="bat-fill" x="-24" y="-11" width="44" height="22" rx="2" fill="{UP}"/>')
    elif icon_type == "face_guess":
        inner = ('<circle cx="0" cy="0" r="22" fill="#fde68a"/>'
                 '<circle cx="-8" cy="-5" r="3.2" fill="#1f2937"/>'
                 '<circle cx="8" cy="-5" r="3.2" fill="#1f2937"/>'
                 '<path d="M-8 11 Q0 6 8 13" stroke="#1f2937" stroke-width="2.6" fill="none"'
                 ' stroke-linecap="round"/>'
                 f'<text x="24" y="-18" fill="{MIDLINE}" font-size="30" font-weight="900"'
                 ' font-family="Arial">?</text>')
    elif icon_type == "face_smile":
        inner = ('<circle cx="0" cy="0" r="22" fill="#fde68a"/>'
                 '<circle cx="-8" cy="-5" r="3.2" fill="#1f2937"/>'
                 '<circle cx="8" cy="-5" r="3.2" fill="#1f2937"/>'
                 '<path d="M-10 7 Q0 18 10 7" stroke="#1f2937" stroke-width="2.8" fill="none"'
                 ' stroke-linecap="round"/>')
    else:
        inner = person("#64748b")

    pill = ""
    if label:
        w = 26 + len(str(label)) * 12
        pill = (f'<g class="avatar-pill"><rect x="{-w/2:.1f}" y="-74" width="{w:.1f}" height="31"'
                f' rx="15.5" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>'
                f'<text x="0" y="-52" fill="#e2e8f0" font-size="19" font-weight="800"'
                f' text-anchor="middle" font-family="Arial">{_esc(label)}</text></g>')
    return (f'<g class="avatar-icon" data-icon="{icon_type}"'
            f' transform="translate({float(x):.1f},{float(y):.1f}) scale({float(scale):.3f})">'
            f'{pill}{inner}</g>')


# ------------------------------------------------- tiện ích nền (bonus) ---
def grid(coord, step=6):
    """Lưới ngang mờ theo trục giá (nền chart) — dùng chung cho mọi dạng bài."""
    x0 = coord["chart_left_x"]
    x1 = coord["chart_left_x"] + coord["chart_width_px"]
    lines = []
    for k in range(step + 1):
        p = coord["price_min"] + (coord["price_max"] - coord["price_min"]) * k / step
        yy = price_to_y(p, coord)
        lines.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x1}" y2="{yy:.1f}"'
                     f' stroke="rgba(255,255,255,0.05)" stroke-width="1"/>')
    return "\n".join(lines)


# ----------------------------------------------------------- self-test ----
if __name__ == "__main__":
    import sys
    coord = dict(DEFAULT_COORD)
    # chuỗi nến: giảm -> sideway quét thanh khoản -> bùng nổ
    raw = [(190, 194, 176, 178), (178, 180, 150, 152), (152, 154, 120, 122),
           (122, 128, 108, 124), (124, 130, 112, 118), (118, 126, 104, 121),
           (121, 128, 96, 123), (123, 130, 112, 119), (119, 126, 112, 115),
           (115, 140, 110, 138), (138, 160, 132, 157), (157, 182, 150, 179)]
    candles = [{"o": o, "h": h, "l": l, "c": c, "x": 130 + i * 68, "width": 30,
                "id": f"c_{i}"} for i, (o, h, l, c) in enumerate(raw)]
    xs = [130 + i * 68 + 15 for i in range(len(raw))]
    vols = [{"vol": v, "is_spike": s, "color": (UP if u else DOWN)}
            for v, s, u in [(500, 0, 0), (900, 0, 0), (1400, 0, 0), (700, 0, 1),
                            (600, 0, 0), (800, 0, 1), (2600, 1, 1), (700, 0, 0),
                            (500, 0, 0), (1900, 1, 1), (1500, 0, 1), (2200, 1, 1)]]
    bins = [{"price": p, "volume": v} for p, v in
            [(100, 18), (108, 42), (116, 96), (124, 70), (132, 30), (140, 16), (150, 9)]]
    rsi = [{"x": 100 + k * 80, "rsi": r} for k, r in
           enumerate([62, 48, 35, 30, 38, 34, 42, 47, 45, 58, 66, 72])]
    svg = "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1560" viewBox="0 0 1080 1560"'
        ' style="background:#0e111a">',
        grid(coord),
        render_price_box(130, 104, 290, 760, coord, style="dashed", label="SIDEWAY GOM HÀNG"),
        render_price_box(168, 148, 620, 980, coord, style="fvg", label="FVG"),
        render_volume_profile(bins, coord, poc_price=116, x_start=100, max_w=150),
        render_level_line(96, coord, label="QUÉT THANH KHOẢN", color=LEVEL),
        render_level_line(179, coord, label="TP", line_style="solid", color=UP),
        render_polyline([{"x": 130, "price": 190}, {"x": 430, "price": 112},
                         {"x": 640, "price": 96}], coord, mode="trendline"),
        render_polyline([{"x": 540, "price": 115}, {"x": 700, "price": 140},
                         {"x": 790, "price": 128}, {"x": 880, "price": 160},
                         {"x": 1000, "price": 180}], coord, mode="elliott",
                        markers=["1", "2", "3", "4", "5"], stroke_color="#38bdf8"),
        render_candlesticks(candles, coord, highlight_idx=[6, 11]),
        render_bottom_volume_bars(vols, xs, y_bottom=1180, max_h=120),
        render_subpanel_rsi(rsi, {"top_y": 1220, "height": 190, "left_x": 100, "width": 880}),
        render_icon_avatar("buyer_green", 250, 540, label="MUA", scale=1.1),
        render_icon_avatar("trapped_red", 420, 560, label="MẮC KẸT"),
        render_icon_avatar("bank_vault", 640, 420, label="GOM ÂM THẦM"),
        render_icon_avatar("market_cart", 850, 460, label="THANH KHOẢN", scale=0.9),
        render_icon_avatar("battery_low", 250, 1500, label="PHE BÁN ĐUỐI"),
        render_icon_avatar("battery_full", 540, 1500, label="PHE MUA"),
        render_icon_avatar("face_guess", 790, 1495),
        render_icon_avatar("face_smile", 900, 1495),
        '</svg>'])
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", sys.argv[1], len(svg), "bytes")
    else:
        print(svg[:300], "...\n[OK trading_svg 8-ham demo]")


# ================== LỚP TƯƠNG THÍCH NGƯỢC (API v1 — build.py cũ) ==========
# Giữ cho template aurora-trading-explainer-hf hiện tại build được trong lúc
# Brain/ANTI chuyển hẳn sang 8 hàm chuẩn ở trên. KHÔNG dùng cho code mới.

def make_axis(min_val, max_val, top=120.0, height=620.0):
    """(v1) Trục giá kiểu cũ: trả dict có y_of closure."""
    span = (max_val - min_val) or 1.0

    def y_of(p):
        return top + (max_val - p) / span * height

    return {"y_of": y_of, "min": min_val, "max": max_val,
            "top": top, "height": height, "span": span}


def render_candles(candles, axis, x0=70.0, dx=58.0, width=30.0, idprefix="cd"):
    """(v1) Nến dạng list [o,h,l,c] theo axis cũ."""
    y = axis["y_of"]
    out = []
    for i, c in enumerate(candles):
        o, h, l, cl = (list(c) + [c[-1]] * 4)[:4]
        cx = x0 + i * dx + width / 2.0
        yo, yc, yh, yl = y(o), y(cl), y(h), y(l)
        bull = cl >= o
        col = UP if bull else DOWN
        top = min(yo, yc)
        hgt = max(abs(yc - yo), 2.0)
        out.append(
            f'<g class="candle" id="{idprefix}{i}" data-i="{i}">'
            f'<line x1="{cx:.1f}" y1="{yh:.1f}" x2="{cx:.1f}" y2="{yl:.1f}"'
            f' stroke="{col}" stroke-width="2.4"/>'
            f'<rect x="{x0 + i*dx:.1f}" y="{top:.1f}" width="{width:.1f}"'
            f' height="{hgt:.1f}" fill="{col}" rx="2.5"/></g>'
        )
    return "\n".join(out)


def sideway_box(axis, x, w, lo_price, hi_price, color=BOX, idn="swbox", label=None):
    """(v1) Khung sideway nét đứt theo axis cũ."""
    y = axis["y_of"]
    y1, y2 = y(hi_price), y(lo_price)
    svg = (f'<rect class="sideway-box" id="{idn}" x="{x:.1f}" y="{y1:.1f}"'
           f' width="{w:.1f}" height="{(y2-y1):.1f}" fill="{color}14"'
           f' stroke="{color}" stroke-width="2.2" stroke-dasharray="6 4" rx="6"/>')
    if label:
        svg += (f'<text class="sw-label" x="{x+10:.1f}" y="{y1-12:.1f}" fill="{color}"'
                f' font-size="26" font-weight="800" font-family="Consolas,monospace">{_esc(label)}</text>')
    return svg


def buyer_icon(x, y, state="buy", idn="buyer"):
    """(v1) Icon người mua cũ — tương đương render_icon_avatar buyer/trapped."""
    body = UP if state == "buy" else "#64748b"
    if state == "buy":
        pill = (f'<g class="pill-buy"><rect x="-34" y="-74" width="68" height="30" rx="15" fill="{UP}"/>'
                f'<text x="0" y="-53" fill="#06240f" font-size="20" font-weight="900"'
                f' text-anchor="middle" font-family="Arial">MUA</text></g>')
        x_mark = ""
    else:
        pill = ('<g class="pill-trap"><rect x="-60" y="-78" width="120" height="32" rx="16" fill="#f43f5e"/>'
                '<text x="0" y="-56" fill="#2a0810" font-size="19" font-weight="900"'
                ' text-anchor="middle" font-family="Arial">MẮC KẸT</text></g>')
        x_mark = ('<path d="M-13 -26 L13 0 M13 -26 L-13 0" stroke="#f43f5e" stroke-width="5"'
                  ' stroke-linecap="round"/>')
    return (f'<g class="buyer {state}" id="{idn}" transform="translate({x:.0f},{y:.0f})">'
            f'{pill}<circle cx="0" cy="-20" r="15" fill="{body}"/>'
            f'<rect x="-14" y="-6" width="28" height="30" rx="8" fill="{body}"/>{x_mark}</g>')


def _legacy_vp(bars, axis, lo_price, hi_price, x_left=70.0, max_w=150.0,
               poc_index=None, idprefix="vp"):
    """(v1) Volume Profile theo axis cũ (bars = list số)."""
    y = axis["y_of"]
    n = len(bars) or 1
    maxv = max(bars) or 1
    if poc_index is None:
        poc_index = list(bars).index(maxv)
    step = (hi_price - lo_price) / n
    band_px = abs(y(lo_price) - y(hi_price))
    bh = (band_px / n) * 0.82
    out = []
    for i, v in enumerate(bars):
        price = lo_price + (i + 0.5) * step
        yy = y(price)
        w = (v / maxv) * max_w
        is_poc = (i == poc_index)
        col = POC if is_poc else VP
        out.append(
            f'<rect class="vp-bar" id="{idprefix}{i}" data-poc="{1 if is_poc else 0}"'
            f' x="{x_left:.1f}" y="{yy-bh/2:.1f}" width="{w:.1f}" height="{bh:.1f}"'
            f' fill="{col}" rx="2.5" opacity="{0.96 if is_poc else 0.82}"/>'
        )
    return "\n".join(out)


# --- dispatcher: giữ TÊN render_volume_profile / grid dùng được cả 2 đời API
_render_volume_profile_v2 = render_volume_profile


def render_volume_profile(bins, coord, poc_price, *args, **kw):  # noqa: F811
    if isinstance(coord, dict) and "y_of" in coord:   # gọi kiểu v1
        return _legacy_vp(bins, coord, poc_price, *args, **kw)
    return _render_volume_profile_v2(bins, coord, poc_price, *args, **kw)


_grid_v2 = grid


def grid(coord, x0=None, x1=None, step=6):  # noqa: F811
    if isinstance(coord, dict) and "y_of" in coord:   # gọi kiểu v1: grid(axis, x0, x1)
        y = coord["y_of"]
        lines = []
        for k in range(step + 1):
            p = coord["min"] + (coord["max"] - coord["min"]) * k / step
            yy = y(p)
            lines.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x1}" y2="{yy:.1f}"'
                         f' stroke="rgba(255,255,255,0.05)" stroke-width="1"/>')
        return "\n".join(lines)
    return _grid_v2(coord, step=step)
