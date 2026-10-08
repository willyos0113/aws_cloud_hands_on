# DNS 與內容分發

> 來源：`lectures/第 11 單元 DNS 與內容分發.pdf`（共 90 頁；定價與額度為講義 2026-09-24 查閱的數字）

**今日目標**：替自己的網域接上 CloudFront，桶維持不公開，改檔後知道怎麼讓全世界換新版。

**六個名詞**

| 名詞                   | 意思                                                            |
| ---------------------- | --------------------------------------------------------------- |
| DNS                    | 把網域名稱翻成 IP 位址的全球查號台；Route 53 是 AWS 的 DNS 服務 |
| 託管區域 hosted zone   | Route 53 裡一個網域底下所有記錄的容器，查詢的最後一站           |
| 存活時間 TTL           | 答案可以被快取幾秒；DNS 與 CloudFront 都用它                    |
| 別名記錄 Alias         | Route 53 專屬的擴充，直接回 AWS 資源當下的位址                  |
| 邊緣位置 edge location | 離使用者最近的 AWS 快取機房，又叫 POP                           |
| 來源 origin            | 放原始檔案的地方，例如 S3 桶或任何 HTTP 伺服器                  |

---

## 一、名字怎麼變成位址

**三件事**

- 查詢一路轉問，託管區域是最後一站
- IP 會變的 AWS 資源，接名字用 Alias
- 同名多筆記錄，路由策略決定回哪一筆

**一筆查詢怎麼走**

1. 瀏覽器問遞迴解析器（ISP 的 DNS，替你一路問到底並把答案記 TTL 秒）
2. 解析器先問根、再問 `.com`，每一站只告訴你下一站是誰
3. 問到託管區域（Route 53 name server）才有答案
4. 拿到 IP 後，網頁請求直連目標（例如 ALB），不再經過 Route 53

**三種記錄回三種東西**

| 記錄  | 你填什麼                   | 解析器拿到什麼     | 根網域 | 查詢收費                   |
| ----- | -------------------------- | ------------------ | ------ | -------------------------- |
| A     | 一個 IPv4 位址             | IP，一次查完       | 能     | 收                         |
| CNAME | 另一個名字                 | 名字，還要再查一次 | 不能   | 收；指到同區域的名字算兩次 |
| Alias | AWS 資源或同區域另一筆記錄 | 資源當下的位址     | 能     | 指向 AWS 資源免費          |

- IPv6 版的 A 記錄叫 AAAA
- Alias 是掛在既有型別上的開關：選 A 或 AAAA 再打開它；`dig` 看到的是你選的型別，看不出 Alias

**根網域（zone apex）要指到 CloudFront：答案是 Alias**

| 想做的事                      | 天真做法                    | 結果                           | 正解                                    |
| ----------------------------- | --------------------------- | ------------------------------ | --------------------------------------- |
| `www` 指到 CloudFront         | `www` CNAME 到 distribution | 建得起來，但收查詢費、多查一次 | `www` Alias 到 distribution             |
| `example.com` 指到 CloudFront | 根網域 CNAME                | 建不起來                       | 根網域 Alias 到 distribution            |
| `example.com` 指到 `www`      | 根網域 CNAME 到 `www`       | 建不起來                       | Alias 到 `www` 那筆（那筆不能是 CNAME） |

IP 會變的資源用 A 記錄指，位址一跑就斷；CNAME 又碰不了根網域，所以 Alias 是標準做法。

**TTL 長省錢，改 IP 生效就慢**

- TTL 300：每個解析器從拿到答案起五分鐘內都用手上這份；**各自倒數，不是全世界一起**
- 改設定的順序：先把 TTL 縮到 300 秒 → 等舊答案陸續到期 → 再改 IP → 確認沒問題再拉長
- 託管區域自帶 NS（網域歸哪幾台伺服器管）與 SOA（區域基本資料）兩筆
- 網域在別家買的：自己建同名託管區域，到註冊商把 name server 換成 Route 53 給的四個

**路由策略：同一個名字，回哪一筆**

四種要會用（前三種是平常怎麼分，故障切換是出事怎麼換）：

