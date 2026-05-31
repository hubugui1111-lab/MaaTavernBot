"""GUI 启动异常通知测试"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_startup_error_sends_offline_alert():
    """_start 截图失败时应该发送掉线通知"""
    from unittest.mock import patch, MagicMock
    from bot.notify import set_token

    set_token("test-token")

    with patch("bot.notify.send_alert") as mock_send:
        from gui import BotGUI

        # 创建一个不显示 UI 的实例
        app = MagicMock()
        gui = BotGUI.__new__(BotGUI)
        gui.controller = MagicMock()
        gui.controller.post_screencap.return_value.wait.return_value.get.side_effect = Exception("Failed to get cached image")
        gui.tasker = MagicMock()
        gui.tasker.inited = True
        gui.running = False
        gui.token_input = MagicMock()
        gui.token_input.text.return_value = "test-token"
        gui._cfg_path = MagicMock(return_value="/tmp/test_config.json")
        gui.log_signal = MagicMock()
        gui.btn_start = MagicMock()
        gui.btn_stop = MagicMock()
        gui.lbl_running = MagicMock()
        gui._log = MagicMock()
        gui.VERSION = "1.5"

        # 调 _start，异常在线程里触发，需要等一下
        import time
        gui._start()
        time.sleep(0.5)

        # 验证 send_alert 被调用了
        called = mock_send.call_count > 0
        assert called, f"send_alert 未被调用，call_count={mock_send.call_count}"


if __name__ == "__main__":
    test_startup_error_sends_offline_alert()
    print("PASS: startup_error_sends_offline_alert")
