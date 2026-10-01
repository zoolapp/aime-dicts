# 词库发行包

维护仓库为 `zoolapp/aime-dicts`；固定发行版本为 `v2026.10.01`。
`SOURCE.json` 记录公开仓库与完整源 commit；没有传入 `--repository` 的离线构建仍标记 `publicationStatus: pending`。
线上验收证据见 [发布记录](publication-2026-10-01.md)。

## 构建

无需第三方依赖，Python 3 + Git 即可。在仓库根目录运行：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py --revision HEAD --version 2026.10.01 --repository https://github.com/zoolapp/aime-dicts --output dist/2026.10.01
```

构建读取指定 Git commit 中的词表、目录与许可，忽略未提交内容；新增词条必须先提交。
输出目录必须不存在，防止覆盖已有产物。发布时记录完整 `sourceCommit` 和构建工具所在的 commit。
同一工具版本、源 commit 与版本号生成逐字节相同的 ZIP：成员排序、固定时间、权限与无压缩格式，
不包含本机路径或构建时刻。全量 ZIP 及其 `.zip.sha256` 位于输出目录，其他文件也展开保存。

## 包内内容

- `feeds/`：三份可导入 AIME 的 TXT，保留每表词条与权重。
- `rime/`：每表独立 `.dict.yaml` 与合并的 `aime_online.dict.yaml`。
- `SOURCE.json`：完整源 commit、原始目录与词表 SHA-256。
- `LICENSE`、`ATTRIBUTION.txt`：CC BY 4.0、作者与转换说明。
- `manifest.json`：版本、计数、合并规则与内容文件的 SHA-256、字节数。
- `SHA256SUMS`：校验所有内容文件与 manifest；自身不校验自身。ZIP 校验值在包外。

当前三表各 160 条，共 480 条；跨表相同文字与编码共有 9 条重复，合并词典为 471 条。
合并时取最高权重，按首次出现顺序排列；各独立词表不变。
计数由源文件计算，不写死在构建工具里。TXT 头注释改为真实 commit 与许可，清除历史个人地址。

## 校验与使用

```sh
cd dist/2026.10.01
shasum -a 256 -c aime-vocabulary-2026.10.01.zip.sha256
shasum -a 256 -c SHA256SUMS
```

AIME 可用 TXT 做本地词库导入。RIME 使用者可将合并词典放入自己的配置目录，在自定义方案的
`translator/dictionary` 中选择 `aime_online`；也可从已有词典的 `import_tables` 引入它，再部署。
词典结构遵循 [RIME 官方方案教程](https://github.com/rime/home/wiki/RimeWithSchemata)，禁用预设词汇，避免额外数据混入。
不要直接覆盖已有词典或把此发行包当成完整拼音方案。

可用已经构建好的 AIME CLI 做真实引擎验收，命令只创建临时目录，不安装、不写入当前输入法配置：

```sh
python3 scripts/verify_rime.py --cli /absolute/path/to/aime --package dist/2026.10.01 --evidence build/rime-check
```

验收编译合并词典并检查三份词表的代表词候选（DeepSeek、智能体、松弛感）；
JSON 和日志记录引擎产物、CLI 哈希与退出码，不代表每条词的全拼、双拼都已实测。

## 公开发布前

固定版本 Release 上传后，匿名下载并校验 ZIP、包内全部文件及三份订阅 TXT；
目录经 main 发现版本，实际下载固定到 tag，更新时增加新 tag，不覆盖已发布版本。
官网旧快照保持不变。现有 AIME 通用订阅器不自动验证目录中的 SHA-256；调试验证器会核对下载字节及哈希。
CC BY 4.0 适用于本仓库原创词表；不包含第三方完整词库，也不表示品牌授权或背书。
