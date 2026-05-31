"""版本比较测试 —— 1.5 vs 1.5.0 应视为相同"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _compare(cur, latest):
    """版本比较：补零对齐后逐段比较"""
    cur_parts = [int(x) for x in cur.split(".")]
    new_parts = [int(x) for x in latest.split(".")]
    # 补零对齐长度
    max_len = max(len(cur_parts), len(new_parts))
    cur_parts += [0] * (max_len - len(cur_parts))
    new_parts += [0] * (max_len - len(new_parts))
    for c, n in zip(cur_parts, new_parts):
        if n > c:
            return True
        if n < c:
            return False
    return False


def test_same_version_different_length():
    """1.5 == 1.5.0, 不应该判定为更新"""
    assert not _compare("1.5", "1.5.0"), "1.5 vs 1.5.0 不应判为更新"
    assert not _compare("1.5.0", "1.5"), "1.5.0 vs 1.5 不应判为更新"


def test_truly_newer():
    """真正的更新应该检测到"""
    assert _compare("1.4", "1.5"), "1.4 vs 1.5 应该是更新"
    assert _compare("1.5.0", "1.5.1"), "1.5.0 vs 1.5.1 应该是更新"
    assert _compare("1.5", "2.0"), "1.5 vs 2.0 应该是更新"


def test_not_newer():
    """旧版本不判为更新"""
    assert not _compare("2.0", "1.5"), "2.0 vs 1.5 不是更新"
    assert not _compare("1.5", "1.5"), "1.5 vs 1.5 不是更新"


if __name__ == "__main__":
    test_same_version_different_length()
    print("PASS: same_version_different_length")
    test_truly_newer()
    print("PASS: truly_newer")
    test_not_newer()
    print("PASS: not_newer")
