"""Đọc log của một lượt chạy lỗi → trả 1 dòng giải thích dễ hiểu để gửi kèm Telegram.

Dùng: python tools/ci/fail_reason.py brain.log ci-run.log   (in ra chuỗi rỗng nếu không nhận ra lỗi)
"""
import re
import sys
from pathlib import Path

RULES = [
    (r"spending cap|spend cap|ai\.studio/spend",
     "💳 Nguyên nhân: tài khoản Gemini đã chạm HẠN MỨC CHI TIÊU THÁNG. Vào https://ai.studio/spend nâng hạn mức, rồi chạy lại."),
    (r"API key not valid|API_KEY_INVALID|PERMISSION_DENIED",
     "🔑 Nguyên nhân: khoá Gemini (GEMINI_API_KEY) không hợp lệ hoặc bị thu hồi."),
    (r"Gemini HTTP 429|RESOURCE_EXHAUSTED|Too Many Requests",
     "⏳ Nguyên nhân: Gemini báo quá tải/hết lượt (429). Chờ ít phút rồi chạy lại."),
    (r"Gemini HTTP 5\d\d|Gemini timeout",
     "⏳ Nguyên nhân: máy chủ Gemini lỗi tạm thời. Chạy lại sau ít phút."),
    (r"YouTube token refresh failed: HTTP 4|invalid_grant",
     "🔑 Nguyên nhân: quyền đăng YouTube hết hạn/bị thu hồi — cần cấp lại refresh token."),
    (r"YouTube token refresh failed|quotaExceeded|uploadLimitExceeded",
     "📺 Nguyên nhân: YouTube từ chối đăng (lỗi máy chủ hoặc hết hạn mức upload trong ngày)."),
    (r"SAI SỐ CÂU|KẾT QUẢ: KHÔNG ĐẠT|deck không đạt",
     "📝 Nguyên nhân: nội dung Gemini viết không đạt kiểm tra (số câu/độ dài) sau các lượt sửa. Chạy lại thường sẽ qua."),
]


def reason(text):
    for pat, msg in RULES:
        if re.search(pat, text, re.I):
            return msg
    return ""


if __name__ == "__main__":
    txt = "\n".join(Path(p).read_text(encoding="utf-8", errors="replace") for p in sys.argv[1:] if Path(p).exists())
    print(reason(txt))
