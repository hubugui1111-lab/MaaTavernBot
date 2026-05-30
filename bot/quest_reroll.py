"""任务更换 —— 本地模板匹配导航 + MinerU OCR"""

import time, random, re, subprocess, os, cv2

MINERU = r"C:\Users\lenovo\AppData\Roaming\npm\mineru-open-api.cmd"
CHECK_HOURS = 4
QUEST_BTN = (330, 645)  # mode_select 底部任务图标（商店右边、开包左边）
QUEST_SIDEBAR = (234, 245)  # 任务中心左边栏第2个按钮（歪感叹号）→ 真正任务界面


class QuestReroll:
    def __init__(self):
        self.runtime = 0; self.last = time.time()

    def should_check(self):
        self.runtime += time.time() - self.last; self.last = time.time()
        if self.runtime > CHECK_HOURS * 3600: self.runtime = 0; return True
        return False

    def _ocr(self, path):
        """MinerU OCR: 截图 → 文字。输出是 UTF-8 Markdown，取 stdout"""
        try:
            r = subprocess.run(
                f'"{MINERU}" extract "{path}"',
                capture_output=True, timeout=120, shell=True,
            )
            # MinerU 输出 UTF-8，stdout 包含 <details> 格式的识别文字
            raw = (r.stdout or b"").decode("utf-8", errors="replace")
            # stderr 只有 "Thinking..." "Done" 等状态，不含文字
            return raw
        except Exception:
            return ""

    def _go_main_menu(self, ctrl):
        """用模板匹配识别画面并返回主菜单"""
        from .screen_match import identify_screen, BACK_BUTTONS
        for _ in range(20):
            img = ctrl.post_screencap().wait().get()
            name, sc = identify_screen(img)
            print(f"[导航] {name} sc={sc:.2f}")
            if name in ("main_menu", "mode_select"):
                return True
            bx, by = BACK_BUTTONS.get(name, (60, 60))
            if bx:
                ctrl.post_click(bx, by).wait()
                time.sleep(1)
        return False

    def do_reroll(self, ctrl):
        print("[任务] 返回主菜单...")
        if not self._go_main_menu(ctrl):
            print("[任务] 导航失败"); return

        print(f"[任务] 点任务按钮 ({QUEST_BTN})")
        ctrl.post_click(*QUEST_BTN).wait()
        time.sleep(2)

        # 进入任务中心后，点左边栏第2个按钮进入真正任务界面
        print(f"[任务] 点任务侧边栏 ({QUEST_SIDEBAR})")
        ctrl.post_click(*QUEST_SIDEBAR).wait()
        time.sleep(2)

        img = ctrl.post_screencap().wait().get()
        tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "quest_ocr.png")
        cv2.imwrite(tmp, img)

        text = self._ocr(tmp) or ""
        all_quests = [{"progress": int(m.group(1)), "quota": int(m.group(2))}
                      for m in re.finditer(r"(\d+)\s*/\s*(\d+)", text) if 0 < int(m.group(2)) <= 5000]
        # 只取前3个（日常任务），过滤活动和每周任务
        quests = all_quests[:3]
        zero = [q for q in quests if q["progress"] == 0]
        print(f"[任务] {len(quests)}个日常, {len(zero)}个零进度 (共识别{len(all_quests)}个)")

        if zero:
            idx = quests.index(random.choice(zero))
            # 三个刷新箭头在同一水平线 y≈185（屏幕上半），从左到右三列
            # 通过 R 通道金/橙色检测定位，用户确认绿框位置
            refresh_arrows = [(474, 191), (646, 191), (818, 191)]
            if idx < len(refresh_arrows):
                ax, ay = refresh_arrows[idx]
                for dx in range(-5, 10, 3):
                    ctrl.post_click(ax + dx, ay).wait()
                    time.sleep(0.12)
            print(f"[任务] 已尝试更换第 {idx} 个任务")

        self._go_main_menu(ctrl)
        print("[任务] 完成")