| 策略              | 挑法                             | 每筆多填                       | 典型場景          |
| ----------------- | -------------------------------- | ------------------------------ | ----------------- |
| 簡單 Simple       | 一個名字一筆記錄，照填的值全部回 | 沒有                           | 單一伺服器        |
| 加權 Weighted     | 依權重比例回，權重 0–255         | Weight、Record ID              | 新版先給 10% 流量 |
| 延遲 Latency      | 回 AWS 量到延遲最低的區域        | Region                         | 多區域部署        |
| 故障切換 Failover | 主要健康回主要，不健康才回次要   | Primary 或 Secondary、健康檢查 | 主站加維修頁      |

另外四種認得名字就好：

| 策略                  | 一句話                                | 什麼時候想到它                 |
| --------------------- | ------------------------------------- | ------------------------------ |
| 地理位置 Geolocation  | 看使用者在哪個洲、國家                | 內容只在有授權的地區提供       |
| 地理鄰近 Geoproximity | 看人與資源的距離，bias 可放大縮小範圍 | 手動把流量從 A 區推一些到 B 區 |
| 多值回答 Multivalue   | 最多回八筆健康的記錄                  | 沒有 ALB，想用 DNS 做一點分流  |
| IP 位址 IP-based      | 你上傳來源 IP 段對端點的表            | 特定 ISP 導到特定端點          |

- **加權**：比例是「這筆權重除以總權重」；要停掉一邊把權重改 0，不用刪記錄（灰度上線）。這是 DNS 回答的比例，解析器會快取，實際請求數只是大致照比例走
- **延遲**：依 AWS 量到的網路延遲，**不是看地圖距離**；資料會隨時間變，且只涵蓋 AWS 區域
- **地理位置**：記得多建一筆 Default，否則 IP 對不到地區時 Route 53 回「沒有答案」

**一筆 A 記錄填兩個 IP，夠不夠？**

- ✗ 大家通常會想：東京、奧勒岡兩個 IP 填同一筆，Route 53 會幫我分流
- ✓ 實際上：簡單路由把全部的值隨機排序回給解析器，不判斷誰近、也不做健康檢查；掛了照樣回。要挑，就建同名多筆記錄配路由策略

**查詢費（每月前十億次的單價）**

| 策略                                 | 每百萬次查詢 |
| ------------------------------------ | ------------ |
| 標準：簡單、加權、故障切換、多值回答 | 0.40 美元    |
| 延遲                                 | 0.60 美元    |
| 地理位置、地理鄰近                   | 0.70 美元    |
| IP 位址                              | 0.80 美元    |

兩個例外不算錢：指向 AWS 資源的 Alias，以及私有託管區域的查詢。

**動手做：用 dig 看 CNAME 與 TTL（CloudShell，0 元）**

```bash
dig +noall +answer www.amazon.com   # 看到 CNAME 鏈與最後的 A 記錄；第二欄是剩餘 TTL 秒數
dig +noall +answer amazon.com       # 根網域只有 A 記錄，沒有 CNAME
dig +noall +answer d1.awsstatic.com # 可能看到 CNAME 指到 cloudfront.net 結尾的名字
```

**CCP 考點**

- 「提供 DNS 解析功能」→ Route 53（CloudFront 是誘答，它靠 DNS 導人但自己不是 DNS 服務）
- 「延遲路由、地理 DNS、地理鄰近、加權輪詢」這串是 Route 53 的路由策略，不是 CloudFront

## 二、壞了，自動換一條路

**三件事**

- 很多檢查器投票，超過 18% 說好就算健康
- 故障切換是路由策略加健康檢查的組合
- 最壞斷線時間：判定時間加上舊答案的 TTL

**一個檢查器怎麼評分**

- HTTP / HTTPS：4 秒內連上，2 秒內收到 2xx 或 3xx 才算過
- TCP：只看連不連得上，10 秒內連上就算
- 間隔選每 30 秒（Standard）或每 10 秒（Fast）；連續失敗到 Failure threshold 次數才翻成不健康
- 彙總規則：回報健康的檢查器**多於 18%** 就算健康（算的是檢查器數目，不是地區數）

**三種健康檢查**

| 類型              | 監控什麼                               | 什麼時候用                 |
| ----------------- | -------------------------------------- | -------------------------- |
| 監控端點          | 一個 IP 或網域，用 HTTP、HTTPS、TCP 敲 | 最常見，敲網站或 API       |
| 計算型 calculated | 其他健康檢查的狀態，最多 255 個        | 三台裡至少兩台活著才算健康 |
| CloudWatch 警報   | 一條指標的資料流                       | 拿內部指標當判準           |

