# 铭牌识别｜当前发布状态（2026-11-23）

正式版：**v1.18.6** — https://acly20-bot.github.io/mingpai-ocr/

测试基线：**v1.18.6-test.1** — https://acly20-bot.github.io/mingpai-ocr/test-adaptive/

兼容性验证入口：**v1.18.6-test.1** — https://acly20-bot.github.io/mingpai-ocr/test-v1186/

## v1.18.6 基线与下一阶段

- 正式发布基线：`release-baseline/v1186-verified`，固定 SHA `91d795983fd8cd5a01cc758b2d54dbbf742be2c0`。此前 v1.18.5 原始基线 `release-baseline/v1185-plx-r10`（SHA `37de7dee133a36f70e55b65dbd0ca4bac3bf53d6`）保留回滚。
- 主程序：`index-B81hyAdU-v1186-test1-qqgpu-thumbfix.js`，部署在 COS `assets/`；正式/测试入口引用同一份通过实机测试的主程序，各自独立 Service Worker 缓存。无需覆盖旧 COS 正式版 JS。
- 已确认：QQ 浏览器原生图片工具不再接管缩略图；双指缩放、拖动、重拍照及重识别正常；WebGPU 不兼容时避免跨批次重复无效初始化；QQ 与 Edge 的“保存图片”直接下载通过实机测试；启动不再不必要地重复刷新。
- 已知限制：微信内置浏览器可能拦截 H5 文件下载；Edge 后台恢复的浏览器级“预览此页面”快照无法保证由网页脚本自行恢复。按成本/性能优先原则，不为两者增加全局轮询或强制刷新。
- 正式版额外保留 v1.18.5 的底部快捷栏自恢复保护，避免简单覆盖丢失稳定修复；保留普通审核、温湿度、飞书同步和统计汇总功能。统计中英文括号显示归并及 `~220V/50Hz` 电气提醒已包含在本次基线中。
- 识别规则保持 86 条，`recognition-rules-v1184.json`，规则号 `v1.18.4-20261122-r10`。
- **下一阶段**：`v1.18.7-test.1` 设备信息界面精简原型 — https://acly20-bot.github.io/mingpai-ocr/test-v1187/ 。仅测试新记录卡片布局：OCR 原文默认收起、备注标题精简、字段间距缩小；不修改 COS JS、识别规则或记录结构。保持 v1.18.6 正式及 v1.18.6-test.1 测试基线不动，实机回归后再考虑是否进入 `v1.19.0`。

## 历史记录（2026-11-22）

正式版：**v1.18.5** — https://acly20-bot.github.io/mingpai-ocr/

测试版：**v1.18.5-test.3** — https://acly20-bot.github.io/mingpai-ocr/test-adaptive/

## 当前完整稳定基线

- 发布基线：[`release-baseline/v1185-plx-r10`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v1185-plx-r10)，SHA `37de7dee133a36f70e55b65dbd0ca4bac3bf53d6`。
- 用户已通过 v1.18.5-test.3 的五项实机回归，相关 DOM 观察器与增量 IndexedDB 读取性能改善已合入正式版 v1.18.5。
- 独立识别规则 **86 条**（`recognition-rules-v1184.json`，修订号 `v1.18.4-20261122-r10`）；新增南京普爱移动平板 C 形臂型号 `PLX118F/a` 的精确纠偏，已同步正式版和测试版，不改网页版本号。
- **测试版专用、尚未实机回归**：数据统计分组把中英文括号统一为中文括号；字段黄色电气参数提醒识别以 `~`/`～` 开头的电压频率。统计只归并显示，不修改本地历史记录，也不触发飞书同步。
- 正式版保留底栏自恢复、原生温湿度审核与飞书同步、待审核确认后自动退出筛选、统计页面用户选定的布局。移除旧版启动耗时监听，不保留临时启动诊断条。
- QQ 浏览器的 WebGPU 实际后端未选中，以及点击缩略图被浏览器图片功能接管，仍列为**待独立诊断的兼容问题**。优先保证 Edge、微信及正常浏览器稳定。
- Edge 再次打开旧标签页遇到的“预览此页面”静态快照属已知兼容问题；不再叠加强制刷新。

## 发布与回退

- 精简正式发布工作流 [`deploy-paddleocr.yml`](.github/workflows/deploy-paddleocr.yml) 从固定完整 Pages 基线 SHA 恢复，主程序及 OCR 模型仍由 COS 提供。
- 识别规则可以直接同步正式版与测试版，发布后通过重识别进行实机验证，不改变网页版本号；界面、浏览器兼容和功能修复则先在测试版验证后合入正式版。
- 回滚时将工作流指向上一条已核验的完整基线，重新部署即可；不清除用户现存 IndexedDB 数据。
