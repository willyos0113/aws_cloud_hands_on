# d13 | Infrastructure as Code：CloudFormation、SAM、CDK 與 AI 生成

> 來源：`lectures/第 13 單元 Infrastructure as Code.pdf`（共 78 頁；定價與額度為講義 2026-10-14 查閱的數字）

**今日目標**：上週在主控台點了兩個小時環境才會動，組員說「我也要一套一樣的」——把環境寫成一份檔案，能重做、能審查、能一鍵收掉。

**六個名詞**

| 名詞                     | 意思                                       |
| ------------------------ | ------------------------------------------ |
| IaC                      | Infrastructure as Code，把基礎設施寫成檔案 |
| 模板 template            | YAML 檔，列出要哪些資源                    |
| 堆疊 stack               | 一組資源，當一個單位建、改、刪             |
| 變更集 change set        | 部署前的預覽：將要新增、修改、刪除什麼     |
| 取代 Replacement         | 建新的、刪舊的，資料不會搬家               |
| 偏離偵測 drift detection | 抓出有人已經繞過模板偷改的資源             |

---

## 一、為什麼要 IaC：把環境寫成一份檔案

**三件事**

- 手點：重做不出來、說不出誰改了什麼、收不乾淨
- 模板：可重現、可審查、環境一致、一鍵清理
- 堆疊是一個單位：全部建好，或全部收回

**流程**：模板（YAML）→ CloudFormation（照著建、改、刪）→ 堆疊（一組資源）

**一份檔案，四件事一起解決**

| 好處     | 說明                       |
| -------- | -------------------------- |
| 可重現   | 同一份模板，再建一次就一樣 |
| 可審查   | 放進 Git，改了哪行一目了然 |
| 環境一致 | 開發、測試、正式同一份模板 |
| 一鍵清理 | 刪掉堆疊，資源一起刪       |

**Stack：要嘛全部建好，要嘛全部收回**

- 模板有四個資源，第四個失敗 → **預設整個回滾**，前三個也自動刪掉
- 想留住成功的，建立時選 `Preserve successfully provisioned resources`

**用模板部署不花錢？**

- ✗ 大家通常會想：用模板部署不花錢
- ✓ 實際上：CloudFormation 工具不加收，**資源照算**；建出來的 EC2、ALB 跟手點一樣計費

**檢查點：四個資源，前三個建好，第四個失敗，沒改任何設定，結果？**

- ✓ 整個回滾，前三個也刪掉
- ✗ 前三個留著：那是勾了「保留成功資源」才會發生
- ✗ 跳過第四個照樣完成：全部成功才算成功
- ✗ 卡住要自己刪：回滾是自動的

**CCP 考點**

- CLF-C02 第 0629 題：用標準化**範本**建立架構的**複本**，用於開發、測試、正式環境 → **CloudFormation**
- 誘答：Cloud Map 幫服務互相找到對方；CloudFront 是 CDN（d11）；CloudTrail 記誰呼叫 API（d12）

> 一句話：手點的環境只活在你的記憶裡。寫成檔案，才能重做、審查、收掉。

## 二、CloudFormation 模板：按部署前先看預覽

**三件事**

- 只有 `Resources` 必填；改哪個屬性，決定會不會被取代
- 變更集先預覽，`Replacement` 是 True 就先停手
- 偏離偵測抓偷改；`DeletionPolicy` 與 `UpdateReplacePolicy` 保命

**模板結構：只有 Resources 是必填**

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Parameters: # 部署時才填的值
  Env:
    Type: String
    AllowedValues: [dev, prod]
Resources: # 必填：要建哪些資源
  DemoBucket: # 邏輯 ID（AWS 給的真名叫實體 ID）
    Type: AWS::S3::Bucket
    Properties:
      Tags:
        - { Key: env, Value: !Ref Env } # !Ref 引用參數
Outputs: # 建好後拿出來看
  BucketName:
    Value: !Ref DemoBucket
