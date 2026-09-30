# AIME 在线词库

[AIME](https://github.com/foru17/aime) 输入法的公开词库源。每个词表都是一个纯文本文件，
在 AIME 设置 › 词库 › 在线词库 中一键订阅；AIME 每小时检查、每个词表至多 12 小时下载一次，
新词在你停止打字后自动生效，全拼与小鹤双拼都能打出。

也适用于任何 RIME 前端：词条行与 RIME `dict.yaml` 的词条部分兼容。

## 词表

| 词表 | 说明 | 链接 |
|---|---|---|
| AI 公司与产品 | OpenAI、Anthropic、DeepSeek、Claude、ChatGPT 等，按正确大小写上屏 | [`feeds/ai-companies-products.txt`](feeds/ai-companies-products.txt) |
| AI 与开发术语 | 大模型、智能体、提示词、RAG、向量数据库等 | [`feeds/ai-terms-dev-tools.txt`](feeds/ai-terms-dev-tools.txt) |
| 互联网品牌与热词 | 平台、品牌与 2026 年常见流行语 | [`feeds/internet-brands-platforms.txt`](feeds/internet-brands-platforms.txt) |

`index.json` 是 AIME 读取的目录（名称、说明、词条数、原始链接）。

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
