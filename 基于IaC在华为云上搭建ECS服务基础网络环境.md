# 基于 IaC 在华为云上搭建 ECS 服务基础网络环境

> 华为 ICT 大赛云赛道 赛题18 实践文档
> 工具：Terraform + `huaweicloud` provider

## 一、目标

用代码（而不是控制台点击）描述一套最小可用的 ECS 网络环境：

```
VPC 192.168.0.0/16
└── 子网 192.168.1.0/24（网关 192.168.1.1）
    └── ECS ×2（2C4G，HCE OS）
        安全组：仅入方向 22 / 80
```

## 二、资源清单与依赖顺序

| 顺序 | 资源 | 说明 |
|--:|:--|:--|
| 1 | `huaweicloud_vpc` | 划出 192.168.0.0/16 |
| 2 | `huaweicloud_vpc_subnet` | `gateway_ip = cidrhost(var.subnet_cidr, 1)` 自动算出网关 |
| 3 | `huaweicloud_networking_secgroup` | 安全组容器 |
| 4 | `secgroup_rule` ×2 | 只放 22 与 80，出方向默认全通 |
| 5 | `compute_instance` ×N | 依赖上面全部 |

Terraform 会按引用关系自动推导顺序，不需要手写 `depends_on`。

## 三、三个"用代码写"才有的好处

1. **网关不用手算**：`cidrhost(var.subnet_cidr, 1)` 从 CIDR 直接算出 192.168.1.1
2. **规格不用猜**：用 `data "huaweicloud_compute_flavors"` 按 2C4G 查出可用规格 ID，换区域不会挂
3. **镜像不用记**：`data "huaweicloud_images_image"` 用正则匹配最新 HCE OS，镜像升级自动跟上

这三处正是控制台点击最费时的地方。

## 四、执行

```bash
export HW_ACCESS_KEY=... HW_SECRET_KEY=... HW_REGION_NAME=cn-north-4
cp terraform.tfvars.example terraform.tfvars   # 按需改
terraform init
terraform plan  -out plan.out
terraform apply plan.out
terraform output
```

销毁：

```bash
terraform destroy
```

## 五、验收

| 检查项 | 期望 |
|:--|:--|
| `terraform output instance_ids` | 2 个 ID |
| VPC 网段 | 192.168.0.0/16 |
| 子网网关 | 192.168.1.1 |
| 安全组入方向 | 只有 22、80 |

## 六、设计取舍

- **不建 EIP**：内部服务不需要公网，需要时再单独加 `huaweicloud_vpc_eip` 与 `compute_eip_associate`
- **密钥对可选**：`key_name` 默认空，纯网络环境验证不需要 SSH
- **实例数与规格变量化**：`instance_count` 改一个数就能扩
- **tag 打标**：便于在控制台按项目筛选与计费归集