字串比對：回應前 5,120 個位元組要出現指定字串，抓得到「活著但回錯誤頁」的假健康。

**HTTPS 檢查說健康，憑證可能已過期**

- ✗ 大家通常會想：HTTPS 健康檢查會順便驗證憑證
- ✓ 實際上：HTTPS 檢查不驗證憑證，只看連上與 2xx / 3xx；憑證到期要另外監控。剛建好的檢查，資料不夠前也算健康

**Route 53 挑記錄的四條規則**

| 規則 | 內容                                       |
| ---- | ------------------------------------------ |
| 一   | 沒掛健康檢查的記錄，永遠算健康             |
| 二   | 全部不健康時，全部算健康，照策略挑         |
| 三   | Secondary 沒掛檢查，Primary 一壞就盲切過去 |
| 四   | Primary 與 Secondary 都不健康，回 Primary  |

- 用 Failover 是主備；用加權、延遲多半是多活
- Alias 指 ALB 時不另建檢查，把 Evaluate Target Health 設成 Yes；指 CloudFront 時不能開

**最壞斷線時間 = 判定時間 + TTL**（講師的簡化估算）

1. 判定時間：間隔 × 失敗門檻，例如 30 秒 × 3 次 ≈ 90 秒才判定不健康
2. TTL：判定前拿到的舊答案還要活多久；第 89 秒查到的答案，TTL 300 就活到第 389 秒
3. 到期後還要下一次查詢與連線；正在失敗的連線不會自己搬到備援

- 官方建議掛健康檢查的記錄 TTL 設 60 秒以內
- 跨區域的標準長相：東京 ALB 當 Primary、維修頁 S3 桶當 Secondary

**CCP 考點**

- 「某個地理區域發生天災仍要運作」→ 跨多個 Region 部署 EC2；邊緣位置是快取點不能跑 EC2，Local Zones 是某個 Region 的延伸，不算另一個 Region

## 三、快取放在門口，桶不用公開

**三件事**

- 邊緣位置命中就回，沒中才回來源拿
- OAC 讓 CloudFront 簽名讀桶，桶維持不公開
- 改檔後邊緣不會自己知道：等 TTL、失效或換檔名

**一個請求在 CloudFront 裡走的路**

```
瀏覽器 → 邊緣位置（POP） → 區域邊緣快取 → 來源 S3 桶
          命中：直接回       多個 POP 共用     Block Public Access 全開
          沒中：往後問       容量更大的一層     只認 CloudFront 簽過名的請求
```

回程沿路都存一份，下一個人就命中。

**distribution（分發設定）**

- 建好拿到一個 `dxxxx.cloudfront.net` 的名字，路徑照舊，只換網域
- 檔案在邊緣預設放 24 小時（最短 0 秒、沒有上限）
- 用自己的網域要做三件事：填備用網域、掛 ACM 憑證（免費簽發與續期）、用 Alias 指過來

**桶要不要公開？**

| 做法                | 桶要不要公開                 | 現在該不該用                   |
| ------------------- | ---------------------------- | ------------------------------ |
| 桶設成公開讀        | 要，Block Public Access 得關 | 不該；任何人可繞過 CloudFront  |
| OAI（舊版專用身分） | 不用                         | 舊專案才看到，官方建議搬到 OAC |
| OAC                 | 不用，四個開關全開           | 該；也支援 KMS 加密的物件      |

**OAC 拆開看：CloudFront 簽名，S3 驗章**

1. CloudFront 這一半：Signing behavior 選 Sign requests，送往 S3 的每個請求都帶 SigV4 簽章，一律走 HTTPS
2. S3 這一半：桶政策一條 Allow，Principal 是 `cloudfront.amazonaws.com`，Action 是 `s3:GetObject`
3. **Condition 的 `AWS:SourceArn` 是必要的**：少了它，任何 distribution 都能讀你的桶

- 使用者直接打 S3 網址：沒有簽章、也不是 CloudFront → `AccessDenied`
- OAC 鎖的是入口，檔案仍可經 CloudFront 網址看到；要限制誰能看內容，另外用簽章 URL

**開了靜態網站託管，OAC 就用不上**

- ✗ 大家通常會想：來源填 `s3-website` 那個網站端點，再加 OAC
- ✓ 實際上：網站端點是 HTTP 的自訂來源，OAC 選項不會出現，桶就得公開，也不支援 HTTPS。來源要填一般桶端點（`桶名.s3.ap-northeast-1.amazonaws.com`），精靈按 Browse S3 選桶就會填成這種

