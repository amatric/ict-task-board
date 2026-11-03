# 基于 IaC 的静态网站自动化部署与访问控制

> 华为 ICT 大赛云赛道 赛题19 实践文档
> 工具：Terraform + OBS 静态网站托管 + 桶策略

## 一、要解决的两件事

1. **自动化部署**：`terraform apply` 一次，把整个 `site/` 目录同步到 OBS
2. **访问控制**：桶私有，但**只**允许匿名读对象，**禁止**列举桶

这两件事在控制台是"点十几下 + 手动拖文件 + 调策略"，用 IaC 就是一次 apply。

## 二、访问控制设计（核心）

```hcl
Statement = [
  { Sid = "AllowPublicReadObjects"  Effect = "Allow"  Action = ["GetObject"]  Resource = ["obs://bucket/*"] },
  { Sid = "DenyPublicList"          Effect = "Deny"   Action = ["ListBucket"] Resource = ["obs://bucket"]   },
]
```

| 设计点 | 为什么 |
|:--|:--|
| 桶 ACL 保持 `private` | 不用"公有读"这种粗粒度开关，避免顺带放开列举 |
| 只 Allow `GetObject` | 精确到单个对象读 |
| 显式 Deny `ListBucket` | 即使有别的策略误放行，Deny 优先级更高，兜底 |
| 不开放 `PutObject` | 匿名不可写，杜绝被当成图床/投毒 |

## 三、自动化部署怎么做的

```hcl
resource "huaweicloud_obs_bucket_object" "files" {
  for_each = fileset(var.site_dir, "**")
  key      = each.value
  source   = "${var.site_dir}/${each.value}"
  content_type = ...   # 按扩展名映射 MIME
}
```

- `fileset()` 递归列出目录，**新增文件不用改代码**
- `content_type` 按扩展名映射，否则浏览器会把 HTML 当纯文本下载
- `for_each` 保证增删文件时只动差异对象

## 四、执行

```bash
export HW_ACCESS_KEY=... HW_SECRET_KEY=...
terraform init
terraform apply -var="bucket_name=my-ict-site-2026"
terraform output website_url
```

访问 `website_url` 应看到站点首页。

## 五、验收清单

| 检查 | 期望 |
|:--|:--|
| 访问 `/index.html` | 200，返回 HTML |
| 访问不存在的路径 | 返回 `404.html` 内容 |
| 访问 `/` （列举桶） | 403 / 拒绝 |
| 匿名 PUT 一个对象 | 403 |
| `terraform output object_keys` | 与 `site/` 下文件一致 |

## 六、设计取舍

- **CDN 默认关闭**：`enable_cdn=false`，因为 CDN 需要已备案域名，实验中不一定具备；置 true 才创建
- **不建自定义域名解析**：DNS 依赖域名所有权，超出本实验范围
- **MIME 用 lookup 映射**：不引入额外 provider，保持单文件可读
- **错误页走 OBS 的 error_document**：不需要额外配置，OBS 原生支持
