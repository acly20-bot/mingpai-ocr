# 铭牌识别｜v1.18.4.4 发布仓库

当前正式版：**v1.18.4.4**；测试版：**v1.18.4.4-test**。

- 正式版：https://acly20-bot.github.io/mingpai-ocr/
- 测试版：https://acly20-bot.github.io/mingpai-ocr/test-adaptive/
- 部署工作流：[deploy-paddleocr.yml](.github/workflows/deploy-paddleocr.yml)
- 完整基线分支：[`release-baseline/v11844`](https://github.com/acly20-bot/mingpai-ocr/tree/release-baseline/v11844)，精简前的全部构建源、历史脚本和产物均保留于该分支以及 Git 历史。

## 当前部署原则

GitHub Actions 只从固定基线 **`780c368e4b3fc3460db3b39d68720e80cc2e5780`** 恢复完整 Pages 产物并进行哈希、版本及 JS 语法校验，不重新生成早期历史版本。COS 中的 OCR 主程序和模型不受本仓库精简影响；飞书 SCF 服务也未修改。

今后如需修复识别规则、审核界面或性能，请**先在独立测试版采用主程序原生成熟机制实现并通过实机回归**，然后创建新固定基线、更新部署工作流中的基线分支/提交及验证哈希，再正式发布。不要直接在当前稳定基线追加未经验证的运行时补丁。

## 回退

若新版本出现异常，可把工作流的固定基线提交恢复到上面的 SHA，并运行工作流重新发布。旧版构建脚本和资源均仍存在于历史提交以及 `release-baseline/v11844` 分支，无需为节省文件数量删除远程回退信息。

> 当前 GitHub 主分支只保留部署所需文件和 SCF 文档；旧版源码的归档并不意味着它们从 Git 历史被清除。