**快取行為（cache behavior）：三個問題**

1. **哪條規則**：路徑比對由上往下、先中先贏；預設行為樣式固定是 `*`，永遠墊底
2. **放多久**：來源開價（`Cache-Control`），政策定範圍（Min / Default / Max TTL）
3. **改檔後怎麼趕走舊的**：失效或版本化檔名

- `*` 比對零到多個字元、`?` 剛好一個，大小寫有別
- **順序排錯會出安全問題**：`/private/*` 排在 `*.mp4` 後面，私人影片就被直接放行

**放多久**

| 情況                          | 邊緣位置放多久                        |
| ----------------------------- | ------------------------------------- |
| 來源沒給 `Cache-Control`      | Default TTL；不掛政策時 24 小時       |
| 來源給 `max-age=3600`         | 用它，但夾在 Min 與 Max 之間          |
| Min 大於 0，來源給 `no-cache` | 照樣至少放 Minimum TTL                |
| 受管政策 CachingOptimized     | Min 1 秒、Default 24 小時、Max 365 天 |
| 受管政策 CachingDisabled      | 三個都是 0，等於不快取                |

**轉給來源，不等於分開存**

- Cache policy：放多久、哪些請求算同一份（預設看網址，可再加查詢字串、標頭、Cookie）
- Origin request policy：轉什麼給來源；轉過去的值不拿來區分快取
- **登入 Cookie 只放後者，A 的回應可能回給 B**；要分開存就放進 Cache policy
- CloudFront 只快取 GET 與 HEAD 的回應（OPTIONS 可選）；POST 一律穿過去

**按強制重新整理，CloudFront 就回來源？**

- ✗ 大家通常會想：瀏覽器帶 `no-cache` 上去，CloudFront 會回來源拿新的
- ✓ 實際上：CloudFront 忽略瀏覽器請求裡的 `Cache-Control` 與 `Pragma`，只聽來源跟你的政策；過期後回來源問，沒變就回 304

**改了檔：救急用失效，常態換檔名**

|                    | 失效 Invalidation                      | 版本化檔名                  |
| ------------------ | -------------------------------------- | --------------------------- |
| 做法               | 送一組路徑，例如 `/index.html` 或 `/*` | `app.css` 改名 `app.v2.css` |
| 生效               | 幾秒內開始清，下次請求回來源           | 立刻，新名字沒有快取        |
| 費用               | 每月前 1,000 條路徑免費，`/*` 算一條   | 不用付失效的錢              |
| 瀏覽器與代理的快取 | 管不到                                 | 新網址，一定拿新的          |
| 缺點               | 送出後不能取消                         | HTML 裡的連結要一起改       |

`index.html` 這類固定網址的入口檔，TTL 設短或改版時失效它；額度算路徑數，不算檔案數。

**費用：CloudFront 是少數 Always Free 的服務**

| 項目                     | 免費額度                           |
| ------------------------ | ---------------------------------- |
| 傳出到網際網路           | 每月前 1 TB                        |
| HTTP 與 HTTPS 請求       | 每月前 1,000 萬次                  |
| 來源到 CloudFront 的傳輸 | 來源是 S3、ELB、API Gateway 時免費 |
| 失效                     | 每月前 1,000 條路徑                |

**動手做：用 curl 看網站是不是從 CloudFront 回的（CloudShell，0 元）**

```bash
# -I 只要標頭不要內容；Via 含 cloudfront.net 代表經過 CloudFront
# X-Amz-Cf-Pop 是回應你的邊緣位置代碼；X-Cache 顯示 Hit 或 Miss
curl -sI https://d1.awsstatic.com/ | grep -iE 'via|x-cache|x-amz-cf'
```

**CCP 考點**

- 「用 edge location 快取內容」→ CloudFront（Route 53 也用邊緣位置，但做的是 DNS 回應）
- 「觸及全球觀眾、最低延遲」→ CloudFront；Route 53 只決定導到哪個端點，ELB 是單一區域內分流
- CloudFront 的功能描述：安全地將資料、影片、應用程式和 API 以低延遲傳送給全球使用者

## 四、加速連線，與 AI 應用的邊界

**三件事**

- CloudFront 加速內容，Global Accelerator 加速連線
- 延遲路由只導人，不會替你查模型在哪
- 聊天 API 是 POST，CDN 的快取價值在前端

