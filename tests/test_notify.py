"""notify 模块单元测试 —— debounce + token 校验"""
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_empty_token_does_nothing():
    """Token 为空时不发请求，也不记入 _last_sent"""
    from bot.notify import set_token, send_alert, _last_sent
    set_token("")
    before = len(_last_sent)
    send_alert("测试", "内容")
    after = len(_last_sent)
    assert before == after, "Token 为空时不应记录发送时间"


def test_debounce_blocks_within_30min():
    """同一标题 30 分钟内只发一次"""
    from bot.notify import set_token, send_alert, _last_sent, DEBOUNCE_MIN
    set_token("fake-token-for-test")

    # 模拟第一次发送
    _last_sent["测试标题"] = time.time() - 60  # 1 分钟前发过
    before = dict(_last_sent)  # 拷贝
    send_alert("测试标题", "重复内容")
    assert _last_sent["测试标题"] == before["测试标题"], \
        "30 分钟内不应更新发送时间"


def test_debounce_allows_after_30min():
    """30 分钟后可以再发"""
    from bot.notify import set_token, send_alert, _last_sent, DEBOUNCE_MIN
    set_token("fake-token-for-test")

    _last_sent["旧标题"] = time.time() - DEBOUNCE_MIN * 60 - 10  # 30 分钟前
    send_alert("旧标题", "新的内容")
    assert _last_sent["旧标题"] > time.time() - 5, \
        "超过 30 分钟后应该更新发送时间"


if __name__ == "__main__":
    test_empty_token_does_nothing()
    print("PASS: empty_token_does_nothing")
    test_debounce_blocks_within_30min()
    print("PASS: debounce_blocks_within_30min")
    test_debounce_allows_after_30min()
    print("PASS: debounce_allows_after_30min")
    print("\nAll 3 tests passed!")
