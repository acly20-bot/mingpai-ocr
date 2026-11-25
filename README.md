# 铭牌识别｜当前发布状态（2026-11-25）

- 正式稳定版 **v1.18.6**：https://acly20-bot.github.io/mingpai-ocr/
- 唯一测试版 **v1.18.7-test.2 图片质量专项**：https://acly20-bot.github.io/mingpai-ocr/test-photoquality/

正式基线固定为 `047c22ec7ee7fa6c7058eea0c666aa9c4e97b1d6`，保留 Git 历史及 v1.18.5 回滚基线。测试版直接从正式版网页生成，仅替换图片质量主程序、版本标识和测试缓存标识，保留正式版的底栏自恢复、审核、同步状态实时更新、温湿度、Excel 导出和 86 条识别规则（r10）。
正式 COS 主程序为 `index-B81hyAdU-v1186-test1-qqgpu-thumbfix.js`，测试主程序为 `index-B81hyAdU-v1187-photoquality-test1.js`。微信导出 SCF v1.0.9 已实机通过。
停止发布旧稳定测试入口、已否定的 v1.18.7-test.1 界面原型及 Edge 临时诊断入口；保留历史分支，不删除浏览器数据或 COS 资源。
先完成图片质量专项回归，再进行设备信息界面优化；待审核铭牌文本按正式版逻辑展开、确认后收起。Edge 偶发静态预览接受手动刷新；微信图片下载限制暂缓。

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
