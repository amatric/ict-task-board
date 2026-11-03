# 基于 IaC 的静态网站自动化部署与访问控制

华为 ICT 大赛云赛道 **赛题19** 参评作品。

Terraform 一次 apply：建私有 OBS 桶 → 开静态网站托管 → 递归上传 `site/` → 下发"只读不可列举"的桶策略。

## 一键部署

```bash
export HW_ACCESS_KEY=... HW_SECRET_KEY=...
terraform init
terraform apply -var="bucket_name=my-ict-site-2026"
terraform output website_url
```

## 访问控制要点

- 桶 ACL `private`，不用粗粒度的"公有读"
- 只 Allow `GetObject`，显式 **Deny `ListBucket`**（Deny 优先级更高，做兜底）
- 不开放 `PutObject`，匿名不可写

详见[实践文档](基于IaC的静态网站自动化部署与访问控制.md)。

## 文件

```
main.tf     桶 / 网站托管 / 桶策略 / 对象上传 / 可选CDN
outputs.tf  website_url 等
site/       待部署的静态文件（index.html、404.html）
```