**兩個都住邊緣，一個存、一個不存**

|            | CloudFront                             | Global Accelerator                          |
| ---------- | -------------------------------------- | ------------------------------------------- |
| 定位       | HTTP 內容分發網路（CDN）               | 固定 IP 的流量加速器                        |
| 協定       | 只講 HTTP / HTTPS                      | TCP 或 UDP 都行                             |
| 快取       | 有，沒中才回來源                       | 不存任何內容，每個請求都到你的伺服器        |
| 位址       | `dxxxx.cloudfront.net`，IP 會變        | 兩個固定的 anycast IP                       |
| 後端       | S3、ALB、任何 HTTP 來源                | ALB、NLB、EC2、Elastic IP                   |
| 強項       | 靜態檔、影片、下載；動態內容也能走骨幹 | 遊戲、IoT、VoIP；防火牆白名單；快速區域切換 |
| 固定費     | 按量計費時沒有                         | 每小時 0.025 美元，停用也照收               |
| 免費額度   | 1 TB 傳出、1,000 萬次請求              | 沒有                                        |
| 掛著一個月 | 0 元                                   | 約 18 美元，加兩個 IPv4 約 25 美元          |

**Global Accelerator 細節**

- anycast IP：同一個 IP 在全球很多邊緣位置同時廣播，封包自然流到最近的那個
- 兩個靜態 IP 來自兩個隔離的網路區塊，一個被擋或故障就改連另一個；白名單兩個都填
- 端點不健康約一分鐘內移出；**已建立的連線不會被搬，新連線才改送**
- 兩種比例：端點權重與流量刻度盤（Traffic dial）
- accelerator 停用時 IP 還在，**刪除才停止收費**

**選型：先問是不是 HTTP**

| 你的流量                    | 選                                           | 為什麼                             |
| --------------------------- | -------------------------------------------- | ---------------------------------- |
| 網站、圖片、影片、下載      | CloudFront                                   | 可快取，命中率高就又快又省         |
| HTTP 的動態 API             | CloudFront 不快取行為，或 Global Accelerator | 都走骨幹；要固定 IP 選後者         |
| UDP 遊戲、IoT 的 MQTT、VoIP | Global Accelerator                           | 不是 HTTP，CloudFront 收不了       |
| 客戶防火牆要 IP 白名單      | Global Accelerator                           | 兩個固定 IP；CloudFront 的 IP 會變 |
| 多區域主備，不靠 DNS 切換   | Global Accelerator                           | 端點健康一變就改送新連線           |

是 HTTP 再問能不能快取：能就 CloudFront；不能但要固定 IP 或快速區域切換，才找 Global Accelerator。

**Global Accelerator 是更強的 CloudFront？**

- ✗ 大家通常會想：Global Accelerator 比較快，靜態網站也放它後面
- ✓ 實際上：它不存任何內容，一萬個人要同一張圖，伺服器就被打一萬次；CloudFront 把一萬次變一次

**三個都能導流量，各管一層**

| 服務               | 管哪一層                                 |
| ------------------ | ---------------------------------------- |
| ALB                | 在一個區域裡，把流量分給後面的機器       |
| Route 53 故障切換  | 改 DNS 答案，受舊答案的 TTL 拖累         |
| Global Accelerator | 在多個區域之間挑一個，同一個 IP 後面改送 |

**網站工具套到聊天機器人，踩空兩次**

| 踩空                                  | 原因                                                | 解法                                              |
| ------------------------------------- | --------------------------------------------------- | ------------------------------------------------- |
| 延遲路由把人導到沒模型的區域          | 延遲路由只看網路；各區域能用的模型不一樣            | 只在有模型的區域建記錄，或改用 Bedrock 跨區域推論 |
| 把 CloudFront 放在 LLM API 前面想快取 | POST 不快取；問題幾乎不重複；串流是給這個人這一次的 | 前端靜態檔走 CDN，API 直達區域                    |

**兩層分開：DNS 導人，設定檔導請求**

- 死路：只在有模型的區域建延遲記錄；換模型時要重新確認，不相容就得改 DNS
- 活路：呼叫跨區域推論（cross-Region inference）設定檔，Bedrock 在允許的區域裡挑一個處理；路由不另收費，走 AWS 內網
- 上線前確認三件事：來源區域在支援清單、IAM 允許所有目的區域、SCP 沒擋

