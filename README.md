# 铭牌识别｜v1.18.4.5 稳定发布

**正式版 v1.18.4.5**：https://acly20-bot.github.io/mingpai-ocr/

**测试版 v1.18.4.5-test**：https://acly20-bot.github.io/mingpai-ocr/test-adaptive/

## 当前基线（2026-11-21）

- 正式版稳定分支：[`release-baseline/v11845-rules-cpap-r9`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v11845-rules-cpap-r9)
- 正式版固定提交：`505a09ba03730c2de1d72cddbc1bcfea5b7ef1ee`
- 正式版规则：`recognition-rules-v1184.json`，**85 条**，规则修订号 `v1.18.4-20261121-r9`，新增鸽子小儿CPAP产品编号 `20126III012` 纠偏（OCR数字1/字母I混淆）。
- 正式版保留已验证的底栏自恢复、温湿度审核与飞书同步、待审核筛选确认后自动移除、用户选定的统计布局。
- **正在实机测试的独立分支**：[`release-baseline/v11845-bootfix-test`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v11845-bootfix-test)；仅测试入口引入 Huawei/QQ/UC 首次加载超时与重试、减少大 JS 重复预缓存、已确认记录隐藏字段警告。该部分尚未合入正式版。

## 发布规则

- **独立识别规则**：样本和负例自动检查通过后，规则直接同步正式版与测试版，**网页显示版本号不变**；需换用新规则重新识别历史记录，不自动覆盖人工审核数据。
- **页面 Bug/启动/界面修改**：先在测试版回归，再合入正式版，确认不覆盖现有稳定审核和同步功能。
- 记录修改优先使用主程序已有编辑、确认及同步事件，不重新实现第二套状态。
- 完整 Pages 发布来自固定基线分支；精简版工作流在 [`.github/workflows/deploy-paddleocr.yml`](.github/workflows/deploy-paddleocr.yml)。

## 回退

将部署工作流固定 SHA 恢复到上一稳定分支提交并运行发布。历史版本保存在 Git 记录及 `release-baseline/v11845-pending-confirm` 分支。不要删除腾讯云 COS 现用 OCR 主程序和模型。
