"""ADB 断连检测测试 —— 连续截图失败触发通知"""
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_offline_triggers_alert():
    """_check_adb_alive 连续 3 次失败应发送掉线通知"""
    from unittest.mock import patch, MagicMock
    from bot.notify import set_token

    set_token("test-token")

    with patch("bot.notify.send_alert") as mock_send:
        from bot.game_bot import BotAction

        bot = BotAction()
        bot._offline_count = 0
        bot._last_ok_time = time.time()

        # 模拟一个永远返回 None 的 controller
        fake_ctrl = MagicMock()
        fake_ctrl.post_screencap.return_value.wait.return_value.get.return_value = None

        # 连续 3 次调用，前 2 次不触发，第 3 次触发
        for i in range(3):
            bot._check_adb_alive(fake_ctrl)

        # 第 3 次应该触发通知
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert "掉线" in call_args[0], f"标题应包含'掉线'，实际: {call_args[0]}"


def test_offline_resets_on_success():
    """一次成功截图应重置计数器"""
    from bot.notify import set_token

    set_token("test-token")

    from bot.game_bot import BotAction
    from unittest.mock import MagicMock

    bot = BotAction()
    bot._offline_count = 2  # 已经失败 2 次

    fake_ctrl = MagicMock()
    fake_img = MagicMock()
    fake_img.size = 100
    fake_ctrl.post_screencap.return_value.wait.return_value.get.return_value = fake_img

    bot._check_adb_alive(fake_ctrl)
    assert bot._offline_count == 0, f"成功后应重置，实际: {bot._offline_count}"


if __name__ == "__main__":
    test_offline_triggers_alert()
    print("PASS: offline_triggers_alert")
    test_offline_resets_on_success()
    print("PASS: offline_resets_on_success")