| 設定檔 | 在哪些區域挑               | 資料落地（data residency）         |
| ------ | -------------------------- | ---------------------------------- |
| 地理型 | 美國、歐洲、亞太這類範圍內 | 保證留在那個地理範圍               |
| 全球型 | 所有支援它的商業區域       | 不保證；SCP 要放行區域未指定的請求 |

有法規要求，選地理型。

**拆解「CDN 加速 LLM」：三刀**

1. 方法：聊天是 POST，不快取，連區域邊緣快取都不經過
2. 內容：問題幾乎每次不同，回答帶隨機性，命中率本來就低
3. 形狀：串流回應為這個人這一次生成，快取要嘛沒作用、要嘛回錯人的東西

CloudFront 對聊天 API 剩下的價值是「門」：終止 HTTPS、掛 WAF、走骨幹。**加速不等於快取。**

**該放哪：前端走 CDN，API 直達**

| 流量                        | 放哪                         | 說明                            |
| --------------------------- | ---------------------------- | ------------------------------- |
| `index.html`、JS、CSS、圖片 | S3 加 CloudFront，OAC 鎖桶   | 快取命中率高                    |
| `POST /chat`                | 區域內的 ALB 或 API Gateway  | 直連，或經 CachingDisabled 行為 |
| 模型呼叫                    | 有模型的區域，或跨區域推論   | 延遲路由只導人，不導模型        |
| 自己的網域                  | Alias 指到 CloudFront 與 ALB | `www` 與 `api` 用不同名字分開   |

想省模型費用，找應用層的語意快取：由你的程式判斷哪類問題能重用舊答案。

> CDN 幫你把不會變的東西放到門口；LLM 的回答為每個人各自生成，快取價值幾乎都在前端。

**動手做：查兩個區域各有哪些模型（CloudShell，0 元，只列清單不呼叫模型）**

```bash
# 數東京可用的模型數；把 --region 改成 us-east-1 再比一次
aws bedrock list-foundation-models --region ap-northeast-1 --query 'length(modelSummaries)'
```

**CCP 考點**

- 使用全球邊緣位置的服務：CloudFront 與 Global Accelerator
- 數量關係：邊緣位置 > 可用區域（AZ）> 區域（Region）；邊緣位置不是 AZ，不能開 EC2
- 共同責任模型：為 IAM 使用者實作 MFA 是客戶的責任；Lambda@Edge 的作業系統更新是 AWS 的責任

## 五、實作：S3 靜態前端掛上 CloudFront

零程式碼，全部在主控台點；全程在 Tokyo 區域，用 `course-admin` 登入。CloudFront 與失效都在免費額度內，**預期 0 元，做完當天刪掉**。

**三個重點**

- 桶從頭到尾不公開，匿名只能走 `cloudfront.net`
- 改檔之後邊緣不會自己知道，送失效才換新
- 清理要兩段：先 Disable，等部署完再 Delete

**準備**：在自己電腦建 `index.html`，內容只有一行 `<h1>v1 hello from S3 and CloudFront</h1>`

**必做：八步就及格（70%）**

1. **建桶**：S3 → Create bucket，名稱 `a07-web-` 加英文名或亂數（全小寫、全球唯一），Region Tokyo，ACLs disabled，**Block Public Access 四個勾全部保留**
2. **上傳**：Upload → 選 `index.html`
3. **直接打 S3**：開 `https://桶名.s3.ap-northeast-1.amazonaws.com/index.html`，應該看到 `AccessDenied`
4. **建 distribution**：CloudFront → Create distribution，名稱 `a07-web`，Single website or app，Origin type 選 Amazon S3 並按 Browse S3 選桶，選 Use recommended origin settings（會自動設定 OAC 並更新桶政策）
5. **不開 WAF**：Enable security protections 頁選不啟用 → Create distribution
6. **等部署**：Last modified 從 Deploying 變成日期時間（通常幾分鐘），複製 Distribution domain name
7. **兩個網址各開一次**：CloudFront 網址看到 v1；S3 網址仍是 `AccessDenied`；桶政策多了一條 Principal 為 `cloudfront.amazonaws.com`、Condition 為 `AWS:SourceArn` 的 Allow
8. **改檔與失效**：v1 改成 v2 覆蓋上傳，重新整理多半還是 v1 → Invalidations → Create invalidation，Object paths 填 `/*` → 等 Status 變 Completed 再重新整理看到 v2

