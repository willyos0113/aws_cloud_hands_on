#!/usr/bin/env python3
"""A04-7 實作用：一台「常掛掉」的單機服務。

只用標準函式庫。聽 8080：
  GET /        回這台機器的 instance id、AZ、已處理幾個請求
  GET /health  回 200（給 ALB 的 health check 用）

故意設計的毛病：處理了 LIMIT 個請求之後整個 process 直接結束，
機器還活著（EC2 status checks 照樣通過），服務卻死了。
這就是課堂要證明的事：只有負載平衡器層級的 health check 抓得到，
Auto Scaling 開了 ELB health check 才會把這台換掉。
"""
import json
import os
import random
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080
LIMIT = random.randint(40, 120)  # 每台機器崩潰點不同，看起來更像真實故障
NO_CRASH = os.environ.get("FLAKY_NO_CRASH") == "1"  # 加分題用：設 1 就不崩
COUNT = 0


def imds(path: str) -> str:
    """讀 EC2 instance metadata（IMDSv2）；不在 EC2 上就回 unknown。"""
    try:
        token_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = urllib.request.urlopen(token_req, timeout=1).read().decode()
        req = urllib.request.Request(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
        )
        return urllib.request.urlopen(req, timeout=1).read().decode()
    except Exception:
        return "unknown"


INSTANCE_ID = imds("instance-id")
AZ = imds("placement/availability-zone")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global COUNT
        if self.path == "/health":
            self._send(200, {"status": "ok", "instance": INSTANCE_ID})
            return
        COUNT += 1
        self._send(200, {"instance": INSTANCE_ID, "az": AZ,
                   "served": COUNT, "will_crash_at": LIMIT})
        if COUNT >= LIMIT and not NO_CRASH:
            # 故意讓服務死掉：process 結束，機器不會重啟它
            self.wfile.flush()
            os._exit(1)

    def _send(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # 安靜一點
        pass


if __name__ == "__main__":
    print(f"listening on {PORT}, will crash after {LIMIT} requests")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
