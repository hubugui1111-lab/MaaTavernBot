"""GUI 界面 —— 顶部导航 + 左侧控制 + 右侧日志"""

import os, sys, time, json, threading
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFrame,
    QCheckBox, QTimeEdit, QSystemTrayIcon, QMenu, QScrollArea,
    QStackedWidget, QDialog, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QTime, QUrl, Slot
from PySide6.QtGui import QFont, QDesktopServices, QIcon


class LogSignal(QObject):
    new_log = Signal(str)
    show_dialog = Signal(str, str)
    conn_ok = Signal()
    conn_fail = Signal()
    start_ok = Signal()
    start_fail = Signal()


class GuiLogStream:
    def __init__(self, s): self.s = s; self.buf = ""
    def write(self, t):
        self.buf += t
        if "\n" in self.buf:
            ls = self.buf.split("\n"); self.buf = ls[-1]
            for l in ls[:-1]:
                if l.strip(): self.s.new_log.emit(l.strip())
    def flush(self):
        if self.buf.strip(): self.s.new_log.emit(self.buf.strip()); self.buf = ""


class BotGUI(QMainWindow):
    VERSION = "1.7.0"
    GITHUB_API = "https://api.github.com/repos/hubugui1111-lab/MaaTavernBot/releases/latest"
    CHANGELOG = """
MaaTavernBot v1.7 更新内容:

• 炉石酒馆主题 QSS 界面 (金色边框 + 暖色文字 + 暗棕底)
• PushPlus 微信异常告警 (卡住/断线自动通知)
• 版本检查修复 (1.5 和 1.5.0 不再误判)
• 桌面快捷方式 bat 文件
• 11 种界面模板匹配导航
• 任务自动更换 (MinerU OCR + 千问备份)
• 软件图标: 炉石石碑漩涡
• 启动自动杀旧进程
""".strip()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MaaTavernBot v{self.VERSION}")
        self.resize(960, 640); self.setMinimumSize(800, 500)

        # 图标路径
        if getattr(sys, 'frozen', False):
            self._app_dir = sys._MEIPASS
        else:
            self._app_dir = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(self._app_dir, "resource", "app_icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))
        self.controller = None; self.tasker = None
        self.running = False; self.connected = False
        self.log_signal = LogSignal()

        self._setup_theme()
        self._build_ui()
        self._setup_tray()
        self._connect_signals()

        self.schedule_timer = QTimer(); self.schedule_timer.timeout.connect(self._check_schedule); self.schedule_timer.start(15000)
        self.status_timer = QTimer(); self.status_timer.timeout.connect(self._refresh_status); self.status_timer.start(1000)
        QTimer.singleShot(500, self._startup_tasks)

    def _startup_tasks(self):
        """启动流程：公告 → 检查更新 → 自动连接"""
        self._show_announcement(from_startup=True)
        self._check_update(silent=True)
        QTimer.singleShot(1500, self._auto_connect)

    def _setup_theme(self):
        # QSS 已由 main() 从 resource/tavern.qss 加载
        pass

    def _build_ui(self):
        c = QWidget(); self.setCentralWidget(c)
        root = QVBoxLayout(c); root.setContentsMargins(8,8,8,8); root.setSpacing(6)

        # 标题栏
        hdr = QHBoxLayout()
        title = QLabel("MaaTavernBot"); title.setObjectName("title")
        hdr.addWidget(title); hdr.addStretch()
        ver = QLabel(f"v{self.VERSION}"); ver.setStyleSheet("color:#8D6E63;font-size:11px;")
        hdr.addWidget(ver); root.addLayout(hdr)

        # 顶部导航
        nav = QHBoxLayout(); nav.setSpacing(4)
        self.pages = QStackedWidget()
        nav_names = [("🎮 一键长草", 0), ("❓ 帮助", 1), ("🔧 工具", 2), ("⚙️ 设置", 3)]
        self.nav_btns = []
        for name, idx in nav_names:
            btn = QLabel(name); btn.setObjectName("nav_btn"); btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.mousePressEvent = lambda e, i=idx: self._switch_page(i)
            nav.addWidget(btn); self.nav_btns.append(btn)
        nav.addStretch()
        root.addLayout(nav)

        # 分隔线
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("background:#5D4037;max-height:1px;")
        root.addWidget(sep)

        # 页面
        self.pages.addWidget(self._page_play())
        self.pages.addWidget(self._page_help())
        self.pages.addWidget(self._page_tools())
        self.pages.addWidget(self._page_settings())
        root.addWidget(self.pages, 1)
        self._switch_page(0)

    def _switch_page(self, idx):
        for i, b in enumerate(self.nav_btns):
            b.setStyleSheet("QLabel#nav_btn { background: " + ("#5D4037" if i == idx else "transparent") + "; padding: 6px 16px; border-radius: 4px; font-size: 14px; }")
        self.pages.setCurrentIndex(idx)

    # ===== 一键长草 =====
    def _page_play(self):
        w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(0,4,0,0)
        # 左侧控制
        left = QWidget(); left.setFixedWidth(360); ll = QVBoxLayout(left); ll.setContentsMargins(0,0,6,0); ll.setSpacing(8)

        # 状态
        gs = QGroupBox("运行状态"); gsl = QVBoxLayout(gs)
        self.status_bar = QFrame(); self.status_bar.setObjectName("status_bar"); sb = QHBoxLayout(self.status_bar)
        self.lbl_phase = QLabel("阶段: -"); self.lbl_turn = QLabel("回合: -"); self.lbl_running = QLabel("● 已停止")
        self.lbl_running.setProperty("status", "stopped")
        sb.addWidget(self.lbl_phase); sb.addWidget(self.lbl_turn); sb.addStretch(); sb.addWidget(self.lbl_running)
        gsl.addWidget(self.status_bar); ll.addWidget(gs)

        # 控制按钮
        gc = QGroupBox("控制"); gcl = QHBoxLayout(gc)
        self.btn_start = QPushButton("▶ 开始"); self.btn_start.setObjectName("btn_start")
        self.btn_stop = QPushButton("■ 停止"); self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)
        btn_tray = QPushButton("⤓ 托盘"); btn_tray.clicked.connect(self._minimize_to_tray)
        gcl.addWidget(self.btn_start); gcl.addWidget(self.btn_stop); gcl.addWidget(btn_tray)
        ll.addWidget(gc)

        # 定时
        gsc = QGroupBox("定时运行"); gscl = QVBoxLayout(gsc)
        self.sched_enable = QCheckBox("启用定时运行"); gscl.addWidget(self.sched_enable)
        r = QHBoxLayout(); r.addWidget(QLabel("开始:")); self.time_start = QTimeEdit(QTime(0,0)); self.time_start.setDisplayFormat("HH:mm"); r.addWidget(self.time_start)
        r.addWidget(QLabel("结束:")); self.time_end = QTimeEdit(QTime(8,0)); self.time_end.setDisplayFormat("HH:mm"); r.addWidget(self.time_end); r.addStretch()
        gscl.addLayout(r)
        self.lbl_sched = QLabel("定时未启用"); self.lbl_sched.setStyleSheet("color:#9E9E9E;"); gscl.addWidget(self.lbl_sched)
        ll.addWidget(gsc); ll.addStretch()

        # 右侧日志
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(6,0,0,0)
        glog = QGroupBox("操作日志"); gll = QVBoxLayout(glog)
        h = QHBoxLayout(); h.addStretch()
        btn_clear = QPushButton("清空"); btn_clear.setMaximumWidth(50); btn_clear.clicked.connect(lambda: self.log_text.clear()); h.addWidget(btn_clear)
        gll.addLayout(h)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True); self.log_text.setFont(QFont("Consolas", 10))
        gll.addWidget(self.log_text); rl.addWidget(glog)

        l.addWidget(left); l.addWidget(right, 1)
        return w

    # ===== 帮助 =====
    def _page_help(self):
        w = QWidget(); l = QVBoxLayout(w)
        g = QGroupBox("使用说明"); gl = QVBoxLayout(g)
        txt = QTextEdit(); txt.setReadOnly(True); txt.setFont(QFont("Microsoft YaHei", 11))
        txt.setHtml("""
<h3>MaaTavernBot 使用说明</h3>
<p><b>1. 环境准备</b><br>
MuMu模拟器，分辨率<b>1600×900横屏、DPI 240</b>，开启ADB调试</p>
<p><b>2. 启动</b><br>
输入ADB端口号 → 连接 → 开始。启动自动连接上次端口。</p>
<p><b>3. 功能</b><br>
自动导航、选英雄、升级酒馆、购买随从、打出手牌、使用技能、饰品选择、对局重开。</p>
<p><b>4. 定时运行</b><br>
勾选启用定时 → 设置开始/结束时间 → 到点自动启停。</p>
<p><b>5. 注意事项</b><br>
本软件开源免费，仅供学习交流。使用风险自负。</p>
<p><b>下载/反馈:</b> <a href='https://github.com/hubugui1111-lab/MaaTavernBot'>GitHub</a></p>
""")
        gl.addWidget(txt); l.addWidget(g)
        return w

    # ===== 工具 =====
    def _page_tools(self):
        w = QWidget(); l = QVBoxLayout(w)
        g = QGroupBox("任务管理"); gl = QVBoxLayout(g)
        gl.addWidget(QLabel("自动检测0进度任务并更换。需要 mineru-open-api。"))
        btn = QPushButton("📋 检查并更换任务"); btn.setMinimumHeight(40); btn.clicked.connect(self._quest_reroll)
        gl.addWidget(btn); l.addWidget(g)
        g2 = QGroupBox("更多工具（预留）"); g2l = QVBoxLayout(g2)
        g2l.addWidget(QLabel("即将推出..."))
        l.addWidget(g2); l.addStretch()
        return w

    # ===== 设置 =====
    def _page_settings(self):
        w = QWidget(); l = QVBoxLayout(w)
        g = QGroupBox("ADB 连接"); gl = QVBoxLayout(g)
        r = QHBoxLayout(); r.addWidget(QLabel("端口:"))
        self.port_input = QLineEdit("16416"); self.port_input.setMaximumWidth(120); r.addWidget(self.port_input)
        self.btn_connect = QPushButton("连接"); r.addWidget(self.btn_connect)
        self.conn_status = QLabel("● 未连接"); self.conn_status.setStyleSheet("color:#9E9E9E;font-weight:bold;")
        r.addWidget(self.conn_status); r.addStretch()
        gl.addLayout(r)
        btn_find = QPushButton("🔍 查找设备"); btn_find.clicked.connect(self._list_devices); gl.addWidget(btn_find)
        l.addWidget(g)

        # PushPlus 通知设置
        g_push = QGroupBox("PushPlus 微信通知"); g_push_l = QVBoxLayout(g_push)
        r_tok = QHBoxLayout()
        r_tok.addWidget(QLabel("Token:"))
        self.token_input = QLineEdit("")
        self.token_input.setMaximumWidth(280)
        self.token_input.setPlaceholderText("输入 PushPlus Token 启用掉线/卡住微信通知")
        r_tok.addWidget(self.token_input)
        r_tok.addStretch()
        g_push_l.addLayout(r_tok)
        l.addWidget(g_push)

        g2 = QGroupBox("关于"); g2l = QVBoxLayout(g2)
        g2l.addWidget(QLabel(f"版本: v{self.VERSION}"))
        btn_chk = QPushButton("🔍 检测更新"); btn_chk.clicked.connect(lambda: self._check_update(silent=False)); g2l.addWidget(btn_chk)
        btn_ann = QPushButton("📢 查看公告"); btn_ann.clicked.connect(self._show_announcement); g2l.addWidget(btn_ann)
        l.addWidget(g2); l.addStretch()
        return w

    # ===== Tray =====
    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon_path = os.path.join(self._app_dir, "resource", "tray_icon.png")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            from PySide6.QtGui import QPixmap, QPainter, QColor
            px = QPixmap(32,32); px.fill(Qt.GlobalColor.transparent); p = QPainter(px)
            p.setBrush(QColor("#5D4037")); p.drawRoundedRect(2,2,28,28,6,6); p.end()
            self.tray.setIcon(QIcon(px))
        self.tray.setToolTip("MaaTavernBot v1.5")
        m = QMenu(); m.addAction("显示").triggered.connect(self._show_window)
        m.addAction("退出").triggered.connect(self._quit_app)
        self.tray.setContextMenu(m); self.tray.show()
    def _show_window(self): self.show(); self.activateWindow()
    def _quit_app(self): self._stop(); self.tray.hide(); QApplication.quit()
    def closeEvent(self, e): self._stop(); self.tray.hide(); QApplication.quit()

    # ===== 公告 =====
    def _show_announcement(self, from_startup=False):
        try:
            if from_startup:
                cfg = self._cfg_path()
                if os.path.exists(cfg):
                    try:
                        with open(cfg) as f:
                            if json.load(f).get("announcement_seen") == self.VERSION:
                                return
                    except: pass
            dlg = QDialog(self); dlg.setWindowTitle(f"MaaTavernBot v{self.VERSION} 更新内容")
            dlg.resize(520, 400)
            l = QVBoxLayout(dlg)
            text = QTextEdit(); text.setReadOnly(True); text.setFont(QFont("Microsoft YaHei", 11))
            text.setPlainText(self.CHANGELOG); l.addWidget(text)
            cb = QCheckBox("不再显示此公告"); l.addWidget(cb)
            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok); bb.accepted.connect(dlg.accept); l.addWidget(bb)
            dlg.exec()
            if cb.isChecked():
                cfg = self._cfg_path()
                os.makedirs(os.path.dirname(cfg), exist_ok=True)
                existing = {}
                if os.path.exists(cfg):
                    with open(cfg) as f:
                        existing = json.load(f)
                existing["announcement_seen"] = self.VERSION
                with open(cfg, 'w') as f: json.dump(existing, f)
        except Exception as e:
            self._log(f"[公告] 错误: {e}")

    # ===== 更新检查 =====
    def _check_update(self, silent=False):
        def do():
            try:
                import urllib.request, json, urllib.error, socket
                req = urllib.request.Request(self.GITHUB_API, headers={"User-Agent": "MaaTavernBot/1.5"})
                data = json.loads(urllib.request.urlopen(req, timeout=8).read())
                latest = data.get("tag_name", "").lstrip("v")
                url = data.get("html_url", "https://github.com/hubugui1111-lab/MaaTavernBot/releases/latest")
                if not latest:
                    if not silent:
                        self.log_signal.show_dialog.emit("检测更新", "无法获取最新版本信息")
                    return
                cur_parts = [int(x) for x in self.VERSION.split(".")]
                new_parts = [int(x) for x in latest.split(".")]
                # 补零对齐: 1.5 vs 1.5.0 → [1,5,0] vs [1,5,0]
                max_len = max(len(cur_parts), len(new_parts))
                cur_parts += [0] * (max_len - len(cur_parts))
                new_parts += [0] * (max_len - len(new_parts))
                newer = False
                for c, n in zip(cur_parts, new_parts):
                    if n > c: newer = True; break
                    if n < c: break
                same = cur_parts == new_parts
                if same and not silent:
                    self.log_signal.show_dialog.emit("检测更新", f"当前 v{self.VERSION} 已是最新版本")
                else:
                    title = "发现新版本" if newer else "版本检查"
                    msg = f"当前版本: v{self.VERSION}\n最新版本: v{latest}"
                    if newer: msg += "\n\n是否更新？"
                    self._show_update_dialog_via_signal(title, msg, url)
            except (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError) as e:
                if not silent:
                    self.log_signal.show_dialog.emit("检测更新",
                        "网络不通，无法连接 GitHub\n如需检查更新请开启 VPN 或代理后重试")
            except Exception as e:
                if not silent:
                    self.log_signal.show_dialog.emit("检测更新", f"检查失败: {e}")
        threading.Thread(target=do, daemon=True).start()

    def _show_update_dialog_via_signal(self, title, msg, url):
        """通过信号从后台线程通知主线程显示更新弹窗"""
        # 直接在 do 线程里用 invokeMethod
        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self, "_show_update_dialog",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, title), Q_ARG(str, msg), Q_ARG(str, url)
        )

    # ===== 任务 =====
    def _quest_reroll(self):
        if not self.controller: self._log("[任务] 请先连接"); return
        self._log("[任务] 开始检查...")
        def do():
            try:
                from bot.quest_reroll import QuestReroll
                qr = QuestReroll()
                old_stdout = sys.stdout
                sys.stdout = GuiLogStream(self.log_signal)
                try: qr.do_reroll(self.controller)
                finally: sys.stdout = old_stdout
            except Exception as e: self.log_signal.new_log.emit(f"[任务] {e}")
        threading.Thread(target=do, daemon=True).start()

    # ===== 连接 =====
    def _list_devices(self):
        self._log("查找设备...")
        def f():
            try:
                from maa.toolkit import Toolkit; self._maa_init()
                for d in Toolkit.find_adb_devices(): self.log_signal.new_log.emit(f"  {d.address}")
            except Exception as e: self.log_signal.new_log.emit(f"[错误] {e}")
        threading.Thread(target=f, daemon=True).start()

    def _auto_connect(self):
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            cfg = os.path.join(exe_dir, '.maa', 'last_port.txt')
            if os.path.exists(cfg):
                with open(cfg) as f: self.port_input.setText(f.read().strip())
            port = self.port_input.text().strip()
            if port: self._log(f"自动连接 127.0.0.1:{port} ..."); self._connect()
        except: pass

    def _connect(self):
        port = self.port_input.text().strip()
        if not port: self._log("[错误] 请输入端口号"); return
        self.btn_connect.setEnabled(False); self._log(f"连接 {port}...")
        def do():
            try:
                from maa.toolkit import Toolkit; from maa.controller import AdbController
                from maa.resource import Resource; from maa.tasker import Tasker
                from bot.phase_detector import PhaseDetector; from bot.game_bot import BotAction
                self._maa_init()
                devices = Toolkit.find_adb_devices()
                device = None
                for d in devices:
                    if port in d.address: device = d; break
                if not device: self.log_signal.new_log.emit(f"[错误] 未找到端口 {port}"); self.log_signal.conn_fail.emit(); return
                self.controller = AdbController(adb_path=device.adb_path, address=device.address, screencap_methods=device.screencap_methods, input_methods=device.input_methods, config=device.config)
                self.controller.post_connection().wait()
                if not self.controller.connected: self.log_signal.new_log.emit("[错误] 连接失败"); self.log_signal.conn_fail.emit(); return
                BotAction.adb_device = device.address
                app_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
                res = Resource(); res.post_bundle(os.path.join(app_dir, 'resource')).wait()
                res.register_custom_recognition('PhaseDetector', PhaseDetector())
                self.bot_action = BotAction(); res.register_custom_action('BotAction', self.bot_action)
                self.tasker = Tasker(); self.tasker.bind(res, self.controller)
                if not self.tasker.inited: self.log_signal.new_log.emit("[错误] 初始化失败"); self.log_signal.conn_fail.emit(); return
                self.connected = True; self._save_port(port)
                # 加载 PushPlus token
                try:
                    import json
                    cfg_path = self._cfg_path()
                    if os.path.exists(cfg_path):
                        with open(cfg_path) as f:
                            tok = json.load(f).get("pushplus_token", "")
                            self.token_input.setText(tok)
                            from bot.notify import set_token
                            set_token(tok)
                except: pass
                self.log_signal.new_log.emit("[信息] 连接成功"); self.log_signal.conn_ok.emit()
            except Exception as e: self.log_signal.new_log.emit(f"[错误] {e}"); self.log_signal.conn_fail.emit()
        threading.Thread(target=do, daemon=True).start()

    def _save_port(self, port):
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            os.makedirs(os.path.join(exe_dir, '.maa'), exist_ok=True)
            with open(os.path.join(exe_dir, '.maa', 'last_port.txt'), 'w') as f: f.write(str(port))
        except: pass

    def _maa_init(self):
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        from maa.toolkit import Toolkit
        os.makedirs(os.path.join(exe_dir, '.maa'), exist_ok=True); Toolkit.init_option(os.path.join(exe_dir, '.maa'))

    def _cfg_path(self):
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        return os.path.join(exe_dir, '.maa', 'config.json')

    # ===== 开始/停止 =====
    def _start(self):
        if not self.tasker: self._log("[错误] 请先连接"); return
        if self.running: self._log("[警告] 已在运行中"); return
        # 保存 PushPlus token (读-改-写，不冲掉其他配置)
        try:
            import json
            tok = self.token_input.text().strip()
            cfg = {}
            cfg_path = self._cfg_path()
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    cfg = json.load(f)
            cfg["pushplus_token"] = tok
            with open(cfg_path, 'w') as f:
                json.dump(cfg, f)
            from bot.notify import set_token
            set_token(tok)
        except: pass
        self.btn_start.setEnabled(False); self.btn_stop.setEnabled(True); self.running = True
        self.lbl_running.setText("● 运行中"); self.lbl_running.setProperty("status", "running"); self.lbl_running.style().unpolish(self.lbl_running); self.lbl_running.style().polish(self.lbl_running)
        self._log("检测游戏状态..."); self._orig_stdout = sys.stdout; sys.stdout = GuiLogStream(self.log_signal)
        def do():
            try:
                from bot.phase_detector import PhaseDetector
                detector = PhaseDetector(); known = {"main_menu","mode_select","bg_lobby","hero_select","recruit","game_end"}
                self.log_signal.new_log.emit("[启动] 截图...")
                img = self.controller.post_screencap().wait().get()
                self.log_signal.new_log.emit("[启动] 检测阶段...")
                phase = detector.analyze(None, type('a',(),{'image':img})()).detail.get("phase","combat")
                self.log_signal.new_log.emit(f"[启动] 当前阶段: {phase}")
            except Exception as e:
                self.log_signal.new_log.emit(f"[启动] 错误: {e}")
                self.running = False
                if hasattr(self, '_orig_stdout'): sys.stdout = self._orig_stdout
                # 截图失败 → PushPlus 掉线通知
                try:
                    from bot.notify import send_alert
                    send_alert("掉线", f"Bot 启动失败，可能已断开<br>错误: {e}<br>时间: {__import__('time').strftime('%H:%M:%S')}")
                except: pass
                self.log_signal.start_fail.emit()
                return
            if phase not in known:
                self.log_signal.new_log.emit("启动游戏...")
                self.controller.post_start_app("com.blizzard.wtcg.hearthstone").wait()
                for i in range(24):
                    time.sleep(5); img = self.controller.post_screencap().wait().get()
                    p = detector.analyze(None, type('a',(),{'image':img})()).detail.get("phase","combat")
                    self.log_signal.new_log.emit(f"  {(i+1)*5}s: {p}")
                    if p in known: break
            self.tasker.post_task("MainLoop"); self.log_signal.new_log.emit("[信息] Bot 启动")
        threading.Thread(target=do, daemon=True).start()

    def _stop(self, close_game=False):
        self.running = False; self.btn_stop.setEnabled(False)
        self.lbl_running.setText("● 已停止"); self.lbl_running.setProperty("status", "stopped"); self.lbl_running.style().unpolish(self.lbl_running); self.lbl_running.style().polish(self.lbl_running)
        self._log("停止中...")
        if hasattr(self, '_orig_stdout'): sys.stdout = self._orig_stdout
        def do():
            if self.tasker: self.tasker.post_stop().wait()
            self.btn_start.setEnabled(True); self.log_signal.new_log.emit("[信息] 已停止")
            if close_game:
                try:
                    from bot.game_bot import BotAction
                    if BotAction.adb_device:
                        import subprocess
                        subprocess.run(f'"D:/MuMuPlayer/nx_main/adb.exe" -s {BotAction.adb_device} shell "am force-stop com.blizzard.wtcg.hearthstone"', shell=True, timeout=5)
                except: pass
        threading.Thread(target=do, daemon=True).start()

    def _check_schedule(self):
        if not self.sched_enable.isChecked(): self.lbl_sched.setText("定时未启用"); return
        now = datetime.now().time(); st, et = self.time_start.time().toPython(), self.time_end.time().toPython()
        in_range = (st <= now <= et) if st <= et else (now >= st or now <= et)
        if in_range and not self.running:
            if self.connected: self._start(); self.lbl_sched.setText(f"自动开始 {now:%H:%M}")
            else: self.lbl_sched.setText("等待连接...")
        elif not in_range and self.running: self._stop(close_game=True); self.lbl_sched.setText(f"自动停止 {now:%H:%M}")
        elif in_range and self.running: self.lbl_sched.setText(f"运行中 {now:%H:%M}")
        else: self.lbl_sched.setText(f"等待 {now:%H:%M}")

    def _log(self, msg): self.log_signal.new_log.emit(msg)
    def _append_log(self, msg): self.log_text.append(f"{datetime.now():%H:%M:%S} {msg}")
    def _refresh_status(self):
        if hasattr(self, 'bot_action') and self.bot_action and self.running:
            self.lbl_phase.setText(f"阶段: {self.bot_action.last_phase}")
            self.lbl_turn.setText(f"回合: {self.bot_action.turn_number}")

    def _show_info_dialog(self, title, msg):
        QMessageBox.information(self, title, msg)

    @Slot(str, str, str)
    def _show_update_dialog(self, title, msg, url):
        mb = QMessageBox(self); mb.setWindowTitle(title); mb.setText(msg)
        mb.addButton("更新", QMessageBox.ButtonRole.AcceptRole)
        mb.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        if mb.exec() == 0:
            QDesktopServices.openUrl(QUrl(url))

    def _connect_signals(self):
        self.btn_connect.clicked.connect(self._connect)
        self.btn_start.clicked.connect(self._start); self.btn_stop.clicked.connect(self._stop)
        self.log_signal.new_log.connect(self._append_log)
        self.log_signal.show_dialog.connect(lambda t,m: QMessageBox.information(self, t, m))
        self.log_signal.conn_ok.connect(self._on_conn_ok)
        self.log_signal.conn_fail.connect(self._on_conn_fail)
        self.log_signal.start_fail.connect(self._on_start_fail)
        self.sched_enable.toggled.connect(lambda: self._check_schedule())
        self.time_start.timeChanged.connect(lambda: self._check_schedule())
        self.time_end.timeChanged.connect(lambda: self._check_schedule())

    def _on_conn_ok(self):
        self.conn_status.setText("● 已连接"); self.conn_status.setStyleSheet("color:#4CAF50;font-weight:bold;")

    def _on_conn_fail(self):
        self.btn_connect.setEnabled(True)

    def _on_start_fail(self):
        self.btn_start.setEnabled(True); self.btn_stop.setEnabled(False)
        self.lbl_running.setText("● 已停止"); self.lbl_running.setProperty("status", "stopped"); self.lbl_running.style().unpolish(self.lbl_running); self.lbl_running.style().polish(self.lbl_running)

    def _minimize_to_tray(self): self.hide(); self._log("已最小化到托盘")


def main():
    app = QApplication(sys.argv); app.setStyle("Fusion")
    # 加载炉石酒馆 QSS 样式
    app_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(app_dir, "resource", "tavern.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    app.setQuitOnLastWindowClosed(False)
    BotGUI().show(); sys.exit(app.exec())

if __name__ == "__main__": main()
