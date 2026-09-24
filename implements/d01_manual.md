# 驗收表(D01)

1. 雲端帳號: root 開啟 MFA -> [x] 完成

2. 預算警告: Budgets 列表有 Zero spend 和 Monthly cost 兩筆 -> [x] 完成

3. CLI 與多組態: `aws sts get-caller-identity --profile course` 回傳你的帳號 ID -> [x] 完成

   ref 1: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
   ref 2: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html
   (1) 建立 IAM 使用者，生成 credentials 和 accessKeys 兩個檔案
   (2) 設定 aws 存取憑證及預設環境

   ```
   aws configure --profile course
   ```

   (3) 填入 AWS Access Key ID 與 AWS Secret Access Key 下一步完成

4. Python 環境: Python 3.12 以上; venv 或 uv 建好; 能 import boto3 -> [x] 完成

   (1) 建立虛擬環境

   ```
   python3 -m venv .venv
   ```

   (2) 啟動虛擬環境 (Activate)

   ```
   source .venv/bin/activate
   ```

   (3) 安裝 AWS SDK (boto3)

   ```
   pip install boto3
   ```

5. Git 與版控: `git log` 有第一個 commit;`.gitignore` 含 `.env` 與 `*.pem` -> [x] 完成

   (1) 建立 `.gitignore` 並寫入 `.env` 與 `*.pem`
   (2) 先 commit 一次
