# AWS Cloud Hands-on — AWS 雲端工程師學習工作區

這是一份個人的 **AWS 雲端工程師 / AWS Certified Cloud Practitioner (CCP)** 學習與實作紀錄，內容涵蓋課程講義、單元筆記、題庫練習、每日作業驗收與實際動手做的帳號、CLI 操作紀錄。目錄會隨學習進度持續變動，非固定結構。

## 目錄結構

```
.
├── d00_ai_tutor/          # AI 家教功能介紹、課程介紹、個人學習流程圖與反思
├── d01~d03_review/        # D01–D03 講義重點整理（學習方法、DevOps、Docker/GitHub）
│   ├── ref/               #   對應的原始 PDF 講義
│   └── output/summary.md  #   整理後的重點筆記
├── d05_iam/               # 第 5 單元實作截圖（root MFA、Budgets、多使用者權限、Budget Action）
├── d08_ha/                # 第 8 單元實作腳本（持續打 ALB 觀察高可用與自動擴展）
├── lectures/              # 課程原始 PDF（第 4–11 單元）與 AI Agent 補充簡報
│   ├── meterials/         #   各單元題庫練習 PDF（第 5–11 單元）
│   └── A04-7 常掛掉的單機服務/  # 第 8 單元講師材料（app.py、user-data.sh）
├── lecture_notes/         # 依單元整理的筆記（d04 開發者日常 ~ d11 DNS/CDN）與上課日誌
├── implements/            # 每日動手做紀錄與驗收表（d01, d05, d07）
│   └── d07_implement/     #   S3 CLI 操作實作 + Deny HTTP 的 Policy 範例
├── references/            # 題庫參考資料（CLF-C02、SAA-C03 PDF）
├── CLAUDE.md              # Claude 在此工作區的角色與行為準則
└── .gitignore             # 排除憑證、.venv、.DS_Store、.obsidian 等
```

## 各區塊說明

### `lectures/` — 課程教材

第 4～11 單元的原始 PDF 講義，題庫練習放在 `meterials/`：

| 單元       | 主題                                       | 題庫練習 |
| ---------- | ------------------------------------------ | -------- |
| 第 4 單元  | 程式開發人員的日常                         | —        |
| 第 5 單元  | 帳號安全、IAM 與成本控制（另有更新版講義） | ✓        |
| 第 6 單元  | EC2 與運算選型                             | ✓        |
| 第 7 單元  | 儲存 EBS、EFS 與 S3                        | ✓        |
| 第 8 單元  | 高可用與自動擴展                           | ✓        |
| 第 9 單元  | VPC 網路                                   | ✓        |
| 第 10 單元 | 資料庫 RDS、Aurora 與快取                  | ✓        |
| 第 11 單元 | DNS 與內容分發                             | ✓        |

另有非單元類的補充簡報：`AGENT介紹.pdf`（AI Agent 介紹）與 `AI 員工帝國.pdf`（AI 員工 demo）。

`A04-7 常掛掉的單機服務/` 是第 8 單元的講師材料：一支處理 40～120 個請求後會自行結束的 HTTP 服務（`app.py`，聽 8080，`/health` 回 200）與對應的 EC2 開機腳本（`user-data.sh`），用來練習 ALB 健康檢查與 Auto Scaling 自動換機。

### `lecture_notes/` — 個人筆記

依單元整理的重點筆記：

- `d04_developer_daily.md`：Sprint 管理與票
- `d05_iam.md`：Region/AZ/Edge Location、IAM 身分管理與帳號安全
- `d06_ec2.md`：EC2 型號命名與運算選型
- `d07_storage.md`：EBS／EFS／S3 三種儲存形狀
- `d08_ha.md`：單點失敗、負載平衡、健康檢查、Auto Scaling
- `d09_vpc.md`：VPC、CIDR、Subnet、Route Table、IGW、NAT Gateway
- `d10_rds.md`：RDS、Aurora 與快取，含手動 failover 量測中斷秒數的實作
- `d11_dns_cdn.md`：Route 53（記錄型別、Alias、路由策略與故障切換）、CloudFront + OAC、Global Accelerator，含 S3 靜態前端掛 CloudFront 的實作

另有非單元類的紀錄：`20260920_上課日誌.md`（d07 下半～d08 的階段性摘要）、`課堂補充.md`。

### `implements/` — 動手做與驗收

每日作業的實際操作紀錄，多以「驗收表」形式呈現，方便對照確認：

- `d01_manual.md`：root MFA、Budgets 預警、`aws configure --profile`、Python venv + boto3、Git 初始化與 `.gitignore`
- `d05_manual.md`：空帳號四步驟（root MFA 不留 access key → Identity Center 身分 → CLI 多 profile → 月預算 30 美元），含進階（多使用者權限先寬後收緊）與加分（Budget Action 自動煞車）
- `d07_implement/`：S3 CLI 操作（`cp` / `list-object-versions` / `presign`）與一份 Deny HTTP（強制 HTTPS）的 Policy 範例

### `d05_iam/` — 第 5 單元實作截圖

對應 `implements/d05_manual.md` 的驗收截圖，依步驟編號：Free Plan、root MFA、`course-admin` 登入、CLI 指令、Budgets（0 元與 30 美元）、不同使用者的權限允許／拒絕結果，以及 Budget Action 觸發後 EC2 被擋下的畫面。

### `d08_ha/` — 第 8 單元實作腳本

用 `curl` 每秒打一次 ALB 並印出時間與回應的觀察腳本，用來驗收「終止一台機器後服務是否持續可用」：

- `check_alb_prof1.sh`：打 `/health`
- `check_alb_prof2.sh`：打 `/`，觀察流量落在哪台機器
- `check_alb_plusalpha.sh`：不間隔連續打 `/`，用來製造負載觸發擴展策略

執行前需把腳本內的 `ALB_URL` 換成自己的 ALB DNS Name。ALB 與 Auto Scaling 的 EC2 會持續計費，驗收完記得刪除資源。

### `d01~d03_review/` — 前三單元複習

D01（學習方法與 AI 家教）、D02（DevOps 與 GitHub）、D03（Docker 多系統兼容與 GitHub 多分支管理）的原始 PDF 與整理後的 `output/summary.md`，另附操作截圖（`awssts_shot.png`、`gitlog_shot.png`、`venv_shot.png`）。

### `d00_ai_tutor/`

AI 家教功能與課程介紹 PDF，以及個人針對「跟 AI 一起學習」流程的反思紀錄（`d00_learn_flow_chart.md`）。

### `references/`

題庫參考資料，供額外練習使用：

- `CCP題庫集/`：SAA-C03 題庫 PDF（1～1019 題）
- `蝦皮題庫集/`：CLF-C02 題庫（中文、英文、解答）

## 憑證與機密

`.gitignore` 已排除 `account_info/`、`*_accessKeys.csv`、`*_credentials.csv`、`*.pem`、`.env` 等檔案，憑證一律不進版控；CLI 操作以 `aws configure --profile` 或 Identity Center 登入為準，不在程式碼或筆記中硬編金鑰。

## 學習主軸

依 CLAUDE.md 中定義的角色設定，本工作區的學習與實作以下列原則為準：

- **最小權限、不留 root access key、預算控管**優先於「先求能動」
- 架構類問題習慣性檢視安全性、成本、可靠性、效能之間的取捨（Well-Architected 精神）
- 作業以驗收表對照，確保每項都有可核對的具體結果