```

**取代：只改資料庫的一個屬性，舊資料庫就被刪掉**

- 改到 `Update requires: Replacement` 的屬性 → 先建新的、再刪舊的，**資料跟著舊的走**
- 改之前：拍快照、準備中斷對策

**變更集：先看預覽，按了執行才真的改**

1. 建立
2. 檢視（新增、修改、刪除）
3. 不放心再建一版比較
4. 執行 — **只有第 4 步會動到堆疊**

**Replacement 欄位：True 就是舊的會被刪掉**

| Replacement   | 意思                         |
| ------------- | ---------------------------- |
| False         | 不會重建，原地改             |
| Conditionally | 看情況，查那個屬性的更新行為 |
| True          | 會重建：舊的會被刪掉         |

- 同一個資源改了好幾處，取最嚴重的那一個

**變更集 vs 偏離偵測：一個看未來，一個抓過去**

|        | 變更集               | 偏離偵測                       |
| ------ | -------------------- | ------------------------------ |
| 看什麼 | 預覽「將要」做的改變 | 抓出有人「已經」繞過模板偷改的 |
| 限制   | —                    | 只比對模板裡明確寫出的屬性     |

**刪除與取代的保險**

| 屬性                | 什麼時候生效             | 可以設                             |
| ------------------- | ------------------------ | ---------------------------------- |
| DeletionPolicy      | 刪堆疊，或從模板拿掉資源 | `Retain` 留著；`Snapshot` 先拍快照 |
| UpdateReplacePolicy | 更新時被取代             | `Retain` 留舊的；`Snapshot`        |

- **陷阱**：DeletionPolicy 管不到取代
- 沒寫預設刪掉；RDS 預設 Snapshot

**StackSets：一份模板，發到很多帳號**

- 管理帳號建一個 StackSet，發到多個帳號、多個區域
- 需要帳號間信任或 Organizations；學員 Free plan 只看講師示範

**檢查點：變更集顯示正式資料庫 Replacement 是 True，下一步？**

- ✓ 先停下，找出哪個屬性造成重建，備份或改寫法
- ✗ 直接執行：取代是建新的、刪舊的，**不會搬資料**
- ✗ 先跑偏離偵測：偏離偵測看過去，跟這次的取代無關
- ✗ 加 `DeletionPolicy: Retain` 就安全：它管不到取代，要 `UpdateReplacePolicy`

> 一句話：按部署之前，先看變更預覽。Replacement 是 True，就有東西要重建。

## 三、SAM：寫得少的 CloudFormation

**三件事**

- SAM 範本是 CloudFormation 的簡寫，`Transform` 那行必填
- 部署時展開回完整的 CloudFormation，連 IAM 角色都幫你生
- `sam build`、`local invoke`、`deploy`、`delete`；只有本機測試要 Docker

**背景：Lambda**

- 交出程式，不用管伺服器；有請求進來才跑
- 按次數與執行時間收費，每月免費 100 萬次請求、40 萬 GB-秒（下一單元細講）

**SAM 範本：Transform 那一行必填**

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31 # 告訴 CloudFormation：這是 SAM，先展開
Resources:
  HelloFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.13 # 用哪種語言跑
      Handler: index.handler # 從哪個函式進去
      InlineCode: | # 程式直接寫在範本裡
        def handler(event, context):
            return {"msg": "hello"}
```

**SAM 展開：一個函式，長出兩個資源**

- `AWS::Serverless::Function` 部署時展開成 `AWS::Lambda::Function`
- 沒指定 Role，SAM 再幫你生 `AWS::IAM::Role`

**SAM CLI：四個指令走完一輪**

| 指令                  | 做什麼         |
| --------------------- | -------------- |
| `sam build`           | 整理程式       |
| `sam local invoke`    | 本機容器跑一次 |
| `sam deploy --guided` | 帶你部署       |
| `sam delete`          | 刪堆疊與部署檔 |

**用 SAM 一定要先裝 Docker？**

- ✗ 大家通常會想：用 SAM 一定要先裝 Docker
- ✓ 實際上：部署不用 Docker；只有本機測試、或打包加 `--use-container` 才需要

**檢查點：同學嫌 `Transform` 那行太長，刪了再部署，結果？**

- ✓ CloudFormation 不認得 Serverless 類型，部署失敗：它是展開的開關
- ✗ 照常部署：它是官方規定的必備宣告，不是註解
- ✗ SAM 自動補回：工具不會替你改範本

**CCP 考點**

- CLF-C02 第 0464 題：運行應用程式的**無伺服器計算服務** → **Lambda**
- 誘答：CloudFormation 負責「建」資源，不跑你的程式；Elastic Beanstalk 幫你管機器；ELB 只分流量

> 一句話：SAM 是 CloudFormation 的簡寫。寫得少，變更預覽照樣要看。

## 四、CDK：用程式寫，部署的還是 CloudFormation

**三件事**

- `cdk synth` 先產生模板，再交給 CloudFormation
- 支援六種語言，考試最愛問
- 適不適合，看團隊會不會寫程式

