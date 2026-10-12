"""
amr2.panel — bảng dữ liệu theo tháng và các hồi quy tố.

Mọi chuỗi từ FRED, tải 2026-10-09 qua điểm cuối .txt. Không chuỗi nào là Tier 3,
không chuỗi nào được thay thế âm thầm.

    TWEXAFEGSMTH     chỉ số đô la AFE danh nghĩa, trung bình tháng  — biến phụ thuộc
    GS10             UST 10 năm
    IRLTLT01DEM156N  trái phiếu chính phủ Đức 10 năm
    POILBREUSDM      Brent, USD/thùng
    FEDFUNDS         lãi suất quỹ liên bang hiệu dụng — chân GIÁ của S_Fed
    CPIAUCSL         CPI-U, để dựng lãi suất thực

Một khuyết tật dữ liệu được mang theo chứ không giấu: CPI tháng 2025-10 KHÔNG
TỒN TẠI. BLS không công bố vì đợt đóng cửa chính phủ liên bang bắt đầu
01/10/2025. Giá trị dùng ở đây là nội suy tuyến tính và `row.cpi_imputed` bật
True ở tháng đó. Đây đúng loại lỗi mà §11.5.2 của sách bắt được với RRPONTSYD —
một ô trống đọc nhầm thành một con số — nên nó được đánh dấu thay vì làm lơ.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import series as S                                                   # noqa: E402


def months(a: str, b: str) -> List[str]:
    ya, ma = int(a[:4]), int(a[5:])
    yb, mb = int(b[:4]), int(b[5:])
    out = []
    while (ya, ma) <= (yb, mb):
        out.append(f"{ya:04d}-{ma:02d}")
        ma += 1
        if ma == 13:
            ma, ya = 1, ya + 1
    return out


def prev(m: str) -> str:
    y, mm = int(m[:4]), int(m[5:])
    mm -= 1
    if mm == 0:
        mm, y = 12, y - 1
    return f"{y:04d}-{mm:02d}"


@dataclass(frozen=True)
class Row:
    month: str
    y: float            # 100·Δln DXY  — biến phụ thuộc
    cap: float          # Δ(chênh lệch 10 năm Mỹ–Đức), điểm phần trăm
    oil: float          # 100·Δln Brent
    pol: float          # Δ lãi suất quỹ liên bang, điểm phần trăm
    realcap: float      # Δ(chênh lệch THỰC), dùng CPI so cùng kỳ của Mỹ
    lvl_dxy: float
    lvl_brent: float
    cpi_imputed: bool


def _yoy(d: Dict[str, float], m: str) -> Optional[float]:
    y, mm = int(m[:4]), int(m[5:])
    back = f"{y-1:04d}-{mm:02d}"
    if m not in d or back not in d:
        return None
    return 100.0 * (d[m] / d[back] - 1.0)


def build(first: str = "2006-02", last: str = "2026-07") -> List[Row]:
    rows: List[Row] = []
    for m in months(first, last):
        p = prev(m)
        need = (S.DXY, S.US10, S.DE10, S.BRENT, S.FFR)
        if not all(k in d for d in need for k in (m, p)):
            continue
        y = 100.0 * math.log(S.DXY[m] / S.DXY[p])
        cap = (S.US10[m] - S.DE10[m]) - (S.US10[p] - S.DE10[p])
        oil = 100.0 * math.log(S.BRENT[m] / S.BRENT[p])
        pol = S.FFR[m] - S.FFR[p]

        # Chênh lệch THỰC: lợi suất danh nghĩa trừ lạm phát so cùng kỳ. Phía Đức
        # dùng CÙNG chỉ số lạm phát Mỹ là sai, nên vế Đức để nguyên danh nghĩa và
        # số hạng này chỉ khử lạm phát phía Mỹ. Nó là một PHÉP THỬ của ứng viên
        # "lãi suất thực", không phải một mệnh đề về chênh lệch thực đầy đủ.
        a, b = _yoy(S.CPI, m), _yoy(S.CPI, p)
        realcap = cap - ((a - b) if (a is not None and b is not None) else 0.0)

        rows.append(Row(
            month=m, y=y, cap=cap, oil=oil, pol=pol, realcap=realcap,
            lvl_dxy=S.DXY[m], lvl_brent=S.BRENT[m],
            cpi_imputed=(m in S.CPI_IMPUTED or p in S.CPI_IMPUTED),
        ))
    return rows


PANEL: List[Row] = build()
BYMONTH: Dict[str, Row] = {r.month: r for r in PANEL}


def window(a: str, b: str) -> List[Row]:
    return [r for r in PANEL if a <= r.month <= b]
