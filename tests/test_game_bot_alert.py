"""game_bot 异常告警测试 —— 验证 _restart_game 触发通知"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_restart_triggers_alert():
    """_restart_game 成功后应该调用 send_alert("卡住重启", ...)"""
    from unittest.mock import patch, MagicMock
    from bot.notify import set_token

    set_token("test-token")

    # 拦截 send_alert
    with patch("bot.notify.send_alert") as mock_send:
        from bot.game_bot import BotAction

        bot = BotAction()
        bot.adb_device = "127.0.0.1:5555"  # 假设备

        # 直接 mock _adb_shell 跳过真实 ADB
        bot._adb_shell = MagicMock(return_value=True)

        # 调 _restart_game
        bot._restart_game()

        # 验证 send_alert 被调用
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert "卡住重启" in call_args[0], f"标题应包含'卡住重启'，实际: {call_args[0]}"
        assert "v1.5" in call_args[1], f"内容应包含版本号，实际: {call_args[1]}"


if __name__ == "__main__":
    test_restart_triggers_alert()
    print("PASS: restart_triggers_alert")
