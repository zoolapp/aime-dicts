# ZOOL 词库公开发行记录

2026-10-01（Asia/Singapore）发布到 [zoolapp/aime-dicts](https://github.com/zoolapp/aime-dicts)。
认证 API 回读仓库归属为 zoolapp、公开、默认分支 main。

- 固定版本：[v2026.10.01](https://github.com/zoolapp/aime-dicts/releases/tag/v2026.10.01)。
- 源 commit：`c696760d8bda6fd4d828b5c269e5476641515c49`。
- ZIP SHA-256：`cdbbcceb7b5fefec7411bebd5ae4276da72902e0f130b8a72edb0952e8410d6f`。
- 三份词表各 160 条，合计 480 条；合并去重后 471 条。
- 目录：`https://raw.githubusercontent.com/zoolapp/aime-dicts/main/index.json`；实际词表 URL 固定到 tag。

实测：6 项 Python 测试通过；两次 ZIP 构建逐字节一致；源码新增差异与三份历史提交 Gitleaks 未检出凭据。
15 个 Release 资产、1 个目录、3 个固定 tag 词表均用匿名 curl 下载，HTTP 200，字节与本地一致。
ZIP 内 12 个文件通过全部 SHA256SUMS；目录词表的 SHA-256、体积、计数均匹配。
RIME 在临时目录实际编译合并词典，DeepSeek、智能体、松弛感三个代表词候选通过；未逐条验收全词库。

本地证据：`build/publication/http-verification.json`、`release.json`、`staged-secrets.json`、`history-secrets.json`、
`rime/rime-verification.json`，原始文件与日志位于忽略目录。
官网既有词表快照仍保持原版本；AIME 官网正式部署与 App 安装包发行不属于本次词库 Release。

现有 AIME 通用订阅器不自动使用目录中的 SHA-256；本次在线验收核对了实际下载字节。
公开 tag 提供稳定来源，首次或离线目录不再指向历史个人仓库。
