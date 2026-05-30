"""游戏主循环 —— 根据当前阶段执行对应操作"""

import os
import sys
import time
import random
import subprocess
import cv2
import numpy as np
from maa.custom_action import CustomAction
from .screen_regions import (
    scale_coords, rect_center,
    MODE_BG_BTN,
    HERO_SELECT_SECOND, HERO_CONFIRM_BTN,
    GAME_END_TAP_RECT,
    BUY_FROM_RECTS, BUY_TO_RECT,
    HAND_CARD_RECTS, PLAY_TO_RECT,
    SELL_FROM_RECT, SELL_TO_RECT,
    HERO_POWER_RECT, TRIPLE_RECT,
    TAVERN_REFRESH_RECT, POPUP_CHOICE_RECT,
    SKIP_DARKMOON_RECT, POPUP_OK_RECTS,
    CLICK_ANYWHERE,
)

# exe 环境下的日志文件
def _log(msg):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_debug.log"), "a") as f:
            f.write(f"{msg}\n")
    except:
        pass


class BotAction(CustomAction):
    """核心自定义动作，包含完整的游戏循环逻辑。"""

    # ADB 设备地址（由 main.py 设置）
    adb_device = None

    def __init__(self):
        super().__init__()
        self.turn_number = 0
        self.tavern_tier = 1
        self.last_phase = "unknown"
        self._templates = {}
        self._recruit_done = False
        self._recruit_enter_time = 0
        self._hero_done = False  # 英雄选择只执行一次
        self._same_phase_count = 0
        self._stuck_level = 0  # 卡住级别: 0=正常 1=2分钟自救过 2=5分钟重启过

    @staticmethod
    def _adb_shell(cmd):
        """通过 ADB shell 执行命令"""
        if not BotAction.adb_device:
            return False
        try:
            # 用 MuMu 自带的 ADB，路径固定
            adb_path = "D:/MuMuPlayer/nx_main/adb.exe"
            full_cmd = f'"{adb_path}" -s {BotAction.adb_device} shell "{cmd}"'
            result = subprocess.run(full_cmd, shell=True, timeout=5,
                          capture_output=True)
            if result.returncode != 0:
                _log(f"ADB错误: {result.stderr.decode()[:100]}")
            return result.returncode == 0
        except Exception as e:
            _log(f"ADB异常: {e}")
            return False

    @classmethod
    def _adb_tap(cls, x, y):
        """ADB 点击（带随机偏移）"""
        rx = x + random.randint(-5, 5)
        ry = y + random.randint(-5, 5)
        return cls._adb_shell(f"input tap {rx} {ry}")

    @classmethod
    def _adb_swipe(cls, x1, y1, x2, y2, duration=300):
        """ADB 拖拽（带随机偏移）"""
        rx1 = x1 + random.randint(-5, 5)
        ry1 = y1 + random.randint(-5, 5)
        rx2 = x2 + random.randint(-10, 10)
        ry2 = y2 + random.randint(-10, 10)
        d = duration + random.randint(0, 100)
        return cls._adb_shell(f"input swipe {rx1} {ry1} {rx2} {ry2} {d}")

    def _load_template(self, name):
        """加载模板图片"""
        if name in self._templates:
            return self._templates[name]

        # 优先从模块路径查找，失败则从工作目录查找
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(module_dir, "resource", "image", name)
        if not os.path.exists(path):
            # PyInstaller 环境下备用路径
            path = os.path.join("resource", "image", name)
        if os.path.exists(path):
            img = cv2.imread(path)
            if img is not None:
                self._templates[name] = img
                _log(f"模板加载成功: {path}")
                return img
            _log(f"模板读取失败: {path}")
        else:
            _log(f"模板文件不存在: {path}, module_dir={module_dir}")
        return None

    def _find_button(self, screenshot, template_name, threshold=0.75):
        """在截图中用模板匹配找到按钮位置，返回中心坐标或 None"""
        template = self._load_template(template_name)
        if template is None:
            return None
        th, tw = template.shape[:2]
        sh, sw = screenshot.shape[:2]
        if th > sh or tw > sw:
            return None
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            cx = max_loc[0] + tw // 2
            cy = max_loc[1] + th // 2
            return (cx, cy, max_val)
        return None

    # ---- 主入口 ----

    def run(self, context, argv):
        # 检查停止信号
        if context.tasker.stopping:
            return True

        reco_detail = argv.reco_detail
        if reco_detail and reco_detail.best_result:
            phase = reco_detail.best_result.detail.get("phase", "combat")
        else:
            phase = "combat"

        if phase != self.last_phase:
            print(f"[阶段] {self.last_phase} -> {phase}")
            _log(f"[阶段] {self.last_phase} -> {phase}")
            self.last_phase = phase
            self._same_phase_count = 0
            self._stuck_level = 0
            if phase == "recruit":
                self._recruit_done = False
                self._recruit_enter_time = time.time()
            elif phase == "game_end":
                self._hero_done = False  # 只有对局结束才重置
        else:
            self._same_phase_count += 1

        # === 卡住检测 ===
        if self._same_phase_count > 240 and self._stuck_level == 0:
            _log(f"[卡住] 在 {phase} 2分钟，尝试自救...")
            self._same_phase_count = 0
            self._stuck_level = 1
            self._handle_stuck(context, phase)
        elif self._same_phase_count > 600 and self._stuck_level >= 1:
            _log(f"[卡住] 在 {phase} 5分钟，重启游戏...")
            self._same_phase_count = 0
            self._stuck_level = 2
            self._restart_game()

        handlers = {
            "main_menu": self._handle_main_menu,
            "mode_select": self._handle_mode_select,
            "bg_lobby": self._handle_bg_lobby,
            "hero_select": self._handle_hero_select,
            "recruit": self._handle_recruit,
            "combat": self._handle_combat,
            "game_end": self._handle_game_end,
            "loading": self._handle_combat,  # 加载/等待画面 = 等待
        }
        handler = handlers.get(phase)
        if handler:
            handler(context)

        return True

    # ---- 导航 ----

    def _handle_main_menu(self, context):
        """主菜单——点击进入模式选择"""
        img = context.tasker.controller.post_screencap().wait().get()
        x, y = scale_coords(img, (640, 360))[0]
        context.tasker.controller.post_click(x, y).wait()
        time.sleep(1.0)

    def _handle_mode_select(self, context):
        """模式选择——用模板匹配找到酒馆战旗入口并点击"""
        img = context.tasker.controller.post_screencap().wait().get()
        result = self._find_button(img, "bg_mode_btn.png")
        if result:
            x, y, score = result
            print(f"[导航] 模板匹配找到酒馆战旗 ({x}, {y}) 置信度={score:.2f}")
            context.tasker.controller.post_click(x, y).wait()
        else:
            print("[导航] 未找到酒馆战旗入口，用固定坐标兜底")
            x, y = scale_coords(img, MODE_BG_BTN)[0]
            context.tasker.controller.post_click(x, y).wait()
        time.sleep(1.5)

    def _handle_bg_lobby(self, context):
        """酒馆战旗大厅——用模板匹配找到开始按钮并点击"""
        img = context.tasker.controller.post_screencap().wait().get()
        result = self._find_button(img, "bg_start_btn.png")
        if result:
            x, y, score = result
            print(f"[导航] 模板匹配找到开始按钮 ({x}, {y}) 置信度={score:.2f}")
            context.tasker.controller.post_click(x, y).wait()
        else:
            print("[导航] 未找到开始按钮，用固定坐标兜底")
            x, y = scale_coords(img, (960, 570))[0]
            context.tasker.controller.post_click(x, y).wait()
        time.sleep(2.0)

    def _handle_hero_select(self, context):
        """英雄选择——选第2个英雄+确认（仅一次）"""
        if self._hero_done:
            return
        self._hero_done = True

        ctrl = context.tasker.controller
        img = ctrl.post_screencap().wait().get()
        hx, hy = scale_coords(img, HERO_SELECT_SECOND)[0]
        cx, cy = scale_coords(img, HERO_CONFIRM_BTN)[0]
        _log(f"[英雄] 选 ({hx},{hy}) 确认 ({cx},{cy})")
        print(f"[导航] 选择第2个英雄 ({hx}, {hy})")
        ctrl.post_click(hx, hy).wait()
        time.sleep(1.0)
        print(f"[导航] 确认选择 ({cx}, {cy})")
        ctrl.post_click(cx, cy).wait()
        _log("[英雄] 完成")

    # ---- 游戏阶段 ----

    def _handle_recruit(self, context):
        """招募阶段——执行回合操作（仅一次）"""
        if self._recruit_done:
            return
        if context.tasker.stopping:
            return

        elapsed = time.time() - self._recruit_enter_time
        if elapsed < 3.0:
            return

        self._recruit_done = True
        self.turn_number += 1
        ctrl = context.tasker.controller

        _log(f"[回合{self.turn_number}] === 开始 ===")
        img = ctrl.post_screencap().wait().get()

        # === 步骤0: 饰品检测 ===
        tpl = self._load_template("tavern_upgrade_btn.png")
        upgrade_score = 0.0
        if tpl is not None:
            r = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
            upgrade_score, _, _, _ = cv2.minMaxLoc(r)
        _log(f"[回合{self.turn_number}] 升级分数={upgrade_score:.2f}")

        # 升级按钮分数低可能是饰品回合
        if upgrade_score < 0.6:
            self._try_select_trinket(ctrl)
            time.sleep(0.5)
            img = ctrl.post_screencap().wait().get()

        # === 步骤1: 升级酒馆 (m16) ===
        if tpl is not None:
            r = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(r)
            cx, cy = ml[0] + tpl.shape[1] // 2, ml[1] + tpl.shape[0] // 2
            _log(f"[回合{self.turn_number}] 升级分数={mv:.2f}")
            if mv >= 0.70:
                msg = f"[回合{self.turn_number}] 升级酒馆 sc={mv:.2f}"
                print(msg); _log(msg)
                ctrl.post_click(cx, cy).wait()
                time.sleep(random.randint(100, 300) / 1000)
            else:
                rx, ry = rect_center(TAVERN_REFRESH_RECT)
                _log(f"[刷新] ({rx},{ry})")
                ctrl.post_click(rx, ry).wait()
                time.sleep(random.randint(100, 300) / 1000)

        # === 步骤1.5: 弹窗处理 ===
        self._dismiss_popups(ctrl)

        # === 步骤2: 购买随从 (m37) ===
        to_cx, to_cy = rect_center(BUY_TO_RECT)
        for rect in BUY_FROM_RECTS:
            fx, fy = rect_center(rect)
            _log(f"[购买] 拖拽 ({fx},{fy}) -> ({to_cx},{to_cy})")
            ctrl.post_swipe(fx, fy, to_cx, to_cy, 500).wait()
            time.sleep(1.0)

        # === 步骤3: 打出手牌 - 循环直到手牌清空或超过5次 ===
        play_to_cx, play_to_cy = rect_center(PLAY_TO_RECT)
        for loop in range(5):
            if context.tasker.stopping:
                break
            _log(f"[打牌] 第{loop+1}轮")
            for rect in HAND_CARD_RECTS:
                fx, fy = rect_center(rect)
                ctrl.post_swipe(fx, fy, play_to_cx, play_to_cy, 500).wait()
                time.sleep(1.0)
            # 处理发现弹窗
            ctrl.post_click(play_to_cx, play_to_cy).wait()
            time.sleep(0.3)
            # 检查升级分数是否提高（金币花了）
            gs = self._read_gold(context)
            _log(f"[打牌] 升级分: '{gs}'")
            if gs and "upgrade=" in gs and float(gs.split("=")[1]) > 0.5:
                _log("[打牌] 金币已花，停止循环")
                break

        # === 处理战吼/法术选目标: 点击一个我方随从 ===
        board_minions = self._find_board_minions(img)
        if board_minions and len(board_minions) > 0:
            tx, ty = random.choice(board_minions)
            _log(f"[目标] 选随从 ({tx},{ty}) (共{len(board_minions)}个)")
            ctrl.post_click(tx, ty).wait()
            time.sleep(0.3)

        # === 步骤4: 英雄技能 (按照 5B: 金币花完后使用) ===
        hx, hy = rect_center(HERO_POWER_RECT)
        _log(f"[英雄技能] 点击 ({hx},{hy})")
        ctrl.post_click(hx, hy).wait()
        time.sleep(random.randint(100, 300) / 1000)

        # === 步骤5: 处理三连弹窗 (m2431) ===
        tx, ty = rect_center(TRIPLE_RECT)
        ctrl.post_click(tx, ty).wait()
        time.sleep(0.2)

        # === 步骤6: 出售随从 (m14) ===
        # 打出后出售最右边随从腾空间（每回合50%概率执行）
        if self.turn_number > 2 and random.random() < 0.5:
            sx, sy = rect_center(SELL_FROM_RECT)
            ex, ey = rect_center(SELL_TO_RECT)
            _log(f"[出售] 拖拽 ({sx},{sy}) -> ({ex},{ey})")
            ctrl.post_swipe(sx, sy, ex, ey, 500).wait()
            time.sleep(1.0)
            time.sleep(random.randint(100, 300) / 1000)

        # === 校验：如果升级分数还是很低(金币没花)，重做购买打牌 ===
        after_score_text = self._read_gold(context)
        _log(f"[回合{self.turn_number}] 操作后升级分数: '{after_score_text}'")
        if after_score_text and "upgrade=" in after_score_text:
            try:
                after_score = float(after_score_text.split("=")[1])
                if after_score < 0.5 and upgrade_score < 0.5:
                    _log(f"[回合{self.turn_number}] 金币未花，重做购买打牌")
                    bt_x, bt_y = rect_center(BUY_TO_RECT)
                    for rect in BUY_FROM_RECTS:
                        fx, fy = rect_center(rect)
                        ctrl.post_swipe(fx, fy, bt_x, bt_y, 500).wait()
                        time.sleep(1.0)
                    pt_x, pt_y = rect_center(PLAY_TO_RECT)
                    for rect in HAND_CARD_RECTS:
                        fx, fy = rect_center(rect)
                        ctrl.post_swipe(fx, fy, pt_x, pt_y, 500).wait()
                        time.sleep(1.0)
            except:
                pass

        _log(f"[回合{self.turn_number}] === 完成 ===")

    def _dismiss_popups(self, ctrl):
        """处理各种弹窗（发现/暗月宝藏/免费英雄/无法继续等）"""
        # 发现弹窗 (m2321)
        cx, cy = rect_center(POPUP_CHOICE_RECT)
        ctrl.post_click(cx, cy).wait()
        time.sleep(0.2)

        # 暗月宝藏跳过 (m39)
        sx, sy = rect_center(SKIP_DARKMOON_RECT)
        ctrl.post_click(sx, sy).wait()
        time.sleep(0.2)

        # 各种确定弹窗 (m29_/m25/m26/m18)
        for rect in POPUP_OK_RECTS:
            ox, oy = rect_center(rect)
            ctrl.post_click(ox, oy).wait()
            time.sleep(0.1)

        # 点击任意位置关闭其他弹窗 (m30)
        cx_any, cy_any = CLICK_ANYWHERE
        ctrl.post_click(cx_any, cy_any).wait()

    def _try_select_trinket(self, ctrl):
        """随机选饰品 + 确认"""
        from .screen_regions import TRINKET_RECTS, TRINKET_CONFIRM_RECT
        idx = random.randint(0, len(TRINKET_RECTS) - 1)
        tx, ty = rect_center(TRINKET_RECTS[idx])
        _log(f"[饰品] 选第{idx+1}个 ({tx},{ty})")
        ctrl.post_click(tx, ty).wait()
        time.sleep(0.8)  # 等动画
        cx, cy = rect_center(TRINKET_CONFIRM_RECT)
        _log(f"[饰品] 确认 ({cx},{cy})")
        ctrl.post_click(cx, cy).wait()
        time.sleep(0.8)  # 等关闭

    def _find_board_minions(self, img):
        """蓝框检测我方场上随从，返回[(x,y),...]"""
        board = img[360:450, 80:1200]
        hsv = cv2.cvtColor(board, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([90,50,50]), np.array([140,255,255]))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 300 < area < 5000:
                x, y, rw, rh = cv2.boundingRect(cnt)
                if 30 < rw < 100 and 30 < rh < 100:
                    regions.append((x + rw//2 + 80, y + rh//2 + 360))
        clusters = []
        for cx, cy in sorted(regions):
            merged = False
            for c in clusters:
                if abs(cx - c[-1][0]) < 60:
                    c.append((cx,cy))
                    merged = True
                    break
            if not merged:
                clusters.append([(cx,cy)])
        return [(int(sum(p[0] for p in c)/len(c)), int(sum(p[1] for p in c)/len(c))) for c in clusters]

    def _read_gold(self, context):
        """用升级按钮模板匹配分数间接判断金币是否花掉——分数变高说明金币花了"""
        try:
            img = context.tasker.controller.post_screencap().wait().get()
            tpl = self._load_template("tavern_upgrade_btn.png")
            if tpl is not None:
                r = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
                score, _, _, _ = cv2.minMaxLoc(r)
                return f"upgrade={score:.2f}"
        except:
            pass
        return ""

    def _restart_game(self):
        """强制重启炉石传说"""
        _log("[重启] 强制关闭游戏...")
        try:
            self._adb_shell("am force-stop com.blizzard.wtcg.hearthstone")
            time.sleep(3)
            _log("[重启] 重新启动游戏...")
            self._adb_shell("am start -n com.blizzard.wtcg.hearthstone/.Startup")
            time.sleep(10)
            _log("[重启] 游戏已重启")
        except Exception as e:
            _log(f"[重启] 失败: {e}")

    def _handle_stuck(self, context, phase):
        """卡住自救：OCR 搜索返回 → 模板匹配 → 位置兜底 → 重启"""
        ctrl = context.tasker.controller
        img = ctrl.post_screencap().wait().get()
        h, w = img.shape[:2]

        # 尝试1: OCR 全屏搜索"返回"文字
        _log("[自救] OCR 搜索'返回'...")
        found = self._ocr_find_and_click(context, img, "返回")
        if found:
            time.sleep(3)
            return

        # 尝试2: 模板匹配
        for tpl_name in ["back_btn.png", "bg_start_btn.png"]:
            result = self._find_button(img, tpl_name, threshold=0.7)
            if result:
                x, y, sc = result
                _log(f"[自救] 模板匹配 ({x},{y}) sc={sc:.2f}")
                ctrl.post_click(x, y).wait()
                time.sleep(3)
                return

        # 尝试3: 位置兜底
        positions = [(60,60), (w-100, h-100), (w-60, 60), (60, h-100)]
        for bx, by in positions:
            _log(f"[自救] 尝试 ({bx},{by})")
            ctrl.post_click(bx, by).wait()
            time.sleep(1.0)
        time.sleep(5)

        # 尝试4: 重启游戏
        _log("[自救] 重启游戏...")
        try:
            from subprocess import run
            adb = "D:/MuMuPlayer/nx_main/adb.exe"
            run(f'\"{adb}\" -s {BotAction.adb_device} shell "am force-stop com.blizzard.wtcg.hearthstone"', shell=True, timeout=5)
            time.sleep(3)
            ctrl.post_start_app("com.blizzard.wtcg.hearthstone").wait()
            time.sleep(10)
            _log("[自救] 游戏已重启")
        except Exception as e:
            _log(f"[自救] 重启失败: {e}")

    def _ocr_find_and_click(self, context, img, keyword):
        """用 MaaFramework OCR 搜索指定文字并点击"""
        try:
            result = context.run_recognition("OCRFinder", img, {
                "OCRFinder": {
                    "recognition": "OCR",
                    "expected": keyword,
                    "roi": [0, 0, img.shape[1], img.shape[0]],
                }
            })
            if result and result.hit and result.best_result:
                box = result.best_result.box
                cx, cy = box[0] + box[2] // 2, box[1] + box[3] // 2
                _log(f"[OCR] 找到'{keyword}' at ({cx},{cy})")
                context.tasker.controller.post_click(cx, cy).wait()
                return True
        except Exception as e:
            _log(f"[OCR] 搜索失败: {e}")
        return False

    def _handle_combat(self, context):
        """战斗阶段——等待 + 处理发现弹窗"""
        ctrl = context.tasker.controller
        # 处理抉择/发现弹窗 (m2321 + m2431)
        cx, cy = rect_center(POPUP_CHOICE_RECT)
        ctrl.post_click(cx, cy).wait()
        time.sleep(0.2)
        tx, ty = rect_center(TRIPLE_RECT)
        ctrl.post_click(tx, ty).wait()

    def _handle_game_end(self, context):
        """对局结算——点击退出"""
        self.turn_number = 0
        self.tavern_tier = 1
        img = context.tasker.controller.post_screencap().wait().get()
        x, y = rect_center(GAME_END_TAP_RECT)
        print(f"[结算] 对局结束，点击退出 ({x}, {y})")
        context.tasker.controller.post_click(x, y).wait()
        time.sleep(1.5)
