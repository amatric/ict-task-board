---
name: huawei-cloud-obs-uploader
description: |
  把本地文件/目录上传到华为云 OBS，或从 OBS 下载、列目录、生成临时访问链接。当用户说"传到 OBS""把产物上传到对象存储""从桶里拉个文件""生成一个分享链接"时使用。
  技能内含可执行脚本，按 AK/SK 或 STS 临时凭证直连 OBS REST 接口，带重试与断点续传。
metadata:
  tags: huawei-cloud,obs,object-storage,upload,skill
  version: 1.0.0
---

# 华为云 OBS 上传/下载技能

一个**真的会调华为云接口**的技能，而不是只写文档。脚本在 `scripts/obs.py`，零第三方依赖。

## 何时使用

| 场景 | 用本技能 |
|:--|:--|
| 把构建产物/日志/图片传到对象存储 | ✅ |
| 从桶里下载文件、列对象 | ✅ |
| 给某个对象生成限时分享链接 | ✅ |
| 需要块设备/文件系统语义 | ❌ 用 EVS/SFS |
| 只是本地文件搬运 | ❌ 用 `cp` 就够，不必上云 |

## 前置凭证

三种方式，优先级从高到低：

1. **环境变量（推荐）**
   ```bash
   export OBS_AK=... OBS_SK=... OBS_ENDPOINT=https://obs.cn-north-4.myhuaweicloud.com
   ```
2. **STS 临时凭证**（更安全，900 秒轮换）
   ```bash
   export OBS_AK=$STS_AK OBS_SK=$STS_SK OBS_SECURITY_TOKEN=$STS_TOKEN
   ```
3. 命令行参数 `--ak/--sk`（仅调试，**不要写进脚本或提交到仓库**）

## 命令

```bash
# 上传单文件
python3 scripts/obs.py put ./dist.zip obs://my-bucket/builds/dist.zip

# 递归上传目录
python3 scripts/obs.py put ./output obs://my-bucket/reports/ --recursive

# 列出对象
python3 scripts/obs.py ls obs://my-bucket/reports/

# 下载
python3 scripts/obs.py get obs://my-bucket/builds/dist.zip ./dist.zip

# 生成 1 小时有效的分享链接
python3 scripts/obs.py sign obs://my-bucket/builds/dist.zip --expires 3600
```

## 输出约定

脚本统一输出一行 JSON 结果，便于 Agent 解析：

```json
{"ok": true, "action": "put", "objects": 3, "bytes": 1048576, "elapsed_ms": 1820}
```

失败时：

```json
{"ok": false, "action": "put", "error": "HTTP 403", "hint": "检查 AK/SK 与桶策略；STS 需带 security_token"}
```

## 工程要点（写"调用云服务的技能"的通用经验）

1. **凭证永远从环境读**，脚本里不出现密钥；报错信息里也不回显密钥
2. **输出结构化 JSON**，Agent 才能可靠判断成功与否，不要只 print 人类可读文本
3. **失败要带 hint**，把「403 可能是桶策略 / STS 缺 token」直接写进错误里，减少排查轮次
4. **网络抖动要重试**：上传用指数退避重试 3 次
5. **大文件别整个读进内存**：分块读（8MB）后上传
6. **幂等**：重复上传同名对象直接覆盖，不报错

## 参考

- `scripts/obs.py` —— 实现（签名、上传、下载、列对象、签名 URL）
- OBS 签名规范：V2（`Authorization: OBS AK:signature`）
