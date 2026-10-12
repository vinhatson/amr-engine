"""amr3 — cùng mô hình, đọc trong hệ toạ độ hình học.

    python -m amr3                    # bản đồ, ba phép đo, quét τ
    python tests/test_amr3.py         # kiểm thử, gồm cả lồng khít τ→0
"""

from .atlas import (
    ATLAS, Address, Role, Sheet, cross_sheet_edges, on_sheet, summary, unmeasured,
)
from .geometry import (
    H_STAR, P_DEPTH, PARAMS, Q_TAUT, TAU_CEILING, TAU_CEILING_BY_MODE,
    Decomposition, Memory, Param,
    SheetState, Transversality, tautness,
)
from .model import Manifold, Options3, Step, Trajectory, commutator, holonomy, residual, trace
from .operators import Commutator, Holonomy, Move, Residual

__all__ = [
    "ATLAS", "Address", "Role", "Sheet", "cross_sheet_edges", "on_sheet", "summary",
    "H_STAR", "P_DEPTH", "PARAMS", "Q_TAUT", "TAU_CEILING", "TAU_CEILING_BY_MODE",
    "Decomposition",
    "Memory", "Param",
    "SheetState", "Transversality", "unmeasured",
    "tautness", "Manifold", "Options3", "Step", "Trajectory", "commutator",
    "holonomy", "residual", "trace", "Commutator", "Holonomy", "Move", "Residual",
]
