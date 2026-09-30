# 2026-10-01 本地发行包验收

D02 通过，D03 公开发布尚未进行。

源 commit：`eafdc53b8a61ed8538d03a7d11582e4f0cb504f5`。
工具版本可用 `git log -1 -- scripts/build_release.py` 获取；本次没有把未提交词表混入发行包。

实测证据存于忽略目录 `build/release-audit/`：

| 验收 | 实际结果 | 证据 |
|---|---|---|
| 工具测试 | `Ran 5 tests ... OK`；包含脏工作树隔离、路径穿越、注释注入、计数、数量上限与防覆盖 | `tests.log` |
| 两次构建 | ZIP 逐字节一致 | `package-verification.json` |
| 逐文件核对 | 解包 12 个成员、所有内部校验值、原许可与署名通过 | `package-verification.json`、`unpacked/` |
| 词条核对 | 每表 160 条，源 commit、官网旧快照及生成的独立 RIME 词典逐行一致 | `package-verification.json` |
| 合并规则 | 480 条原始记录，471 个不同文字/编码；9 条跨表重复取最高权重 | `package-verification.json` |
| 真引擎导入 | RIME 生成 table、prism、reverse 文件；3 次 CLI 均退出 0，候选含 DeepSeek、智能体、松弛感 | `rime-verification.json`、`rime-{1,2,3}.log` |

本地 ZIP：`build/release-a/aime-vocabulary-2026-10-01.zip`。
SHA-256：`5e9c314e8c7e134d9e7b04f9f760a5f02fa09311a4b24424c256d8614ec44a5f`。
第二份包位于 `build/release-b/`；两份源码固定在上述 commit，版本号相同。

真实 RIME 验证使用已有 AIME debug CLI，其 SHA-256：
`64d89c998d1dadd2c2f8bc255258c2e83724c64b44afbec2dd6bc8a4ebc5c350`。
只在一次性临时 shared/user 目录编译，关闭用户词典，未安装或重载当前输入法。
此验证证明合并词典可编译及三个代表词可检索；未逐一实测 471 条或双拼方案。

公开公司仓库、固定版本下载 URL 和 App 在线订阅目录属于下一项 D03。
官网已验收的旧资源快照保持原版本与原哈希；本次包的头注释、来源信息和合并词典不同，不能混用哈希。
