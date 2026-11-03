# hwc —— 华为云服务命令行工具

华为 ICT 大赛云赛道 **赛题11（CLI-如何将华为云服务封装成 CLI）** 的参评作品。

把华为云 ECS / EVS / OBS 的常用查询封装成一条 `hwc` 命令，**默认给人看表格，加 `--json` 给程序吃**。

## 设计取向：给人和给机器两副面孔

```bash
$ python3 hwc.py ecs list
NAME        ID          STATUS    FLAVOR        IP
----------  ----------  --------  ------------  ------------
web-01      8f3c...a1   ACTIVE    s6.large.2    192.168.0.10
db-01       1d7e...b2   ACTIVE    c6.xlarge.4   192.168.0.20

$ python3 hwc.py ecs list --json
[
  {"name": "web-01", "id": "8f3c...a1", "status": "ACTIVE", "flavor": "s6.large.2", "ip": "192.168.0.10"}
]
```

同一条命令，**人看表格，脚本看 JSON**，不用维护两套。

## 命令树

```
hwc
├── ecs
│   ├── list [--limit N]
│   └── show <id>
├── evs
│   └── list [--limit N]
├── obs
│   └── ls <obs://bucket/prefix>
└── region                     # 区域 + 凭证 + 数据源状态
```

全局选项 `--json` / `--region` 在**子命令前后都能写**：

```bash
python3 hwc.py --json ecs list
python3 hwc.py ecs list --json
python3 hwc.py ecs list --region cn-east-3
```

## 上线前的凭证切换

```bash
# 未配凭证：走内置样例数据，可直接演示
python3 hwc.py region
# {"region":"cn-north-4","ak_configured":false,"sk_configured":false,"data_source":"builtin-demo",...}

# 配置后：切到真实调用（生产实现需接入官方 SDK，见 hwc/cli.py 的 _real_call）
export HUAWEICLOUD_SDK_AK=... HUAWEICLOUD_SDK_SK=...
```

配了凭证但没接 SDK 时，会明确告诉你怎么办，而不是静默返回空列表：

```json
{"ok": false, "error": "已配置 AK/SK，但本示例未内置官方 SDK。生产环境请 pip install huaweicloudsdkecs 后在此处接入；如需立即体验，请 unset HUAWEICLOUD_SDK_AK 使用内置样例数据。"}
```

## 封装 CLI 的六条经验

1. **人机双输出**：默认表格（可读）+ `--json`（可解析），而不是只 print 文本
2. **错误走 stderr、带 hint**：`{"ok":false,"error":"...","hint":"..."}`，退出码非 0，能被 shell 判断
3. **全局选项放宽位置**：`--json` 前面后面都能写，用 `argparse` 的 `parents=[common]` 实现
4. **命令树分层**：`hwc <服务> <动作>`，和 `kubectl` / `aws` 一致，学习成本低
5. **数据源可切换**：样例数据 + 真实调用两条路，未配凭证也能演示，配了凭证不会被静默吞掉
6. **业务错误不抛栈**：`LookupError` → 友好提示；只有未预期异常才落到兜底

## 自测

```bash
python3 hwc.py ecs list
python3 hwc.py ecs show 8f3c
python3 hwc.py evs list --json
python3 hwc.py region
python3 hwc.py obs ls bad        # 预期失败：参数校验
```

## 目录

```
.
├── hwc.py            # 单文件入口（python3 hwc.py ...）
├── hwc/
│   ├── __init__.py
│   ├── __main__.py   # 支持 python3 -m hwc ...
│   └── cli.py        # 参数解析 + 输出 + 数据层
└── README.md
```
