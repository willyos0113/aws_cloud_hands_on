# AWS Cloud Hands-on — AWS 雲端工程師學習工作區

## 這是一份個人的 **AWS 雲端工程師 / AWS Certified Cloud Practitioner (CCP)** 學習與實作紀錄，內容涵蓋課程筆記、題庫練習、每日作業驗收、實際動手做的帳號與 CLI 操作，以及一個獨立的 Python + boto3 專案。目錄會隨學習進度持續變動，非固定結構。

## 目錄結構

```
.
├── d00_ai_tutor/          # AI 家教功能介紹、個人學習流程圖與反思
├── d01~d03_review/        # D01–D03 講義重點整理（學習方法、DevOps、Docker/GitHub）
│   ├── ref/               #   對應的原始 PDF 講義
│   └── output/summary.md  #   整理後的重點筆記
├── lectures/               # 課程原始 PDF（第 4–8 單元）與題庫練習 PDF
├── lecture_notes/          # 依單元整理的筆記（d04 開發者日常 ~ d08 高可用/Auto Scaling）
├── implements/             # 每日動手做紀錄與驗收表（d01, d05, d07…）
│   └── d07_implement/     #   S3 CLI 操作實作 + IAM Deny Policy 範例
├── references/             # 題庫參考資料（CCP、SAA-C03 等 PDF）
├── account_info/           # AWS IAM 使用者憑證 CSV（已由 .gitignore 排除）
├── my_aws_project/         # 獨立 Python/boto3 專案（有自己的 .git 與 .venv）
├── reviews/                 # （目前為空）預留放置複習或審查紀錄
└── .gitignore               # 已預先排除憑證、.venv、.DS_Store 等
```

---

## 各區塊說明

### `lectures/` — 課程教材

第 4～8 單元的原始 PDF 講義與對應題庫練習：

- 第 4 單元：程式開發人員的日常
- 第 5 單元：帳號安全、IAM 與成本控制
- 第 6 單元：EC2 與運算選型
- 第 7 單元：儲存 EBS、EFS 與 S3
- 第 8 單元：高可用與自動擴展

### `lecture_notes/` — 個人筆記

依單元整理的重點筆記（Region/AZ、IAM、EC2 型號命名、S3/EBS/EFS 儲存形狀、ALB/NLB/Auto Scaling 等），以及 `summary_0920.md` 這類跨單元的階段性摘要。

### `implements/` — 動手做與驗收

每日作業的實際操作紀錄，多以「驗收表」形式呈現，方便對照確認：

- `d01_manual.md`：root MFA、Budgets 預警、`aws configure --profile`、Python venv + boto3、Git 初始化與 `.gitignore`
- `d05_manual.md`：空帳號四步驟（root MFA 不留 access key → Identity Center 身分 → CLI 多 profile → 月預算 30 美元），含進階（多使用者權限先寬後收緊）與加分（Budget Action 自動煞車）
- `d07_implement/`：S3 CLI 操作（`cp` / `list-object-versions` / `presign`）與一份 Deny HTTP（強制 HTTPS）的 IAM Policy 範例

### `d01~d03_review/` — 前三單元複習

D01（學習方法與 AI 家教）、D02（DevOps 與 GitHub）、D03（Docker 多系統兼容與 GitHub 多分支管理）的原始 PDF 與整理後的 `output/summary.md`，另附操作截圖（`awssts_shot.png`、`gitlog_shot.png`、`venv_shot.png`）。

### `d00_ai_tutor/`

AI 家教功能與課程介紹 PDF，以及個人針對「跟 AI 一起學習」流程的反思紀錄（含 recognition vs. recall 的自我檢核方法）。

### `references/`

題庫參考資料，包含 CCP（CLF-C02）與 SAA-C03 題庫 PDF，供額外練習使用。

### `my_aws_project/`

獨立的 Python 專案，內含自己的 `.git`、`.venv` 與 `.gitignore`（已排除 `.env`、`*.pem`、`.venv/`）。目前為空的專案骨架，尚未加入原始碼。

---

## 學習主軸

依 CLAUDE.md 中定義的角色設定，本工作區的學習與實作以下列原則為準：

- **最小權限、不留 root access key、預算控管**優先於「先求能動」
- 架構類問題習慣性檢視安全性、成本、可靠性、效能之間的取捨（Well-Architected 精神）
- 作業以驗收表對照，確保每項都有可核對的具體結果
