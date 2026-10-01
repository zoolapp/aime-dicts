# AIME 在线词库

AIME 输入法的词库源，由 [ZOOL](https://zool.app) 维护。
每个词表都是一个纯文本文件；[固定版本下载](https://github.com/zoolapp/aime-dicts/releases/tag/v2026.10.01)含 TXT、RIME 词典与 SHA-256，使用方式见 [发行说明](docs/releases.md)。

也适用于任何 RIME 前端：词条行与 RIME `dict.yaml` 的词条部分兼容。

## 词表

| 词表 | 说明 | 链接 |
|---|---|---|
| AI 公司与产品 | OpenAI、Anthropic、DeepSeek、Claude、ChatGPT 等，按正确大小写上屏 | [`feeds/ai-companies-products.txt`](feeds/ai-companies-products.txt) |
| AI 与开发术语 | 大模型、智能体、提示词、RAG、向量数据库等 | [`feeds/ai-terms-dev-tools.txt`](feeds/ai-terms-dev-tools.txt) |
| 互联网品牌与热词 | 平台、品牌与 2026 年常见流行语 | [`feeds/internet-brands-platforms.txt`](feeds/internet-brands-platforms.txt) |

发现目录：`https://raw.githubusercontent.com/zoolapp/aime-dicts/main/index.json`。
`index.json` 的词表地址固定到 `v2026.10.01`，包含版本、SHA-256、字节数、许可和署名。
三表各 160 条；合并去重后为 471 条。订阅下载后在本机查询，不上传输入内容或 userdb。

## 版本化构建

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py --revision HEAD --version 2026.10.01 --repository https://github.com/zoolapp/aime-dicts --output dist/2026.10.01
```

发行包包括 TXT、RIME 词典、来源 commit、署名和 SHA-256；输出目录必须不存在。

## 格式

```
# 注释行以 # 开头
词条<TAB>拼音（音节以空格分隔，ü 写作 v）<TAB>权重（1–100）
```

英文词条的编码为小写字母与数字（`DeepSeek	deepseek	98`）。只写词条、不写拼音也可以，AIME 会在本机生成拼音。

## 贡献

欢迎 PR 补充词条：只收录已有一定传播度的词；品牌以官方写法为准；不收录人身攻击、低俗或政治敏感内容；
一次 PR 聚焦一个词表。

## 许可

词表内容以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh-hans) 发布。
构建与验收工具代码使用 [MIT](LICENSE-CODE)。
