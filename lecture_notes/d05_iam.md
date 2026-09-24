# d05 - IAM 身份管理與帳號安全

[內容]

## 一、Region、AZ 與邊緣據點

- 一個 Region 至少有 3 個 AZ（可用區域），AZ 間低延遲專線相連，確保服務 HA；一個 AZ 可能是好幾棟資料中心，重點是跟隔壁 AZ 不共用電力與網路
- 數量關係：Region < AZ < Edge Location（Edge Location 數量最多）
- Edge Location 提供附近客戶端的快取、DNS，分散系統負載，但**不能開 EC2**
- 三種「地端延伸」，都能開 EC2、各解決不同延遲場景：
  - Local Zone：AWS 自己機房，解決大城市低延遲（即時遊戲、直播）
  - Wavelength：電信商機房，解決行動裝置低延遲
  - Outposts：客戶自己機房，資料留在地端、用同一套 API（法規要求資料不能離開地端時選它）
- 選 Region 四問，依序：法規允許資料放哪 > 使用者在哪（延遲）> 服務有沒有開 > 價格
- 多 AZ 擋單一機房故障；多 Region 擋城市級/天災級故障
- 傳輸費：只有從網際網路傳進 AWS 免費；Region 間、同 Region 內跨 AZ 都要收費
- 示意圖：https://aws.amazon.com/tw/about-aws/global-infrastructure/regions_az/

## 二、身份與權限（IAM）

- 權限永遠只寫在 Policy；User/Group/Role 本身沒有權限，只是 Policy 掛的地方；沒寫到就是拒絕（default deny），Allow 與 Deny 同時存在時 Deny 贏
- 五個身分角色：
  - **root user**：權限無限，只開 MFA、日常不登入
  - **User**：長期身分，盡量不用
  - **Group**：一群 User，方便一次指派 Policy
  - **Policy**：JSON，寫著「誰能做什麼」的唯一來源
  - **Role**：沒有密碼沒有金鑰，誰扮演誰暫時拿到權限（一個外套，穿上才能取得臨時憑證）
- Policy 的 Statement 記憶點：1 條 = 誰 + Effect + Action + Resource（填 ARN）+ Condition（選填）；最小權限＝Action 寫具體動詞、Resource 寫具體 ARN、不要用 `*`（口訣：E.P.A.R.C.）
- Role 身上掛兩份 Policy：permission policy（它能做什麼）+ trust policy（誰能穿上它，Principal 決定誰能 AssumeRole）
- **Access Key vs Role 臨時憑證**：
  - Access Key：建好永久有效，等同帳號密碼，外洩後對方就是你，要靠人手動刪
  - Role：透過 STS AssumeRole 換到臨時憑證（key + secret + session token），預設 1 小時、最長 12 小時，到期自動作廢，不用人去刪
- 人怎麼拿身分：人走 Identity Center 登入拿臨時憑證（CLI 用 `aws configure sso` + `aws sso login`）；程式（含 EC2 上的程式）走 Role；跨帳號靠 trust policy 做 AssumeRole
- Identity Center（給員工存取 AWS 帳戶用）vs Cognito（給自己 App 的終端使用者用）— 常考混淆點，兩者用途不同
- 最小權限落地五招：人走聯合登入、不留 IAM User；程式走 Role、不塞 Access Key；全員（含 root）開 MFA；用 IAM Access Analyzer 依實際用量產出剛好的 policy；用 credential report（CSV，列每個 User 的密碼/金鑰/MFA 狀態）定期檢查
- 金鑰常見外洩路徑：忘了 .gitignore 就推上 GitHub、貼進 AI 對話除錯、hard code 在程式裡、筆電或 CI 環境被拿走 → 記得用 Gitignore 模板、取消已追蹤文檔的追蹤

## 三、Well-Architected 六大支柱與共同責任模型

