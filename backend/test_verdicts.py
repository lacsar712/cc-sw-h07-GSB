"""合格/超差两类判定核对，对照氦灯、汞灯种子。

直接运行: python3 test_verdicts.py
或用 pytest: pytest test_verdicts.py
"""

import pathlib

from domain import TOLERANCE_NM, judge

BACKEND_DIR = pathlib.Path(__file__).parent

# 与 api.py on_startup 写入的种子保持一致
HELIUM_SEED = {
    "lamp": "氦灯-587",
    "nominal": 587.56,
    "measured": 587.50,
    "verdict": "合格",
    "reason": "偏差 0.0600 nm 在允差内",
}
MERCURY_SEED = {
    "lamp": "汞灯-546",
    "nominal": 546.07,
    "measured": 546.30,
    "verdict": "超差",
    "reason": "偏差 0.2300 nm 超过允差 0.08",
}


# ---------- 合格类:偏差够线必须走进合格 ----------

def test_pass_helium_seed():
    """氦灯种子:偏差 0.06 nm,灯种合法 → 合格,理由与种子逐字一致。"""
    verdict, reason = judge(HELIUM_SEED["nominal"], HELIUM_SEED["measured"])
    assert verdict == HELIUM_SEED["verdict"], f"氦灯种子应合格,实得 {verdict}"
    assert reason == HELIUM_SEED["reason"], f"理由应为 {HELIUM_SEED['reason']!r},实得 {reason!r}"


def test_pass_small_deviation():
    """偏差 0.02 nm → 合格,且理由如实写出纳米偏差。"""
    verdict, reason = judge(632.80, 632.82)
    assert verdict == "合格", f"偏差 0.02 应合格,实得 {verdict}"
    assert reason == "偏差 0.0200 nm 在允差内", f"实得 {reason!r}"


def test_pass_boundary_deviation():
    """偏差恰为允差 0.08 nm → 仍算合格(<=)。"""
    verdict, reason = judge(500.00, 500.00 + TOLERANCE_NM)
    assert verdict == "合格", f"边界 0.08 应合格,实得 {verdict}"
    assert "0.0800" in reason, f"理由须含实测偏差,实得 {reason!r}"


# ---------- 超差类:汞灯继续超差 ----------

def test_fail_mercury_seed():
    """汞灯种子:偏差 0.23 nm → 超差,理由与种子逐字一致。"""
    verdict, reason = judge(MERCURY_SEED["nominal"], MERCURY_SEED["measured"])
    assert verdict == MERCURY_SEED["verdict"], f"汞灯种子应超差,实得 {verdict}"
    assert reason == MERCURY_SEED["reason"], f"理由应为 {MERCURY_SEED['reason']!r},实得 {reason!r}"


def test_fail_large_deviation():
    """偏差 0.37 nm → 超差,理由写明超过允差。"""
    verdict, reason = judge(435.83, 436.20)
    assert verdict == "超差", f"偏差 0.37 应超差,实得 {verdict}"
    assert "超过允差" in reason, f"实得 {reason!r}"


# ---------- 防回归:判定不得再被旁路,四处都喂真实数值 ----------

def test_no_trap_modules_wired():
    """api.py / worker.py 不得再引用任何旁路模块。"""
    traps = ("h07_queue_trap", "h07_surface_trap", "h07_rules_mask", "judge_skip")
    for name in ("api.py", "worker.py"):
        src = (BACKEND_DIR / name).read_text(encoding="utf-8")
        for trap in traps:
            assert trap not in src, f"{name} 仍引用旁路模块 {trap}"


def test_worker_judges_via_domain():
    """worker 判定入口必须直接调用 domain.judge,不得跳过纳米偏差。"""
    src = (BACKEND_DIR / "worker.py").read_text(encoding="utf-8")
    assert "from domain import judge" in src
    assert "judge(row[" in src, "worker 应对库中真实标称/实测调用 judge"


def test_seed_block_matches_domain():
    """api.py 种子块与 domain.judge 对同一对标称/实测的输出一致(对照氦灯种子)。"""
    src = (BACKEND_DIR / "api.py").read_text(encoding="utf-8")
    for seed in (HELIUM_SEED, MERCURY_SEED):
        verdict, reason = judge(seed["nominal"], seed["measured"])
        assert (verdict, reason) == (seed["verdict"], seed["reason"]), seed["lamp"]
        assert seed["lamp"] in src, f"api.py 缺少种子 {seed['lamp']}"
        assert seed["reason"] in src, f"api.py 种子理由与判定输出不符: {seed['reason']!r}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"{len(fns) - failed}/{len(fns)} 项核对通过")
    raise SystemExit(1 if failed else 0)
