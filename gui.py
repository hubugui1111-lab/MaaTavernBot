"""GUI 界面 —— PySide6 左侧控制 + 右侧日志 + 定时 + 托盘"""

import os, sys, time, queue, threading
from datetime import datetime, time as dtime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFrame,
    QSplitter, QCheckBox, QTimeEdit, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QTime
from PySide6.QtGui import QFont, QAction, QIcon


class LogSignal(QObject):
    new_log = Signal(str)


class BotGUI(QMainWindow):
    # 预设图标（简单 16x16 棕色块）
    _icon = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("炉石传说酒馆战旗 Bot")
        self.resize(960, 620)
        self.setMinimumSize(800, 500)

        self.controller = None
        self.tasker = None
        self.running = False
        self.bot_action = None
        self.connected = False
        self.log_signal = LogSignal()

        self._setup_theme()
        self._build_ui()
        self._setup_tray()
        self._connect_signals()

        # 定时器：每秒检查一次是否需要自动启停
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self._check_schedule)
        self.schedule_timer.start(15000)  # 每15秒检查

        # 状态刷新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._refresh_status)
        self.status_timer.start(1000)

    def _setup_theme(self):
        dark = "#2E1A0E"
        mid = "#3E2723"
        accent = "#5D4037"
        light = "#8D6E63"
        text = "#EFEBE9"
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {dark}; }}
            QWidget {{ color: {text}; font-family: Microsoft YaHei; font-size: 13px; }}
            QGroupBox {{ border: 1px solid {accent}; border-radius: 6px; margin-top: 12px;
                        padding-top: 16px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
            QLineEdit, QTimeEdit {{ background: {mid}; border: 1px solid {accent}; border-radius: 4px;
                        padding: 5px 8px; }}
            QTextEdit {{ background: {mid}; border: 1px solid {accent}; border-radius: 4px;
                        font-size: 12px; }}
            QPushButton {{ background: {accent}; border: none; border-radius: 4px;
                          padding: 6px 16px; min-width: 60px; }}
            QPushButton:hover {{ background: {light}; }}
            QPushButton:pressed {{ background: {mid}; }}
            QPushButton:disabled {{ background: #4E342E; color: #8D6E63; }}
            QPushButton#btn_start {{ background: #2E7D32; }}
            QPushButton#btn_start:hover {{ background: #388E3C; }}
            QPushButton#btn_stop {{ background: #C62828; }}
            QPushButton#btn_stop:hover {{ background: #D32F2F; }}
            QFrame#status_bar {{ background: {accent}; border-radius: 4px; padding: 6px; }}
            QLabel#title {{ font-size: 18px; font-weight: bold; }}
            QLabel#status_on {{ color: #4CAF50; font-weight: bold; }}
            QLabel#status_off {{ color: #9E9E9E; }}
            QSplitter::handle {{ background: {accent}; width: 1px; }}
            QCheckBox {{ spacing: 6px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; }}
            QMenu {{ background: {mid}; border: 1px solid {accent}; }}
            QMenu::item:selected {{ background: {accent}; }}
            QTimeEdit::drop-down {{ border: none; width: 20px; }}
        """)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("炉石传说酒馆战旗 Bot")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        # === 左面板 ===
        left = QWidget()
        left.setMinimumWidth(340)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 8, 0)
        ll.setSpacing(8)

        # 连接
        conn = QGroupBox("连接设置")
        cl = QVBoxLayout(conn)
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("ADB 端口:"))
        self.port_input = QLineEdit("16416")
        self.port_input.setMaximumWidth(120)
        r1.addWidget(self.port_input)
        self.btn_connect = QPushButton("连接")
        r1.addWidget(self.btn_connect)
        r1.addStretch()
        cl.addLayout(r1)
        self.conn_status = QLabel("● 未连接")
        self.conn_status.setObjectName("status_off")
        cl.addWidget(self.conn_status)
        ll.addWidget(conn)

        # 状态
        status = QGroupBox("运行状态")
        sl = QVBoxLayout(status)
        self.status_bar = QFrame()
        self.status_bar.setObjectName("status_bar")
        sb = QHBoxLayout(self.status_bar)
        self.lbl_phase = QLabel("阶段: -")
        self.lbl_turn = QLabel("回合: -")
        self.lbl_running = QLabel("● 已停止")
        self.lbl_running.setObjectName("status_off")
        sb.addWidget(self.lbl_phase)
        sb.addWidget(self.lbl_turn)
        sb.addStretch()
        sb.addWidget(self.lbl_running)
        sl.addWidget(self.status_bar)
        ll.addWidget(status)

        # 控制
        ctrl = QGroupBox("控制")
        ctrl_layout = QHBoxLayout(ctrl)
        self.btn_start = QPushButton("▶ 开始")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setMinimumHeight(36)
        self.btn_stop = QPushButton("■ 停止")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setMinimumHeight(36)
        self.btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        btn_tray = QPushButton("⤓ 托盘")
        btn_tray.setToolTip("最小化到系统托盘")
        btn_tray.clicked.connect(self._minimize_to_tray)
        ctrl_layout.addWidget(btn_tray)
        ll.addWidget(ctrl)

        # 定时
        sched = QGroupBox("定时运行")
        sched_layout = QVBoxLayout(sched)
        self.sched_enable = QCheckBox("启用定时运行")
        sched_layout.addWidget(self.sched_enable)

        sr1 = QHBoxLayout()
        sr1.addWidget(QLabel("开始时间:"))
        self.time_start = QTimeEdit(QTime(0, 0))
        self.time_start.setDisplayFormat("HH:mm")
        sr1.addWidget(self.time_start)
        sr1.addStretch()
        sched_layout.addLayout(sr1)

        sr2 = QHBoxLayout()
        sr2.addWidget(QLabel("结束时间:"))
        self.time_end = QTimeEdit(QTime(8, 0))
        self.time_end.setDisplayFormat("HH:mm")
        sr2.addWidget(self.time_end)
        sr2.addStretch()
        sched_layout.addLayout(sr2)

        self.lbl_sched = QLabel("定时未启用")
        self.lbl_sched.setObjectName("status_off")
        sched_layout.addWidget(self.lbl_sched)
        ll.addWidget(sched)

        disclaimer = QLabel("本软件开源免费，仅供学习交流使用")
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer.setStyleSheet("color: #8D6E63; font-size: 11px; padding: 4px;")
        ll.addWidget(disclaimer)

        ll.addStretch()

        # === 右面板 ===
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        rl.setSpacing(4)

        lh = QHBoxLayout()
        lh.addWidget(QLabel("操作日志"))
        lh.addStretch()
        btn_clear = QPushButton("清空")
        btn_clear.setMaximumWidth(60)
        lh.addWidget(btn_clear)
        rl.addLayout(lh)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        rl.addWidget(self.log_text)
        btn_clear.clicked.connect(self.log_text.clear)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([360, 560])

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        # 用简单色块做图标
        from PySide6.QtGui import QPixmap, QPainter, QColor
        px = QPixmap(32, 32)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        painter.setBrush(QColor("#5D4037"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
        painter.end()
        self.tray.setIcon(QIcon(px))
        self.tray.setToolTip("炉石传说酒馆战旗 Bot")

        menu = QMenu()
        action_show = QAction("显示主窗口")
        action_show.triggered.connect(self._show_window)
        menu.addAction(action_show)
        action_quit = QAction("退出")
        action_quit.triggered.connect(self._quit_app)
        menu.addAction(action_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.activateWindow()

    def _quit_app(self):
        self._stop()
        self.tray.hide()
        QApplication.quit()

    def _minimize_to_tray(self):
        self.hide()
        self._log("已最小化到托盘")

    def closeEvent(self, event):
        self._stop()
        self.tray.hide()
        QApplication.quit()

    # ---- 定时 ----

    def _check_schedule(self):
        if not self.sched_enable.isChecked():
            self.lbl_sched.setText("定时未启用")
            return

        now = datetime.now().time()
        st = self.time_start.time().toPython()
        et = self.time_end.time().toPython()

        # 处理跨天（如 22:00~06:00）
        if st <= et:
            in_range = st <= now <= et
        else:
            in_range = now >= st or now <= et

        if in_range and not self.running:
            if self.connected:
                self.lbl_sched.setText(f"定时触发：自动开始 {now.strftime('%H:%M')}")
                self._start()
            elif not self.connected:
                self.lbl_sched.setText("定时触发：自动连接...")
                self._auto_connect_and_start()
        elif not in_range and self.running:
            self.lbl_sched.setText(f"定时结束：自动停止 {now.strftime('%H:%M')}")
            self._stop(close_game=True)
        elif in_range and self.running:
            self.lbl_sched.setText(f"定时运行中 ({now.strftime('%H:%M')})")
        else:
            self.lbl_sched.setText(f"等待定时 ({now.strftime('%H:%M')})")

    def _auto_connect_and_start(self):
        """自动连接并启动"""
        port = self.port_input.text().strip()
        if not port:
            self._log("[定时] 端口为空，无法自动连接")
            return
        self.btn_connect.setEnabled(False)

        def do_auto():
            try:
                from maa.toolkit import Toolkit
                from maa.controller import AdbController
                from maa.resource import Resource
                from maa.tasker import Tasker
                from bot.phase_detector import PhaseDetector
                from bot.game_bot import BotAction

                app_dir = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
                maa_dir = os.path.join(os.path.dirname(sys.executable), ".maa") if getattr(sys, "frozen", False) else os.path.join(app_dir, ".maa")
                os.makedirs(maa_dir, exist_ok=True)
                Toolkit.init_option(maa_dir)

                devices = Toolkit.find_adb_devices()
                device = None
                for d in devices:
                    if port in d.address:
                        device = d
                        break
                if not device:
                    self.log_signal.new_log.emit("[定时] 未找到设备")
                    self.btn_connect.setEnabled(True)
                    return

                self.controller = AdbController(
                    adb_path=device.adb_path, address=device.address,
                    screencap_methods=device.screencap_methods,
                    input_methods=device.input_methods, config=device.config,
                )
                self.controller.post_connection().wait()
                if not self.controller.connected:
                    self.log_signal.new_log.emit("[定时] 连接失败")
                    self.btn_connect.setEnabled(True)
                    return

                BotAction.adb_device = device.address
                resource_dir = os.path.join(app_dir, "resource")
                resource = Resource()
                resource.post_bundle(resource_dir).wait()
                resource.register_custom_recognition("PhaseDetector", PhaseDetector())
                self.bot_action = BotAction()
                resource.register_custom_action("BotAction", self.bot_action)

                self.tasker = Tasker()
                self.tasker.bind(resource, self.controller)
                if not self.tasker.inited:
                    self.log_signal.new_log.emit("[定时] 初始化失败")
                    self.btn_connect.setEnabled(True)
                    return

                self.connected = True
                self.conn_status.setText("● 已连接")
                self.log_signal.new_log.emit("[定时] 自动连接成功，启动...")
                self._start()
            except Exception as e:
                self.log_signal.new_log.emit(f"[定时] 错误: {e}")
                self.btn_connect.setEnabled(True)

        threading.Thread(target=do_auto, daemon=True).start()

    # ---- 连接 ----

    def _connect(self):
        port = self.port_input.text().strip()
        if not port:
            self._log("[错误] 请输入端口号")
            return
        self.btn_connect.setEnabled(False)
        self._log(f"正在连接 127.0.0.1:{port} ...")

        def do_connect():
            try:
                from maa.toolkit import Toolkit
                from maa.controller import AdbController
                from maa.resource import Resource
                from maa.tasker import Tasker
                from bot.phase_detector import PhaseDetector
                from bot.game_bot import BotAction

                app_dir = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
                maa_dir = os.path.join(os.path.dirname(sys.executable), ".maa") if getattr(sys, "frozen", False) else os.path.join(app_dir, ".maa")
                os.makedirs(maa_dir, exist_ok=True)
                Toolkit.init_option(maa_dir)

                devices = Toolkit.find_adb_devices()
                device = None
                for d in devices:
                    if port in d.address:
                        device = d
                        break
                if not device:
                    self.log_signal.new_log.emit(f"[错误] 未找到端口 {port} 的设备")
                    self.btn_connect.setEnabled(True)
                    return

                self.controller = AdbController(
                    adb_path=device.adb_path, address=device.address,
                    screencap_methods=device.screencap_methods,
                    input_methods=device.input_methods, config=device.config,
                )
                self.controller.post_connection().wait()
                if not self.controller.connected:
                    self.log_signal.new_log.emit("[错误] 连接失败")
                    self.btn_connect.setEnabled(True)
                    return

                BotAction.adb_device = device.address
                resource_dir = os.path.join(app_dir, "resource")
                resource = Resource()
                resource.post_bundle(resource_dir).wait()
                resource.register_custom_recognition("PhaseDetector", PhaseDetector())
                self.bot_action = BotAction()
                resource.register_custom_action("BotAction", self.bot_action)

                self.tasker = Tasker()
                self.tasker.bind(resource, self.controller)
                if not self.tasker.inited:
                    self.log_signal.new_log.emit("[错误] Tasker 初始化失败")
                    self.btn_connect.setEnabled(True)
                    return

                self.connected = True
                self.log_signal.new_log.emit("[信息] 连接成功，可以开始")
                self.conn_status.setText("● 已连接")
            except Exception as e:
                self.log_signal.new_log.emit(f"[错误] 连接异常: {e}")
                self.btn_connect.setEnabled(True)

        threading.Thread(target=do_connect, daemon=True).start()

    # ---- 开始/停止 ----

    def _start(self):
        if not self.tasker:
            self._log("[错误] 请先连接设备")
            return

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.running = True  # 立即标记，防止定时重复触发
        self.lbl_running.setText("● 运行中")
        self._log("检测游戏状态...")

        def do_start():
            from bot.phase_detector import PhaseDetector
            detector = PhaseDetector()
            known = {"main_menu", "mode_select", "bg_lobby", "hero_select", "recruit", "game_end"}

            img = self.controller.post_screencap().wait().get()
            phase = detector.analyze(None, type('a', (), {'image': img})()).detail.get("phase", "combat")

            if phase not in known:
                self.log_signal.new_log.emit("游戏未启动，正在启动...")
                self.controller.post_start_app("com.blizzard.wtcg.hearthstone").wait()
                for i in range(24):
                    time.sleep(5)
                    img = self.controller.post_screencap().wait().get()
                    p = detector.analyze(None, type('a', (), {'image': img})()).detail.get("phase", "combat")
                    self.log_signal.new_log.emit(f"  {(i+1)*5}s: {p}")
                    if p in known:
                        break

            self.tasker.post_task("MainLoop")
            self.log_signal.new_log.emit("[信息] Bot 启动")

        threading.Thread(target=do_start, daemon=True).start()

    def _stop(self, close_game=False):
        self.running = False
        self.btn_stop.setEnabled(False)
        self.lbl_running.setText("● 已停止")
        self._log("[信息] 正在停止...")

        def do_stop():
            if self.tasker:
                self.tasker.post_stop().wait()
            self.btn_start.setEnabled(True)
            self.log_signal.new_log.emit("[信息] Bot 已停止")
            if close_game:
                self.log_signal.new_log.emit("[定时] 正在关闭游戏...")
                try:
                    import subprocess
                    from bot.game_bot import BotAction
                    if BotAction.adb_device:
                        adb = "D:/MuMuPlayer/nx_main/adb.exe"
                        subprocess.run(f'\"{adb}\" -s {BotAction.adb_device} shell \"am force-stop com.blizzard.wtcg.hearthstone\"', shell=True, timeout=5)
                        self.log_signal.new_log.emit("[定时] 游戏已关闭")
                except Exception as e:
                    self.log_signal.new_log.emit(f"[定时] 关闭游戏失败: {e}")

        threading.Thread(target=do_stop, daemon=True).start()

    # ---- 日志 ----

    def _log(self, msg):
        self.log_signal.new_log.emit(msg)

    def _append_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"{ts} {msg}")

    def _refresh_status(self):
        if self.bot_action and self.running:
            self.lbl_phase.setText(f"阶段: {self.bot_action.last_phase}")
            self.lbl_turn.setText(f"回合: {self.bot_action.turn_number}")

    def _connect_signals(self):
        self.btn_connect.clicked.connect(self._connect)
        self.btn_start.clicked.connect(self._start)
        self.btn_stop.clicked.connect(self._stop)
        self.log_signal.new_log.connect(self._append_log)
        self.sched_enable.toggled.connect(lambda: self._check_schedule())
        self.time_start.timeChanged.connect(lambda: self._check_schedule())
        self.time_end.timeChanged.connect(lambda: self._check_schedule())


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)  # 托盘保留
    window = BotGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
