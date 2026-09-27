"""判定核对：合格 / 超差 两类，对照氦灯-587、汞灯-546 种子。

允差 0.08 nm。氦灯种子偏差 0.06 → 合格；汞灯种子偏差 0.23 → 超差。
判定入口、字段组装、详情、队列四处都已改为直喂真实数值，
这里直接核对 domain.judge 的输出与种子行保持一致。

运行方式（任选其一）：
    python test_domain_judge.py
    python -m pytest test_domain_judge.py
"""

import re
from pathlib import Path

from domain import TOLERANCE_NM, judge


# ---------- 合格类 ----------

def test_helium_seed_passes():
    # 对照种子「氦灯-587」：标称 587.56 / 实测 587.50，偏差 0.06 → 合格
    verdict, reason = judge(587.56, 587.50)
    assert verdict == "合格", f"氦灯种子应合格，实得 {verdict}"
    assert reason == "偏差 0.0600 nm 在允差内", reason


def test_deviation_002_passes():
    # 偏差 0.02 且灯种合法 → 合格
    verdict, reason = judge(546.07, 546.05)
    assert verdict == "合格", f"偏差 0.02 应合格，实得 {verdict}"
    assert reason == "偏差 0.0200 nm 在允差内", reason


def test_deviation_at_tolerance_passes():
    # 偏差恰为允差 0.08 → 仍合格（不得被跳过）
    verdict, reason = judge(0.0, TOLERANCE_NM)
    assert verdict == "合格", f"偏差恰等允差应合格，实得 {verdict}"
    assert reason == "偏差 0.0800 nm 在允差内", reason


# ---------- 超差类 ----------

def test_mercury_seed_fails():
    # 对照种子「汞灯-546」：标称 546.07 / 实测 546.30，偏差 0.23 → 超差
    verdict, reason = judge(546.07, 546.30)
    assert verdict == "超差", f"汞灯种子应超差，实得 {verdict}"
    assert reason == "偏差 0.2300 nm 超过允差 0.08", reason


def test_deviation_009_fails():
    # 偏差 0.09 略超允差 → 超差
    verdict, reason = judge(435.83, 435.92)
    assert verdict == "超差", f"偏差 0.09 应超差，实得 {verdict}"
    assert reason == "偏差 0.0900 nm 超过允差 0.08", reason


# ---------- 种子对照 ----------

def test_seed_rows_match_domain_judge():
    # api.py 里每条种子行的结论/理由都必须与 domain.judge 实时判定一致
    src = Path(__file__).with_name("api.py").read_text(encoding="utf-8")
    seeds = re.findall(
        r"\('([^']+)',\s*([\d.]+),\s*([\d.]+),\s*'done',\s*'([^']+)',\s*'([^']+)',\s*'seed'",
        src,
    )
    assert len(seeds) >= 2, "未在 api.py 找到氦灯/汞灯种子行"
    for lamp, nominal, measured, verdict, reason in seeds:
        got = judge(float(nominal), float(measured))
        assert got == (verdict, reason), f"种子 {lamp} 与 domain.judge 不一致: {got} != {(verdict, reason)}"


if __name__ == "__main__":
    checks = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for check in checks:
        check()
        print(f"ok {check.__name__}")
    print(f"{len(checks)} 项核对全部通过")
