# mingpai-feishu-export-scf v1.0.8

基线：用户提供的 `mingpai-feishu-export-scf-v1.0.6-v118-test(2).zip`。

## 本版原则
- 完整保留 v1.0.6 的“统计汇总”规则：
  - 列：单位名称 / 设备名称 / 检定日期 / 数量 / 备注
  - 同设备跨日期分行
  - 多日期设备备注显示“总X”
  - 单位名称、设备名称、备注按 v1.0.6 方式合并单元格
  - 单位末尾保留“合计”
- v1.18 微信导出新增严格的“单位名称 + 检定员”双条件。
- 下载令牌同时保存 unitName 与 operatorName，下载阶段再次按同一条件查询。
- 保留 v1.0.6 的温度、相对湿度、/sync-environment 等行为。

## 安全
真实 FEISHU_APP_SECRET / MINGPAI_SHARED_KEY 不提交 GitHub。
