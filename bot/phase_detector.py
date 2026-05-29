"""页面检测器 —— 用模板匹配判断当前游戏处于哪个阶段

策略:
    1. 先检测特征最明显的阶段（结算 > 英雄选择 > 菜单）
    2. 招募阶段用特定 ROI（右侧计时器区域）判断
    3. 以上都不是则默认为战斗阶段（安全等待）
"""

import os
import cv2
import numpy as np
from maa.custom_recognition import CustomRecognition


class PhaseDetector(CustomRecognition):
    """分析截图，返回当前游戏阶段。"""

    # 全屏模板（特征明显的阶段）
    FULL_SCREEN_TEMPLATES = [
        ("game_end.png", "game_end", 0.7),
        ("hero_select.png", "hero_select", 0.7),
        ("bg_lobby.png", "bg_lobby", 0.7),
        ("mode_select.png", "mode_select", 0.7),
        ("main_menu.png", "main_menu", 0.7),
    ]

    # 招募阶段：用右侧计时器绳索区域来识别
    # 1280x720 横屏下，绳索大约在右侧 1/4 区域
    RECRUIT_ROI_RATIO = (0.82, 0.10, 0.15, 0.70)  # (x_ratio, y_ratio, w_ratio, h_ratio)
    RECRUIT_THRESHOLD = 0.85

    def __init__(self):
        super().__init__()
        self._full_templates = {}
        self._recruit_template = None
        self._upgrade_template = None

    def _load_upgrade_template(self):
        """加载升级按钮模板（用于招募二次确认）"""
        if self._upgrade_template is not None:
            return self._upgrade_template
        image_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resource", "image"
        )
        path = os.path.join(image_dir, "tavern_upgrade_btn.png")
        if os.path.exists(path):
            self._upgrade_template = cv2.imread(path)
        return self._upgrade_template

    def _load_templates(self):
        """加载所有模板图片"""
        if self._full_templates and self._recruit_template is not None:
            return

        image_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resource", "image"
        )

        # 加载全屏模板
        for filename, phase, threshold in self.FULL_SCREEN_TEMPLATES:
            path = os.path.join(image_dir, filename)
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    self._full_templates[filename] = {
                        "image": img, "phase": phase, "threshold": threshold
                    }

        # 加载招募阶段模板（用于 ROI 匹配）
        recruit_path = os.path.join(image_dir, "recruit_phase.png")
        if os.path.exists(recruit_path):
            self._recruit_template = cv2.imread(recruit_path)

    def _get_roi(self, img, ratio):
        """根据比例从图片中截取 ROI 区域"""
        h, w = img.shape[:2]
        x = int(w * ratio[0])
        y = int(h * ratio[1])
        rw = int(w * ratio[2])
        rh = int(h * ratio[3])
        return img[y:y + rh, x:x + rw]

    def _match_full_screen(self, img):
        """全屏模板匹配：遍历模板找最高分"""
        h, w = img.shape[:2]
        best_score = 0
        best_phase = None

        for filename, info in self._full_templates.items():
            template = info["image"]
            if template.shape[:2] != (h, w):
                template = cv2.resize(template, (w, h))
            score = float(cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)[0][0])
            if score > best_score and score >= info["threshold"]:
                best_score = score
                best_phase = info["phase"]

        return best_phase, best_score

    def _check_recruit(self, img):
        """用右侧计时器 ROI 判断是否为招募阶段"""
        if self._recruit_template is None:
            return 0.0

        h, w = img.shape[:2]
        t_h, t_w = self._recruit_template.shape[:2]

        # 从当前截图和模板截图中分别取 ROI 区域
        roi_current = self._get_roi(img, self.RECRUIT_ROI_RATIO)
        roi_template = self._get_roi(self._recruit_template, self.RECRUIT_ROI_RATIO)

        # 统一尺寸
        if roi_current.shape[:2] != roi_template.shape[:2]:
            roi_template = cv2.resize(
                roi_template, (roi_current.shape[1], roi_current.shape[0])
            )

        score = float(
            cv2.matchTemplate(roi_current, roi_template, cv2.TM_CCOEFF_NORMED)[0][0]
        )
        return score

    def analyze(self, context, argv):
        img = argv.image
        h, w = img.shape[:2]

        self._load_templates()

        # 优先检测特征明显的阶段（全屏匹配）
        phase, score = self._match_full_screen(img)
        if phase:
            print(f"[检测] {phase} (全屏 {score:.2f})")
            return CustomRecognition.AnalyzeResult(
                box=(w // 2, h // 2, 1, 1),
                detail={"phase": phase},
            )

        # 检测招募阶段（ROI 匹配右侧计时器 + 升级按钮双重确认）
        recruit_score = self._check_recruit(img)
        if recruit_score >= self.RECRUIT_THRESHOLD:
            # 二次确认：加载/等待画面没升级按钮
            upgrade_tpl = self._load_upgrade_template()
            if upgrade_tpl is not None:
                r = cv2.matchTemplate(img, upgrade_tpl, cv2.TM_CCOEFF_NORMED)
                _, up_score, _, _ = cv2.minMaxLoc(r)
                if up_score >= 0.35:
                    print(f"[检测] recruit (计时器{recruit_score:.2f} 升级{up_score:.2f})")
                    return CustomRecognition.AnalyzeResult(
                        box=(w // 2, h // 2, 1, 1),
                        detail={"phase": "recruit"},
                    )
            # 计时器匹配但无升级按钮 → loading
            print(f"[检测] loading (计时器{recruit_score:.2f}, 无升级)")
            return CustomRecognition.AnalyzeResult(
                box=(w // 2, h // 2, 1, 1),
                detail={"phase": "loading"},
            )

        # 默认：战斗阶段（也是 loading 的安全兜底）
        print(f"[检测] combat (默认, recruit_score={recruit_score:.2f})")
        return CustomRecognition.AnalyzeResult(
            box=(w // 2, h // 2, 1, 1),
            detail={"phase": "combat"},
        )
