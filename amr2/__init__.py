"""
amr2 — mô hình sau chỉnh.

Bản đối chứng của `amr`, giữ nguyên bên cạnh chứ không thay thế. `amr` là mô hình
của cuốn sách, trung thành với đặc tả chuẩn sau ISSUES; `amr2` là cái mà dữ liệu
2026 đòi hỏi sau khi `amr` bị chấm điểm ngoài mẫu.

    from amr2 import CorrectedModel
    m = CorrectedModel().train().prune()
    print(m.fit.r2, m.fit.beta)
    for f in m.forecast_path(["2025-11","2025-12","2026-01"]):
        print(f.line())

Chạy đối chiếu đầy đủ với `amr`:

    python -m amr2
"""

from .estimate import Fit, ols_hac                                   # noqa: F401
from .model import (                                                 # noqa: F401
    LAYER2_ARROWS, OIL_SHOCK_EVIDENCE, OIL_SHOCK_THRESHOLD,
    CorrectedModel, Forecast, Regime,
)
from .panel import BYMONTH, PANEL, Row, build, months, prev, window   # noqa: F401

__version__ = "2.0.0"
