"""任务自动更换——MinerU OCR + 红色按钮检测"""

import time, random, re, subprocess, os, cv2, numpy as np

CHECK_INTERVAL_HOURS = 4


class QuestReroll:
    def __init__(self):
        self.runtime_seconds = 0
        self.last_check = time.time()

    def should_check(self):
        self.runtime_seconds += (time.time() - self.last_check)
        self.last_check = time.time()
        if self.runtime_seconds > CHECK_INTERVAL_HOURS * 3600:
            self.runtime_seconds = 0
            return True
        return False

    def _ocr_text(self, img_path):
        try:
            r = subprocess.run(
                ["mineru-open-api", "extract", img_path],
                capture_output=True, text=True, timeout=120
            )
            return r.stdout
        except:
            return ""

    def _parse_quests(self, text):
        quests = []
        for line in text.split('\n'):
            line = line.strip()
            m = re.match(r'(\d+)\s*/\s*(\d+)', line)
            if m:
                prog, quota = int(m.group(1)), int(m.group(2))
                if quota > 0:
                    quests.append({'progress': prog, 'quota': quota})
        return quests

    def _find_red_buttons(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        red = cv2.bitwise_or(
            cv2.inRange(hsv, np.array([0,100,100]), np.array([10,255,255])),
            cv2.inRange(hsv, np.array([160,100,100]), np.array([180,255,255]))
        )
        roi = red[200:600, 1150:1280]
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ys = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 2000:
                _, y, _, _ = cv2.boundingRect(cnt)
                ys.append(y + 200)

        clusters = []
        for y in sorted(ys):
            merged = False
            for c in clusters:
                if abs(y - c) < 30:
                    clusters[clusters.index(c)] = (c + y) // 2
                    merged = True; break
            if not merged:
                clusters.append(y)
        return sorted(clusters)

    def open_quest_screen(self, ctrl):
        ctrl.post_click(330, 660).wait()
        time.sleep(1.5)

    def close_quest_screen(self, ctrl):
        ctrl.post_click(60, 60).wait()
        time.sleep(1.0)

    def try_reroll(self, context):
        if not self.should_check():
            return

        ctrl = context.tasker.controller
        print("[任务] 检查是否需要更换...")

        self.open_quest_screen(ctrl)

        img = ctrl.post_screencap().wait().get()
        path = 'C:/Users/lenovo/AppData/Local/Temp/quest_check.png'
        cv2.imwrite(path, img)

        text = self._ocr_text(path)
        quests = self._parse_quests(text)
        zero_quests = [q for q in quests if q['progress'] == 0]
        print(f"[任务] OCR 发现 {len(quests)} 个任务, {len(zero_quests)} 个零进度")

        if zero_quests:
            red_ys = self._find_red_buttons(img)
            if red_ys:
                idx = quests.index(random.choice(zero_quests))
                y = red_ys[idx] if idx < len(red_ys) else red_ys[-1]
                print(f"[任务] 更换第{idx+1}个 y={y}")
                ctrl.post_click(1220, y).wait()
                time.sleep(0.5)

        self.close_quest_screen(ctrl)
        print("[任务] 检查完成")
