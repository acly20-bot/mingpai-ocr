# 铭牌识别｜当前发布状态

正式版：**v1.18.4.5** — https://acly20-bot.github.io/mingpai-ocr/

性能测试版：**v1.18.5-test.2** — https://acly20-bot.github.io/mingpai-ocr/test-adaptive/

## 固定基线与发布策略

- 正式版固定基线：[`release-baseline/v11845-boot-closeout`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v11845-boot-closeout)，SHA `ae214f4a11b0c5c107e97fa4b50deb3a562e7200`。
- 性能测试线基线：[`release-baseline/v1185-test2`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v1185-test2)，SHA `25ddd5634fdf28b8531930fd04a08791153b3fb7`。
- 识别规则：**85 条**，独立 JSON（`recognition-rules-v1184.json`），规则修订号 `v1.18.4-20261121-r9`，保持原有优先级。已包括鸽子小儿CPAP正确产品编号 `20126III012`。
- 正式版已合入用户在 Edge 上验证的启动恢复及已确认记录隐藏风险提示；两个入口已移除临时启动诊断条。正式版保留底部快捷栏自恢复保护、原生温湿度审核和飞书同步、待审核确认后自动移除及选定的统计布局。
- 精简部署工作流：[`deploy-paddleocr.yml`](.github/workflows/deploy-paddleocr.yml)，从稳定 SHA 直接恢复完整 Pages 发布产物，不执行旧版本连续补丁。

## 当前性能测试（尚未合入正式版）

`v1.18.5-test.2` 在 test.1 基础上，记录列表新增或重建卡片时只装饰新卡片，不再对当前页所有卡片反复读取 IndexedDB；第一次加载仍完整初始化，温湿度审核依旧采用成熟原生机制。原生记录保存、IndexedDB 数据格式、OCR、飞书 SCF 均不改变。需要 Edge 上验证列表新增/分页/筛选、温湿度修改确认、批量识别、飞书同步等功能后再继续。Edge 旧标签页静态预览兼容问题单独保留，不作为本阶段性能回归失败依据。

## 开发与回退

- 网页 Bug、性能、UI 变更先更新测试版，用户实机回归通过后再推广正式版、固定新基线；识别规则按约定直接同步正式版与测试版并在发布后实测，网页版本号不随规则修改。
- 后续记录界面优先使用主程序已验证的原生编辑与审核机制。
- 回退可将正式版工作流的固定 SHA 恢复至此前通过的完整基线，再重新部署；不会清空任何 IndexedDB 本地记录。
- 尚未对小米自带浏览器启动进行新的兼容修复；以 Edge 为主要使用目标。