**同一個桶，兩種寫法**

```yaml
# CloudFormation 模板（YAML）
Resources:
  ReportBucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: Enabled
```

```python
# CDK（Python，講師示意）
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
class ReportStack(Stack):
  def __init__(self, scope, id):
    super().__init__(scope, id)
    s3.Bucket(self, "ReportBucket", versioned=True)
```

- 問題：這段程式最後是誰去 AWS 把桶建出來？ → **CloudFormation**

**cdk synth：先吐出模板，後面全是老朋友**

- 你的程式 → `cdk synth` 產生模板（放 `cdk.out`）→ CloudFormation 建堆疊
- `cdk diff`：部署前先跟已部署的堆疊比一比

**CDK 組成：積木加上工具**

| 元件              | 意思                                              |
| ----------------- | ------------------------------------------------- |
| Construct Library | 寫好的積木（construct），一行拿到一個設定好的資源 |
| CDK Toolkit       | 主要是 CDK CLI：產生模板、比差異、部署            |

- CDK = Cloud Development Kit，開源開發框架，用程式定義雲端基礎設施，再透過 CloudFormation 佈建

**CDK 支援語言：六種，考試最愛問**

| 支援                                                | 不在清單上（題庫誘答項） |
| --------------------------------------------------- | ------------------------ |
| TypeScript、JavaScript、Python、Java、C# / .NET、Go | Ruby、PHP、Swift         |

**cdk bootstrap：每個帳號加區域，先做一次**

- 環境 = 帳號 + 區域
- 建出堆疊 `CDKToolkit`：S3 桶（放專案檔）、ECR 儲存庫（放 Docker 映像檔）、IAM Roles（部署用權限）
- 看到 `CDKToolkit` 堆疊**不要刪**；這門課由講師示範，不跟做

**CDK 選用時機：看團隊，不看流行**

| 適合用 CDK               | 用設定檔就好             |
| ------------------------ | ------------------------ |
| 團隊天天寫程式           | 維運人員多，程式不是日常 |
| 同樣結構要複製很多份     | 資源不多，一份模板讀得完 |
| 想把架構包成積木給別組用 | 審查的人要逐行讀懂       |

- 這門課主線是設定檔：門檻低，AI 生成之後每一行都讀得到

**CCP 考點**

- CLF-C02 第 0253 題：想用 TypeScript、Python、Java、.NET 等**程式語言**佈建基礎架構 → **CDK**
- 誘答：CloudFormation 寫 YAML／JSON 模板，不是程式語言；CLI 是一行一行下指令；CodeBuild 負責編譯與測試

## 五、工具選型：四個工具，兩個引擎

**三件事**

- CloudFormation、SAM、CDK 共用 CloudFormation 引擎
- Terraform 自己保管 state 檔，適合多雲
- 這門課從今天起，實作一律交設定檔

**兩個引擎**

- 左：CloudFormation、SAM、CDK 最後都交給 CloudFormation，change set、Replacement 全部通用
- 右：Terraform 自己算差異、自己記狀態

| 工具           | 你寫什麼              | 誰記住現況        | 適合                      |
| -------------- | --------------------- | ----------------- | ------------------------- |
| CloudFormation | YAML／JSON 模板       | AWS 的堆疊        | 只用 AWS、要逐行審查      |
| SAM            | 簡化的 YAML           | AWS 的堆疊        | Lambda、API 無伺服器      |
| CDK            | TypeScript、Python 等 | AWS 的堆疊        | 工程師多、結構重複多      |
| Terraform      | Terraform 語言（HCL） | 你保管的 state 檔 | 多雲、已有 Terraform 團隊 |

（「適合」欄為講師經驗）

**Terraform state：一個檔記住雲上一切，弄丟就麻煩**

- `.tf` 設定檔：你寫的
- `terraform.tfstate`：對照表，設定 ↔ 真實資源
- `plan` → `apply`：先看，同意才改
- 預設放本機，不好協作，檔案丟了就有風險；CloudFormation 的狀態由 AWS 幫你顧
- Terraform 留到 GCP 段實作，今天只要知道差在這裡

**選型：由上往下問，第一個「是」就停**

| 順序 | 問題                              | 是 →           |
| ---- | --------------------------------- | -------------- |
| 1    | 要同時管 AWS 以外的雲嗎？         | Terraform      |
| 2    | 主要是 Lambda、API 這類無伺服器？ | SAM            |
| 3    | 團隊是工程師，結構大量重複？      | CDK            |
| —    | 三個都不是                        | CloudFormation |

