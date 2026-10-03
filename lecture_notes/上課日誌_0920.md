# 0920 摘要：d07 下半 + d08 到負載平衡

**d07（儲存類別與安全）**

- S3 分層：Standard → IA → Glacier，越冷越便宜、取回越慢
- Lifecycle 兩坑：128KB 以下不轉；轉進冷層仍收最低天數費
- 版控桶務必加「非目前版本 N 天後過期」規則
- 安全四道門：Block Public Access、Bucket Policy、IAM、SSE 加密，任一擋即擋
- 分享用 Presigned URL，不公開整個桶
- S3 做 RAG 資料源時，異動後要同步向量索引，否則模型講舊話

**d08（單點失敗～負載平衡）**

- 故障三種：AWS 側、機器側、服務死但機器活著
- 只有負載平衡器的 health check 抓得到「服務死但機器活著」
- ALB（第七層）：依 host/path/header 規則轉發，支援 WebSocket、WAF
- NLB（第四層）：只看 IP/埠，效能更高、可固定 IP
- 選型：高併發或非 HTTP 選 NLB，其餘預設 ALB

**補充**

- 可以往 nvidia DLI 走: https://www.nvidia.com/zh-tw/training/
- 儲存服務冷處理的部分，考試要背一個大概，從 Standard -> Standard IA -> Glacier 的順序
