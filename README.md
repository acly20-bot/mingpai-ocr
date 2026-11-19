# 铭牌识别｜v1.18.4.5 发布仓库

当前正式版：**v1.18.4.5**；测试版：**v1.18.4.5-test**。统计弹窗恢复为用户选定的自适应列宽样式，正式版继续保留底部快捷栏自恢复保护，版本号不变。已合入底部快捷栏恢复修复；正式版另加入隐藏状态自恢复检查，页面版本号仍不变，版本号不变。

- 正式版：https://acly20-bot.github.io/mingpai-ocr/
- 测试版：https://acly20-bot.github.io/mingpai-ocr/test-adaptive/
- 部署工作流：[deploy-paddleocr.yml](.github/workflows/deploy-paddleocr.yml)
- 完整基线分支：[`release-baseline/v11845-stats-restored-safe`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v11845-stats-restored-safe)，精简前的全部构建源、历史脚本和产物均保留于该分支以及 Git 历史。

## 当前部署原则

GitHub Actions 只从固定基线 **`458318188f8ffc787f709b3422a1f45bf78948eb`** 恢复完整 Pages 产物并进行哈希、版本及 JS 语法校验，不重新生成早期历史版本。COS 中的 OCR 主程序和模型不受本仓库精简影响；飞书 SCF 服务也未修改。

今后如需修复识别规则、审核界面或性能，请**先在独立测试版采用主程序原生成熟机制实现并通过实机回归**，然后创建新固定基线、更新部署工作流中的基线分支/提交及验证哈希，再正式发布。不要直接在当前稳定基线追加未经验证的运行时补丁。

## 回退

若新版本出现异常，可把工作流的固定基线提交恢复到上面的 SHA，并运行工作流重新发布。旧版构建脚本和资源保存在 Git 历史及 `release-baseline/v11844` 分支；最新版完整站点保存在 `release-baseline/v11845-stats-restored-safe` 分支，无需为节省文件数量删除远程回退信息。

> GitHub 主分支保留稳定部署工作流、SCF 文档及本次已验证的修复/发布脚本。历史版本仍可通过 Git 历史找回。
