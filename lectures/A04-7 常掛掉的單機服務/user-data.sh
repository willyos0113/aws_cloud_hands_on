#!/bin/bash

# 安裝必要套件
yum update -y
yum install -y python3 python3-pip curl
pip3 install -q flask requests

# A04-7 實作用的 User Data：Amazon Linux 2023。開機時把 app.py 放好並啟動。
# 講師把 app.py 放在一個公開可讀的 S3 物件或 GitHub raw 網址，學員填進 APP_URL。
# 範例：https://your-bucket.s3.ap-northeast-1.amazonaws.com/app.py
APP_URL="${APP_S3_URL:?請設定 APP_S3_URL 環境變數}"
export FLAKY_NO_CRASH=0   # 加分題（目標追蹤）時改成 1，程式就不會自己崩
mkdir -p /opt/flaky
curl -fsSL "$APP_URL" -o /opt/flaky/app.py

# 故意不用 systemd 的 Restart=always：服務死了就是死了，讓 health check 去抓
nohup python3 /opt/flaky/app.py > /var/log/flaky.log 2>&1 &