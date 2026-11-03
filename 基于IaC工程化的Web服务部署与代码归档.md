# 基于 IaC 工程化的 Web 服务部署与代码归档

> 华为 ICT 大赛云赛道 赛题20 实践文档
> 工具：Terraform + ECS user_data + OBS 归档桶

## 一、目标

把"部署一个 Web 服务"和"代码/产物归档"都写进同一份 IaC：

```
安全组（22 + 8080）
ECS（HCE OS 2C4G）
  └── user_data：装 nginx → 启服务 → 可选 git clone 代码
EIP（5Mbps 按流量）
OBS 归档桶（私有）
```

## 二、工程化体现在哪

| 做法 | 说明 |
|:--|:--|
| **`user_data` 完成初始化** | 实例一起来就是可用状态，不依赖人工 SSH |
| **端口变量化** | `app_port` 改一个数，安全组与访问 URL 同步变 |
| **代码仓库变量化** | `repo_url` 为空则只起 nginx；给了就 `git clone` 到 `/opt/app` |
| **归档桶独立** | 代码/构建产物落 OBS，ECS 销毁也不丢 |
| **输出即可访问地址** | `web_url` 直接给出 `http://<EIP>:<port>` |

## 三、`user_data` 的关键细节

```hcl
user_data = <<-EOT
  #!/bin/bash
  set -e
  dnf install -y nginx git || yum install -y nginx git
  systemctl enable --now nginx
  ${var.repo_url != "" ? "git clone ${var.repo_url} /opt/app || true" : "# ..."}
EOT
```

- `set -e`：任何一步失败就中止，避免"看起来起来了其实没起"
- `dnf || yum`：HCE OS 用 dnf，老镜像用 yum，双写兼容
- `systemctl enable --now`：**enable 才能开机自启**，只 start 重启后就没了
- `git clone ... || true`：拉代码失败不影响服务本身起来

## 四、执行

```bash
export HW_ACCESS_KEY=... HW_SECRET_KEY=...
terraform init
terraform apply -var="key_name=my-keypair" -var="app_port=8080"
terraform output web_url
```

浏览器打开 `web_url` 应看到 nginx 默认页（内容为 `deployed by terraform`）。

## 五、验收清单

| 检查 | 期望 |
|:--|:--|
| `terraform output web_url` | 可访问 HTTP 200 |
| 安全组入方向 | 仅 22 与 `app_port` |
| ECS `user_data` 执行 | nginx 已 enable 且 active |
| `terraform output archive_bucket` | 桶存在且为私有 |
| `terraform destroy` | 资源全部回收，无残留 |

## 六、设计取舍

- **复用 default VPC/子网**：本实验聚焦"部署与归档"，网络部分赛题18 已单独做；需要隔离时把 18 的 VPC 引用过来即可
- **不引入 CI/CD**：流水线属于 CodeArts 侧，IaC 只负责"环境+初始化"，职责分明
- **带宽按流量计费**：实验场景流量小，按流量比按带宽便宜
- **归档桶名写死**：OBS 桶名全局唯一，实际使用应改为变量并加随机后缀
