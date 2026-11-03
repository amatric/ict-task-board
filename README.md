# 华为云 OBS 上传/下载 Skill

华为 ICT 大赛云赛道 **赛题10（Skill-如何写好一个调用华为云服务的技能）** 的参评作品。

一个**真的会调华为云 OBS 接口**的技能：`SKILL.md` 定义触发时机与用法，`scripts/obs.py` 用 OBS V2 签名直连 REST，零第三方依赖。

## 为什么这个技能"能跑"而不是"只有文档"

很多技能只写清"你应该调用 XX 接口"，Agent 读完还得自己拼签名。本技能的脚本把**签名、重试、分块、结构化输出**都做完了，Agent 只需：

```bash
python3 scripts/obs.py put ./dist.zip obs://my-bucket/builds/dist.zip
```

返回一行 JSON，Agent 可直接判断成败：

```json
{"ok": true, "action": "put", "objects": 1, "bytes": 1048576, "elapsed_ms": 1820, "bucket": "my-bucket", "prefix": "builds/dist.zip"}
```

## 四个子命令

| 命令 | 作用 |
|:--|:--|
| `put` | 上传文件 / 递归上传目录 |
| `get` | 下载对象到本地 |
| `ls` | 列出桶内对象（前缀过滤，最多 100） |
| `sign` | 生成带过期时间的分享链接 |

```bash
python3 scripts/obs.py put ./output obs://my-bucket/reports/ --recursive
python3 scripts/obs.py ls obs://my-bucket/reports/
python3 scripts/obs.py get obs://my-bucket/builds/dist.zip ./dist.zip
python3 scripts/obs.py sign obs://my-bucket/builds/dist.zip --expires 3600
```

## 凭证三档

```bash
# 1) 长期 AK/SK（最方便，最不推荐）
export OBS_AK=... OBS_SK=... OBS_ENDPOINT=https://obs.cn-north-4.myhuaweicloud.com

# 2) STS 临时凭证（推荐，900 秒自动过期）
export OBS_AK=$STS_AK OBS_SK=$STS_SK OBS_SECURITY_TOKEN=$STS_TOKEN

# 3) 命令行参数（仅调试）
python3 scripts/obs.py ls obs://b/ --ak ... --sk ...
```

**代码里不出现密钥、日志里不回显密钥**，凭证缺失时输出的是可执行的修复提示：

```json
{"ok": false, "action": "ls", "error": "缺少凭证", "hint": "设置 OBS_AK/OBS_SK，STS 场景再加 OBS_SECURITY_TOKEN"}
```

## 写"调用云服务的技能"的六条经验（本题要考的点）

1. **凭证从环境读**，绝不硬编码；报错信息也不回显
2. **输出结构化 JSON**，不要只 print 人类可读文本——Agent 要据此分支
3. **失败带 hint**：把"403 多半是桶策略/凭证无权限，STS 需带 token"写进错误里，少一轮排查
4. **网络抖动重试**：指数退避 3 次（0.4s / 0.8s / 1.6s）
5. **大文件不进内存**：常量 `CHUNK = 8MB` 预留分块上传位
6. **幂等**：同名对象重复上传直接覆盖，不报错

## 签名说明

OBS 用 **V2 签名**（与 ECS/EVS 的 V4 不同）：

```
StringToSign = HTTP-VERB + "\n" + Content-MD5 + "\n" + Content-Type + "\n"
             + Date + "\n" + ["x-obs-security-token:" + token + "\n"] + CanonicalizedResource
Authorization = "OBS " + AK + ":" + Base64(HMAC-SHA1(SK, StringToSign))
```

`scripts/obs.py` 里 `sign()` 就是这个实现，`put` 会额外带上 `Content-MD5` 做完整性校验。

## 目录

```
.
├── SKILL.md          # 技能定义（触发词、用法、边界）
├── scripts/obs.py    # 实现（签名/上传/下载/列对象/签名URL）
└── README.md
```
