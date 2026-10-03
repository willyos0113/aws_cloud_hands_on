# A04-7 講師材料：常掛掉的單機服務

- `app.py`：標準函式庫的 HTTP 服務，聽 8080，`/` 回機器身分與計數，`/health` 回 200。處理 40 到 120 個請求後整個 process 結束，機器仍在，服務死了。
- `user-data.sh`：Amazon Linux 2023 的開機腳本，下載 `app.py` 並以 nohup 啟動。刻意不設自動重啟。
- 課前準備：把 `app.py` 放到一個學員抓得到的網址（公開 S3 物件或 GitHub raw），把 `user-data.sh` 的 `APP_URL` 換掉。
  (https://YOUR_BUCKET_NAME.s3.ap-northeast-1.amazonaws.com/app.py)
- Security Group：ALB 的 SG 入站 80 來自 0.0.0.0/0；EC2 的 SG 入站 8080 來源填 ALB 的 SG（第 6 單元第 3 課的互相參照）。
- 驗收：學員手動終止一台，網站在幾十秒內恢復；等 app 自己崩，Auto Scaling 在幾分鐘內把那台換掉。
- 加分題（目標追蹤）前把 `user-data.sh` 的 `FLAKY_NO_CRASH` 改成 1 發新版模板，不然狂打會先觸發崩潰而不是擴展。
