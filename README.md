# 基于 IaC 在华为云上搭建 ECS 服务基础网络环境

华为 ICT 大赛云赛道 **赛题18** 参评作品。

用 Terraform 描述 VPC + 子网 + 安全组 + ECS 的完整网络环境，一条命令拉起、一条命令销毁。

## 结构

```
main.tf                  VPC / 子网 / 安全组 / ECS
outputs.tf               vpc_id / subnet_id / sg_id / instance_ids / ips
terraform.tfvars.example 变量示例
基于IaC在华为云上搭建ECS服务基础网络环境.md   实践文档
```

## 快速开始

```bash
export HW_ACCESS_KEY=... HW_SECRET_KEY=...
terraform init && terraform plan && terraform apply
terraform output
terraform destroy
```

## 三个 IaC 才有的好处

1. `cidrhost()` 自动推子网网关，不用手算
2. `data "huaweicloud_compute_flavors"` 按 2C4G 查规格，换区域不挂
3. `data "huaweicloud_images_image"` 正则匹配最新 HCE OS

详见[实践文档](基于IaC在华为云上搭建ECS服务基础网络环境.md)。
