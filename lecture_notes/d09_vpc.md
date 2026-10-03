# d09 - VPC 網路：先圈地、分三層、看路由表、排網路洞

[內容]

## 一、先圈地，再分三層放東西

- 六個詞先記起來，後面反覆用：**VPC**（一塊隔離的私網、蓋在 Region、跨 AZ）、**CIDR**（用「起點/位數」表示一段連續 IP）、**Subnet**（VPC 裡切出的一段、綁一個 AZ）、**Route Table**（「要去哪、交給誰」的對照表）、**IGW**（VPC 對外的大門、雙向）、**NAT Gateway**（替私有層機器換 IP、只出不進）

- CIDR 斜線後的數字決定地塊大小；AWS 會保留五個位址（開頭、結尾、路由器、DNS、保留）；三個最常用的尺寸：

| 寫法        | 位址數 | 用途                  |
| ----------- | ------ | --------------------- |
| 10.0.0.0/16 | 65,536 | VPC、AWS 允許最大     |
| 10.1.0/24   | 256    | 一個 Subnet、最常見   |
| 0.0.0.0/0   | 全部   | 「任何地方」指向外面  |

- 圈地前先問三件事：
  1. 用私有位址範圍（10 開頭、172.16～31 開頭、192.168 開頭）？網際網路不會路由
  2. 避開公司現網的 CIDR 段？位址重疊 Peering 會爆炸
  3. 子網路有沒有足夠位置？ALB、NAT 都要吃位址；備著後加 AZ 有餘裕

- **三層角色差異**（每層都在兩個 AZ 各開一個 Subnet）：

| 層級     | 放什麼                | Route 0.0.0.0/0 指向 | 誰能看到 |
| -------- | --------------------- | -------------------- | -------- |
| 公開層   | ALB、NAT Gateway      | IGW                  | 網際網路 |
| 私有層   | agent、應用層、工作機 | NAT Gateway          | 不出去   |
| 隔離層   | 資料庫、向量庫、資料  | 無（完全沒有出口）   | 內部只   |

- 常見的設定錯誤：子網路名字叫「private」就以為安全？實際上只看 Route Table；「private」只是名字、決定安全性的是路由表指向誰

## 二、封包往哪走，只看路由表

- Route Table 只有兩欄：**目的地**（一段 CIDR）、**目標**（要送給誰）；最具體的規則勝出（longest prefix match）；目標可以是 local（VPC 內）、IGW、NAT、Endpoint、Peering、Transit Gateway

- 實務配置範例（一個 10.0.0.0/16 的 VPC）：

```
公開層 Subnet (10.0.1.0/24、10.0.2.0/24)
  Route Table：
    10.0.0.0/16 → local
    0.0.0.0/0   → IGW

私有層 Subnet (10.0.10.0/24、10.0.11.0/24)
  Route Table：
    10.0.0.0/16 → local
    0.0.0.0/0   → NAT Gateway（在公開層 AZ a）

隔離層 Subnet (10.0.20.0/24、10.0.21.0/24)
  Route Table：
    10.0.0.0/16 → local
    （沒有 0.0.0.0/0，完全無出口）
```

- **最具體的規則勝出**：如果 Route Table 同時有 10.0.0.0/16 → local 和 0.0.0.0/0 → IGW，封包要去 10.0.1.5，會匹配第一條（/16 比 /0 更具體）、留在內部；要去 8.8.8.8，匹配第二條、走 IGW

- 沒指定的路由表用主路由表；主路由表預設只有 local；如果子網路沒明確關聯路由表，會用主的；所以多數情況預設子網路是隔離的、沒有往外路

## 三、兩道防火牆，加一扇側門

- AWS 防火牆分兩層：**Security Group**（機器級、狀態式、只有 allow）和 **NACL**（子網路級、非狀態式、allow/deny 都有）；兩層都要打開才通

| 面向     | Security Group | NACL         |
| -------- | -------------- | ------------ |
| 層級     | 機器級         | 子網路級     |
| 狀態     | 有記憶         | 死板         |
| Allow 否 | 只 allow       | allow & deny |
| 回應     | 自動放         | 需手動配     |
| 順序     | 無所謂         | 優先順序重要 |

- **IGW 是 VPC 唯一的大門、而且雙向**：掛上去只是「有門」，要走到門還要 Route Table 指過去；所以公開層機器才用 IGW、私有層用 NAT 才能「只出不進」

- **VPC Endpoint：S3 / DynamoDB 不用走 IGW 或 NAT**——流量走 VPC 內部網路、免費、更快、更安全；分兩種：
  - **Gateway Endpoint**（S3、DynamoDB）：掛在 Route Table 上、完全免費、機器 boto3 零改動
  - **Interface Endpoint**（Bedrock、API Gateway）：掛在 Security Group 上、按小時計費；期末專題可能用到 Bedrock Endpoint

