"""
amr2.estimate — OLS với sai số chuẩn Newey–West.

Vì sao HAC chứ không phải OLS thường. Lợi suất FX theo tháng có tương quan chuỗi
nhẹ và phương sai thay đổi mạnh theo chế độ. Sai số chuẩn OLS thường sẽ hẹp giả
tạo, và cả bài này dựa vào việc một hệ số có ý nghĩa hay không. Độ trễ chọn theo
quy tắc Newey–West: floor(4·(n/100)^(2/9)).

Không có hằng số trừ khi được yêu cầu rõ. Trong phiên trước, hằng số đóng gần một
nửa dự báo chân trời 12 tháng với t = +0,81 — nó không xứng ngần ấy việc.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .panel import Row


# --------------------------------------------------------------------------- #
# Đại số tuyến tính tối thiểu
# --------------------------------------------------------------------------- #

def _inv(A: List[List[float]]) -> List[List[float]]:
    k = len(A)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(k)] for i, row in enumerate(A)]
    for i in range(k):
        p = max(range(i, k), key=lambda r: abs(M[r][i]))
        if abs(M[p][i]) < 1e-14:
            raise ValueError("ma trận suy biến — hồi quy tố cộng tuyến")
        M[i], M[p] = M[p], M[i]
        d = M[i][i]
        M[i] = [v / d for v in M[i]]
        for r in range(k):
            if r == i:
                continue
            f = M[r][i]
            M[r] = [a - f * b for a, b in zip(M[r], M[i])]
    return [row[k:] for row in M]


@dataclass
class Fit:
    terms: List[str]
    beta: Dict[str, float]
    se: Dict[str, float]
    t: Dict[str, float]
    n: int
    r2: float
    sigma: float            # độ lệch chuẩn phần dư
    lags: int
    resid: List[float]
    sample: Tuple[str, str]

    def predict(self, x: Dict[str, float]) -> float:
        return sum(self.beta[k] * x.get(k, 0.0) for k in self.terms)

    def significant(self, thr: float = 2.0) -> List[str]:
        return [k for k in self.terms if abs(self.t[k]) >= thr]

    def line(self, k: str) -> str:
        return f"{self.beta[k]:+.4f}  (s.e. {self.se[k]:.4f}, t {self.t[k]:+.2f})"


def ols_hac(rows: Sequence[Row], terms: Sequence[str],
            const: bool = False) -> Fit:
    names = (["const"] if const else []) + list(terms)
    y = [r.y for r in rows]
    X = [[1.0] * const + [getattr(r, t) for t in terms] for r in rows] if const \
        else [[getattr(r, t) for t in terms] for r in rows]
    n, k = len(y), len(names)
    if n <= k + 2:
        raise ValueError("quá ít quan sát")

    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    inv = _inv(XtX)
    beta = [sum(inv[a][b] * Xty[b] for b in range(k)) for a in range(k)]
    resid = [y[i] - sum(beta[a] * X[i][a] for a in range(k)) for i in range(n)]

    # Newey–West
    L = max(1, int(math.floor(4 * (n / 100.0) ** (2.0 / 9.0))))
    Smat = [[0.0] * k for _ in range(k)]
    for i in range(n):
        for a in range(k):
            for b in range(k):
                Smat[a][b] += resid[i] * resid[i] * X[i][a] * X[i][b]
    for lag in range(1, L + 1):
        w = 1.0 - lag / (L + 1.0)
        for i in range(lag, n):
            for a in range(k):
                for b in range(k):
                    g = resid[i] * resid[i - lag] * (X[i][a] * X[i - lag][b]
                                                     + X[i - lag][a] * X[i][b])
                    Smat[a][b] += w * g
    V = [[sum(inv[a][c] * Smat[c][d] * inv[d][b] for c in range(k) for d in range(k))
          for b in range(k)] for a in range(k)]
    se = [math.sqrt(max(V[a][a], 0.0)) for a in range(k)]

    ybar = sum(y) / n
    ss_res = sum(e * e for e in resid)
    ss_tot = sum((v - ybar) ** 2 for v in y)
    sigma = math.sqrt(ss_res / (n - k))

    return Fit(
        terms=names,
        beta={names[a]: beta[a] for a in range(k)},
        se={names[a]: se[a] for a in range(k)},
        t={names[a]: (beta[a] / se[a] if se[a] > 0 else float("nan")) for a in range(k)},
        n=n, r2=1 - ss_res / ss_tot, sigma=sigma, lags=L, resid=resid,
        sample=(rows[0].month, rows[-1].month),
    )
