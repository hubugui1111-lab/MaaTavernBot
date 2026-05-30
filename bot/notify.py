"""PushPlus 微信通知 —— 异常告警推送"""
import urllib.request, json, time, threading

TOKEN = ""
DEBOUNCE_MIN = 30
_last_sent = {}  # {"title": timestamp}


def set_token(token):
    global TOKEN
    TOKEN = (token or "").strip()


def send_alert(title, msg):
    """发送 PushPlus 通知。同类型告警 DEBOUNCE_MIN 分钟内不重复。"""
    if not TOKEN:
        return
    now = time.time()
    if title in _last_sent and (now - _last_sent[title]) < DEBOUNCE_MIN * 60:
        return
    _last_sent[title] = now

    def _post():
        try:
            data = json.dumps({
                "token": TOKEN,
                "title": title,
                "content": msg,
                "template": "html",
                "channel": "wechat",
            }).encode()
            req = urllib.request.Request(
                "http://www.pushplus.plus/send",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=8)
        except Exception:
            pass  # 网络失败静默

    threading.Thread(target=_post, daemon=True).start()
