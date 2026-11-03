# 基于 IaC 工程化的 Web 服务部署与代码归档

华为 ICT 大赛云赛道 **赛题20** 参评作品。

Terraform 一次 apply 完成：安全组 → ECS（user_data 自动装 nginx 起服务）→ EIP 绑定 → OBS 归档桶。

## 一键部署

```bash
export HW_ACCESS_KEY=... HW_SECRET_KEY=...
terraform init
terraform apply -var="key_name=my-keypair" -var="app_port=8080"
terraform output web_url
```

## 工程化要点

- `user_data` 完成初始化（`dnf||yum` 兼容 + `systemctl enable --now`）
- `app_port` 变量化：安全组与访问 URL 同步变
- `repo_url` 可选：给了就 `git clone` 到 `/opt/app`
- OBS 私有归档桶：ECS 销毁，代码/产物不丢

详见[实践文档](基于IaC工程化的Web服务部署与代码归档.md)。