- 六大支柱：
  - **營運卓越** Operational Excellence：小步、頻繁、可逆的變更
  - **安全性** Security：身分為本、每層都防、可追溯（本單元主題）
  - **可靠性** Reliability：自動從失敗復原、水平擴展、不猜容量
  - **效能效率** Performance Efficiency：用對資源、不猜容量
  - **成本最佳化** Cost Optimization：用多少付多少
  - **永續性** Sustainability：提高使用率
- 易混淆考點：評估「上雲準備度」用 **CAF**（Cloud Adoption Framework），不是 Well-Architected（WA 評的是架構設計本身，可用 **Well-Architected Tool** 實際自評）
- 共同責任模型：AWS 管實體機房/硬體/網路/虛擬化層；你管資料/身分權限/OS 補丁；分界線隨服務移動（EC2 你要管 OS，Lambda/S3/DynamoDB 這類全代管服務你不用管底層）

## 四、成本控制四工具（依時間排）

- **事前估**：Pricing Calculator（還沒開資源先算多少）
- **當下守**：Budgets（設門檻發告警）+ Budget Action（到門檻自動套限制性 policy 或停機）
- **事後看**：Cost Explorer（畫圖找大戶）+ Cost and Usage Report／CUR（最細逐筆帳單，財務對帳用）
- **歸屬**：Cost Allocation Tags（標籤要先在 Billing 啟用才會出現在帳單，啟用後最多 24 小時才顯示）
- 多團隊分帳靠多帳號（Organizations）；同帳號內分攤靠標籤
- Budget Action 是唯一會「動手」的：到 80% 只通知，到 100% 可自動套一份 Deny policy（如 `Deny ec2:RunInstances`）到指定 user/group/role，或直接停 EC2/RDS

## 五、Agent 的權限與 LLM 的錢

- Agent 是員工不是分身：給它自己的識別證（Role），不能借用你的 Access Key；也給它自己的預算
- Bedrock InvokeModel 權限可細到指定模型 ARN（如只准叫 `anthropic.claude-*`），用意是成本控制（不讓 agent 跳去用最貴模型）與合規（不讓用未核准模型）
- 傳統雲端按時間計費，上限算得出來（一台 EC2 一個月最多 730 小時）；**LLM 按輸入/輸出 token 分別計價，呼叫次數沒有自然上限**，迴圈跑歪會一直燒錢（「忘了關是漏水，agent 跑歪是水管爆掉」）
- 如何防止 Agent 持續呼叫模型？每個 agent 都要有三個寫在程式碼裡的上限（比 Budgets 反應更快）：
  1. 最大步數（agent 最多想幾輪）
  2. 逾時（單次呼叫最久幾秒）
  3. 每次呼叫最大輸出 token
  - Budgets + Budget Action 是這三道防線之後的第二道保險

[作業]

## 一、核心實作：空帳號四步，三人團隊

（分層評分：必做 70% / 進階 20% / 加分 10%）
情境：拿到一個全新空帳號，老闆說每月不要超過 30 美元，四步做完才算能用：

1. 必做一: root 開 MFA, 不留 access key
2. 必做二: 用 Identity Center 開自己的身分
3. 必做三: CLI 開 admin 跟 dev 兩個 profile
4. 必做四: 兩筆預算, 月預算 30 美元
5. 進階: 加進阿德跟小美, 先寬後收緊
6. 加分: Budget Action 自動煞車

## 二、六份短版回家作業（略，可參考）

1. **選區**：用選區四問替專題選一個 Region，每個問題一行理由，交五行
2. **讀 policy**：挑一份官方 policy 範例，每條 Statement 寫成一句中文，交三到五句
3. **身分圖**：畫你本人、CI 流程、AWS 上的程式各用什麼身分，交一張圖加三行
4. **六根柱子**：拿一個做過的選擇，六根柱子各寫一行加分/扣分/無關，交六行
5. **估一個月**：用 Pricing Calculator 估專題一個月費用，再寫預算門檻，交連結加一行
6. **Agent 的 policy**：寫一份 policy + 三個上限（最大步數/逾時/最大輸出 token），各給數字跟理由，交 JSON 加三行