- 前提：**公司已經在用的工具優先**，換工具的成本常比工具差異大

**課程路線**

| 工具           | 在這門課                           |
| -------------- | ---------------------------------- |
| CloudFormation | 今天實作；讀懂 change set 的基本功 |
| SAM            | AWS 段主線，Lambda、API 都用它     |
| CDK            | 只做對照                           |
| Terraform      | GCP 段實作                         |

- 交作業附模板：助教部署得起來、刪得乾淨，才算數

**CCP 考點**

- CLF-C02 第 0100 題：用 IaC 自動化部署，並把正式環境堆疊擴展到多個區域 → **CloudFormation**（同一份模板，在每個區域各建一個堆疊）
- 誘答：CloudWatch 收指標日誌（看）、Config 記錄設定查合規（看）、Trusted Advisor 給建議；**唯一會「建東西」的是 CloudFormation**

## 六、AI 生成 IaC：先讀懂、看預覽，才執行

**三件事**

- 生成、逐行讀懂、看 change set、才執行
- 改名字最常觸發 Replacement，舊資源連資料被刪
- 有資料的資源，兩個 Retain 都要寫

> AI 三秒寫完模板。按下部署前，每一行你都要說得出它會做什麼。

**四關，順序不能換**

| 順序 | 關卡          | 抓什麼              |
| ---- | ------------- | ------------------- |
| 1    | 生成          | —                   |
| 2    | 逐行讀懂      | 抓 AI「多改了什麼」 |
| 3    | 看 change set | 抓「改了會怎樣」    |
| 4    | 執行          | —                   |

**Replacement：建新的、刪舊的，資料不會搬家**

| 更新行為          | 結果               |
| ----------------- | ------------------ |
| No interruption   | 原地改，例：加標籤 |
| Some interruption | 原地改，會中斷一下 |
| Replacement       | 新 ID，舊的被刪    |

**Update requires：改名字最常觸發取代**

| 屬性                           | 更新行為        |
| ------------------------------ | --------------- |
| DynamoDB `TableName`           | Replacement     |
| S3 `BucketName`                | Replacement     |
| SNS `TopicName`                | Replacement     |
| RDS `DBInstanceIdentifier`     | Replacement     |
| DynamoDB `Tags`、`BillingMode` | No interruption |
| SNS `DisplayName`              | No interruption |

- **不需要固定名字的資源，就不要寫名字**，讓 CloudFormation 自動取（講師經驗）

**change set：每一行先看 Action 和 Replacement**

| Replacement   | 動作                   |
| ------------- | ---------------------- |
| True          | 建新的、刪舊的：停下來 |
| Conditionally | 可能取代：當成 True 查 |
| False         | 原地改                 |

- `Action` 是 `Add`、`Modify`、`Remove`；Replacement 只對 `Modify` 有意義；看到 `Remove` 也停下來問

```bash
# 只建 change set，不執行（不會動到堆疊）
aws cloudformation deploy --template-file new.yaml --stack-name orders --no-execute-changeset
# 只看四個欄位：動作、邏輯 ID、資源類型、是否取代
aws cloudformation describe-change-set --stack-name orders --change-set-name <名字> \
  --query 'Changes[].ResourceChange.[Action,LogicalResourceId,ResourceType,Replacement]' --output table
```

**DeletionPolicy：替有資料的資源加保險**

| 情境           | 寫法                          | 結果                                             |
| -------------- | ----------------------------- | ------------------------------------------------ |
| 刪除堆疊時     | `DeletionPolicy: Retain`      | 資源留下，只脫離堆疊（`Snapshot`：先拍快照再刪） |
| 更新造成取代時 | `UpdateReplacePolicy: Retain` | 舊的那份留下來                                   |
| 任何人想刪表時 | `DeletionProtection: Enabled` | DynamoDB 表刪不掉                                |

- 沒寫 `DeletionPolicy` 預設是刪除（RDS 單機例外，預設快照）
- 留下的資源**照樣收費**

**取代陷阱（兩人一組練習）**：需求只有「訂單表加標籤、主題顯示名稱改成 Order Notifications」，AI 改完哪幾行會出事？

| 改動                            | 需求有嗎 | Replacement | 後果                               |
| ------------------------------- | -------- | ----------- | ---------------------------------- |
| `TableName` → `OrdersProd`      | 沒有     | True        | 新的空表，舊表連資料被刪           |
| `TopicName` → `order-alerts-v2` | 沒有     | True        | 新主題，舊訂閱跟著消失（講師推論） |
| 加 Tags、改 DisplayName         | 有       | False       | 原地改                             |

