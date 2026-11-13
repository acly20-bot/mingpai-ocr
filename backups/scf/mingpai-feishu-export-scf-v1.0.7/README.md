# mingpai-feishu-export-scf v1.0.7

腾讯云 SCF 微信导出服务备份。

## 本版修复
- 微信导出严格按“单位名称 + 检定员”双条件筛选。
- 飞书服务端过滤后，再在 SCF 本地进行一次精确匹配校验。
- 保留该组合“最新检定日期向前 7 个自然日”的导出规则。
- 保留温度（℃）与相对湿度（%RH）列。
- 保留 /prepare-export、/prepare-export-v118、/download、/sync-environment。

## SCF 环境变量
- FEISHU_APP_ID
- FEISHU_APP_SECRET
- MINGPAI_SHARED_KEY
- FEISHU_APP_TOKEN
- FEISHU_TABLE_ID

部署时请勿把真实密钥提交到 GitHub。