**為什麼改成 v2 還是看到 v1**

- 建議設定給的是 CachingOptimized，Default TTL 24 小時，從邊緣第一次存下這份起算
- 重新整理帶的 `no-cache`，CloudFront 不理
- 冷門檔案可能提早被清，直接看到 v2 也正常；照樣送失效，Status 到 Completed 就算完成

**進階（20%）**

- 在桶裡建 `api` 資料夾，上傳 `ping.json`（內容 `{"ok":true}`）
- Behaviors → Create behavior：Path pattern `/api/*`、同一個桶、Cache policy 選 CachingDisabled
- 部署完用 CloudShell 各打兩次，比較 `x-cache`：

```bash
curl -sI https://<distribution 網域>/index.html    | grep -iE 'HTTP/|x-cache'  # 第二次應為 Hit from cloudfront
curl -sI https://<distribution 網域>/api/ping.json | grep -iE 'HTTP/|x-cache'  # 兩次都是 Miss（不快取，狀態碼仍是 200）
```

**加分（10%，二選一）**

- **安全標頭**：Default (\*) 行為 → Response headers policy 選 SecurityHeadersPolicy；回應多出 `x-content-type-options: nosniff`、`x-frame-options: SAMEORIGIN`、`strict-transport-security` 等標頭
- **版本化檔名**：內容改成 v3 另存 `index-v3.html` 上傳，開新網址立刻是 v3，不用失效

**卡住了：提示卡**

| 卡在哪                                 | 怎麼辦                                         |
| -------------------------------------- | ---------------------------------------------- |
| 建桶說名字已被使用                     | 桶名全球唯一，換一組亂數                       |
| 直接打 S3 是 `NoSuchKey`               | 檔名大小寫不對，或上傳沒成功                   |
| 找不到 Use recommended origin settings | 手動選 OAC、Create new OAC，複製政策貼到桶     |
| CloudFront 網址回 `AccessDenied`       | 看桶政策有沒有 `cloudfront.amazonaws.com` 那條 |
| 失效完還是 v1                          | 換無痕視窗，或在 CloudShell 用 curl 看         |

**不要啟用 WAF**：那會建一個另外收費的 web ACL。

**清理（順序不能反）**

1. CloudFront → 勾 `a07-web` → Disable（Last modified 又變 Deploying）
2. 等 Last modified 變回日期時間 → Delete（按不下去就是還在部署，再等）
3. S3 → 勾桶 → Empty → 輸入桶名
4. 再勾同一個桶 → Delete → 輸入桶名
5. 選作：CloudFront 左邊 Origin access 刪掉自動建的 OAC（沒有別的 distribution 在用才刪；留著也不收費）

**實作繳交：三張截圖加一句話**（刪資源之前先拍好）

1. **截圖 1**：CloudFront 網址顯示 v1 或 v2 的頁面
2. **截圖 2**：S3 網址的 `AccessDenied`
3. **截圖 3**：失效的 Status 是 Completed
4. **一句話**：寫失效前後各看到什麼；做了進階附兩組 curl 輸出

驗收比重：必做 70%（三張截圖各 20%、那一句 10%）；進階 Hit 與兩次 Miss 20%；加分 10%。

## 六、回家作業：都拿期末專題來做，一律個人完成(略，參考用)

每一份都接著上一份做，最後得到專題的整條入口設計。

1. **DNS 記錄表**：根網域、`www`、`api` 各指到什麼、型別、TTL、理由
2. **選路由策略**：兩區域求快、單區域給新版 10%，各寫策略與限制
3. **一組故障切換**：Primary、Secondary、TTL，加一條最壞斷線算式
4. **前端送檔路線**：使用者、邊緣位置、來源桶三框，標出 OAC 在哪段
5. **行為表**：靜態、API、預設三列：路徑、來源、快取政策、理由
6. **選邊與拆解**：三種流量選哪一邊；再讓 AI 追問「CDN 加速 LLM」三輪

## Takeaway

1. IP 會變的 AWS 資源接名字用 Alias，根網域尤其如此
2. 故障切換是路由策略加健康檢查；最壞斷線是判定時間加 TTL
3. CloudFront 是門口的快取，OAC 讓桶不用公開；救急用失效，常態換檔名
4. Global Accelerator 加速連線不存內容；聊天 API 是 POST，CDN 的快取價值在前端
