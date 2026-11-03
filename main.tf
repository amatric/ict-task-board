terraform {
  required_version = ">= 1.5"
  required_providers {
    huaweicloud = { source = "huaweicloud/huaweicloud", version = "~> 1.60" }
  }
}

variable "region" { default = "cn-north-4" }
variable "bucket_name" { description = "全局唯一桶名" }
variable "site_dir" { default = "./site" }
variable "enable_cdn" { default = false }

provider "huaweicloud" { region = var.region }

# 1) 私有桶 + 静态网站托管
resource "huaweicloud_obs_bucket" "site" {
  bucket        = var.bucket_name
  storage_class = "STANDARD"
  acl           = "private"          # 桶本身私有，靠策略精确授权

  website {
    index_document = "index.html"
    error_document = "404.html"
  }

  tags = { project = "ict-competition", problem = "19" }
}

# 2) 只允许匿名 GET（读），不允许列举、不允许写
resource "huaweicloud_obs_bucket_policy" "public_read" {
  bucket = huaweicloud_obs_bucket.site.bucket
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowPublicReadObjects"
        Effect    = "Allow"
        Principal = { ID = ["*"] }
        Action    = ["GetObject"]
        Resource  = ["obs://${var.bucket_name}/*"]
      },
      {
        Sid       = "DenyPublicList"
        Effect    = "Deny"
        Principal = { ID = ["*"] }
        Action    = ["ListBucket"]
        Resource  = ["obs://${var.bucket_name}"]
      }
    ]
  })
}

# 3) 上传站点文件（自动化部署）
resource "huaweicloud_obs_bucket_object" "files" {
  for_each     = fileset(var.site_dir, "**")
  bucket       = huaweicloud_obs_bucket.site.bucket
  key          = each.value
  source       = "${var.site_dir}/${each.value}"
  content_type = lookup({
    "html" = "text/html; charset=utf-8",
    "css"  = "text/css; charset=utf-8",
    "js"   = "application/javascript; charset=utf-8",
    "json" = "application/json; charset=utf-8",
    "png"  = "image/png",
    "jpg"  = "image/jpeg",
    "svg"  = "image/svg+xml",
  }, element(split(".", each.value), length(split(".", each.value)) - 1), "application/octet-stream")
}

# 4) 可选：CDN 加速（需已备案域名，默认关闭）
resource "huaweicloud_cdn_domain" "acc" {
  count        = var.enable_cdn ? 1 : 0
  name         = "static.example.com"
  type         = "web"
  domain_origin = huaweicloud_obs_bucket.site.bucket_domain_name
}
