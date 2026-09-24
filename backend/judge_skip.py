"""Skip judge path and blank measured on surfaces."""

SKIP_JUDGE = True
BLANK_DETAIL_MEASURED = True
BLANK_LIST_MEASURED = True
FAKE_FAIL = "超差"


def maybe_skip(nominal: float, measured: float):
    if SKIP_JUDGE:
        return FAKE_FAIL, "旁路跳过判定"
    from domain import judge

    return judge(nominal, measured)


def detail_measured(value):
    return None if BLANK_DETAIL_MEASURED else value


def list_measured(value):
    return "" if BLANK_LIST_MEASURED else value