- **修法**：名字改回原樣；訂單表補上兩個 Retain，再建一次 change set，確認全是 False

**對 AI 的提問：只改需求，並列出每個改動**

> 附上目前的模板。只做這兩件事：（1）訂單表加標籤 `team=checkout`；（2）主題顯示名稱改成 Order Notifications。其他每一行都不要動。改完列一張表：每個被改的屬性、改前、改後、官方文件的 Update requires。

- AI 填的 Update requires 也可能錯：每一列自己查官方參照頁，再用 change set 對答案

**檢查點：有資料的 DynamoDB 表只寫了 `DeletionPolicy: Retain`，有人改 `TableName` 並更新，舊表會怎樣？**

- ✓ 被刪除：取代時預設刪掉舊的
- ✗ 留下來：`DeletionPolicy` 只管「刪除堆疊」，取代時不生效
- ✗ 原地改名：`TableName` 是 Replacement，不能原地改名
- ✗ 更新失敗：名字改了，取代會成功

> 一句話：AI 生成，人讀懂，看預覽，才執行。

## 七、實作：補完一份部署模板

學員跟做，**0 元，全在免費額度內**。檔案 `lab/lab-template.yaml`，堆疊 `course-iac-lab`，東京區域。一份模板四個資源：S3 桶、SNS 主題、DynamoDB 表、IAM Role。

**流程**：補 TODO → 建 change set → 讀每一行 → 執行 → 刪乾淨

**三個目標**

- 補 4 個 TODO，先建 change set，看過再部署
- 說得出 change set 每一行在做什麼
- 刪除堆疊，帳號裡不留任何資源

**必做：六步**

1. **補 4 個 TODO**：S3 封鎖公開存取、信箱用 `!Ref AlertEmail`、表的 `KeySchema`、Outputs 加表名 → 檔案裡沒有 TODO
2. **語法檢查**：`cfn-lint lab-template.yaml` → 沒有輸出
3. **建 change set**：`deploy … --capabilities CAPABILITY_IAM --no-execute-changeset` → 印出 `describe-change-set` 指令
4. **逐行讀**：`describe-change-set`，四行逐一說出會建什麼 → 四行 `Add`：桶、主題、表、Role
5. **執行**：`execute-change-set`，再 `wait stack-create-complete` → Outputs 有四列
6. **確認訂閱**：信箱按 Confirm subscription → 訂閱狀態變 Confirmed

- 指令先 `export AWS_PROFILE=course AWS_DEFAULT_REGION=ap-northeast-1`；完整指令在講稿
- `cfn-lint` 1.57 為講師 2026-10-14 實測

**清理：一行刪光，再親眼確認**

```bash
# 刪堆疊：堆疊內所有資源一起刪
aws cloudformation delete-stack --stack-name course-iac-lab
# 等到刪除完成再往下確認
aws cloudformation wait stack-delete-complete --stack-name course-iac-lab
```

- CloudFormation 主控台：`course-iac-lab` 是 `DELETE_COMPLETE`
- S3、SNS、DynamoDB、IAM：Outputs 那四個名字都找不到
- **卡在 S3 桶**：桶裡有檔案，主控台按 Empty 再刪

> IaC 最大的好處：建了什麼，刪的時候一個不漏。

## 八、回家作業：一律個人完成(略，參考用)

| 主題                | 交什麼                                                                            |
| ------------------- | --------------------------------------------------------------------------------- |
| 為什麼要 IaC        | 本課無作業                                                                        |
| CloudFormation 模板 | 本課無作業                                                                        |
| SAM                 | 本課無作業                                                                        |
| CDK                 | 本課無作業，併入工具選型                                                          |
| 工具選型            | 替期末專題選一個 IaC 工具，用三個選型問題寫理由，半頁                             |
| AI 生成 IaC         | 修好 `ai-generated-trap.yaml`，附 change set 每一行預期的 Replacement             |
| 實作                | 補好的 `lab-template.yaml` 加一頁說明：部署截圖、每行解釋、`DELETE_COMPLETE` 截圖 |

## Takeaway

1. 基礎設施寫成檔案，就能審查、重現、一鍵刪光
2. 動手之前先看 change set，不看就不按
3. Replacement True 是最貴的一行，改名字最常踩到
4. AI 生成，人讀懂，看預覽，才執行