- 實務做法：隔離層資料走 Endpoint 存 S3（免費）、私有層 agent 連 Bedrock 時選 Endpoint（付 Endpoint 費）或 NAT（付流量費）、公開層 ALB 走 IGW

## 四、Agent 的出口，跟一個壞掉的網路

- Agent 放在私有層，需要往外連三個方向：**往上接 ALB**（南北流量）、**往下連資料庫**（東西流量）、**往外連 Bedrock**（推論）；缺一不可；任何一條路斷了服務就壞了

- **排障的金字塔**（出問題時从下往上逐層檢查）：

| 層   | 檢查項目              | 沒配的徵狀                 |
| ---- | --------------------- | -------------------------- |
| 1    | Route Table           | `0.0.0.0/0` 沒指向 NAT    |
| 2    | Security Group        | 出站沒打開 443            |
| 3    | NACL                  | 回程流量被擋              |
| 4    | NAT Gateway           | 沒配、配在錯 AZ           |
| 5    | 應用層                | 程式碼、環境變數、權限    |

- **常見的「壞掉的網路」症狀**：
  - Agent 連不到 Bedrock：先看 Route Table、再看 NAT 有沒有配、再看 Security Group 出站
  - Agent 連不到資料庫：先看路由、再看 NACL、再看資料庫 Security Group 有沒有白名單
  - ALB 連不到 Agent：看 Target Group 的 health check、通常是 Security Group 擋了進來的連線
  - 連線忽快忽慢：NAT Gateway 也是機器、有併發上限；超過就掉封包；看 VPC Pricing 有沒有費用爆表

- **Agent 的三層網路配置**：Agent 在私有層（10.0.10.0/24）、NAT Gateway 在公開層、隔離層 Database；私有層 Route Table 0.0.0.0/0 指向 NAT、NAT 指向 IGW；Security Group 入站白名單 ALB、出站預設 allow all 或限 443；隔離層和私有層的 NACL 通常無限制（default）

[作業]

## 一、實作：一個壞掉的網路，四個洞

（分層評分：必做 60% / 進階 20% / 加分 20%）
全用主控台、零程式碼；用 CloudShell 驗證：

1. 必做一：建一個 VPC 10.0.0.0/16、三層各兩個 Subnet（公開、私有、隔離），共六個 Subnet 分別在 AZ a、AZ c
2. 必做二：建三張 Route Table、公開指向 IGW、私有指向 NAT Gateway、隔離無出口；明確寫出 0.0.0.0/0 的目標
3. 必做三：用 CLI `aws ec2 describe-subnets` 驗證每層 Subnet 的 CIDR、位址數、AWS 保留幾個
4. 進階一：改 default VPC 的一個 default Subnet，Availability Zone preference 改成 No preference
5. 進階二：刪除自訂 VPC；Your VPCs 勾自訂 → Actions → Delete VPC → 輸入 delete → Delete
6. 加分：檢查 NAT Gateway 的 Elastic IP，手動終止一台 EC2 再重啟，觀察 IP 有沒有變

- 繳交：五張截圖（VPC 一張、Subnet 三層各一張、Route Table 驗證一張）+ 三行文字（每層 CIDR / 每層 Route 指向誰 / 隔離層為什麼沒出口） + 進階或加分的附加截圖
- 驗收重點：必做要明確寫出每層的 Route Table 目標；進階要秀出 Availability Zone 的改動；加分要秀 Elastic IP 變化或說明原因

## 二、回家作業：都拿期末專題來做，一律個人完成

1. **VPC 三層規劃圖**：替專題畫簡圖，標公開 / 私有 / 隔離、各層 Subnet 數量、各層 Route 指向，共八行
2. **CIDR 計算**：替專題的每層算一次、寫 CIDR 例（10.0.1.0/24）、可用位址數、AWS 保留幾個；共六行
3. **防火牆配置**：改 agent Security Group，入站白名單 ALB、出站限 443；寫一行為什麼不改 NACL
4. **NAT 成本決策**：各 AZ 要不要各開一個 NAT Gateway；寫成成本 vs 可靠性的二選一，共四行
5. **出口選項的選擇**：Agent 連 Bedrock 用什麼（NAT 或 Endpoint）、隔離層資料存 S3 用什麼；寫一段六行的架構說明
6. **排障實戰**：如果 Agent 連 Bedrock 逾時，依序檢查 Route Table → Security Group → NACL → NAT，各寫一句判斷條件
