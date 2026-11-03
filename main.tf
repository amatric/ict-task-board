terraform {
  required_version = ">= 1.5"
  required_providers {
    huaweicloud = { source = "huaweicloud/huaweicloud", version = "~> 1.60" }
  }
}

variable "region" { default = "cn-north-4" }
variable "key_name" { default = "" }
variable "app_port" {
  type    = number
  default = 8080
}
variable "repo_url" {
  description = "代码归档仓库地址（CodeArts Repo / GitCode）"
  default     = ""
}

provider "huaweicloud" { region = var.region }

data "huaweicloud_availability_zones" "az" {}
data "huaweicloud_vpc" "default" { name = "vpc-default" }
data "huaweicloud_vpc_subnet" "default" {
  name = "subnet-default"
  vpc_id = data.huaweicloud_vpc.default.id
}

# 1) 安全组：SSH + 应用端口
resource "huaweicloud_networking_secgroup" "web" {
  name = "ict-web-sg"
}

resource "huaweicloud_networking_secgroup_rule" "ssh" {
  security_group_id = huaweicloud_networking_secgroup.web.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
}

resource "huaweicloud_networking_secgroup_rule" "app" {
  security_group_id = huaweicloud_networking_secgroup.web.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.app_port
  port_range_max    = var.app_port
  remote_ip_prefix  = "0.0.0.0/0"
}

# 2) Web 服务器
data "huaweicloud_compute_flavors" "web" {
  availability_zone = data.huaweicloud_availability_zones.az.names[0]
  performance_type  = "normal"
  cpu_core_count    = 2
  memory_size       = 4
}

data "huaweicloud_images_image" "os" {
  name_regex  = "^Huawei Cloud EulerOS 2\\.0"
  most_recent = true
}

resource "huaweicloud_compute_instance" "web" {
  name              = "ict-web-01"
  image_id          = data.huaweicloud_images_image.os.id
  flavor_id         = data.huaweicloud_compute_flavors.web.ids[0]
  security_groups   = [huaweicloud_networking_secgroup.web.name]
  availability_zone = data.huaweicloud_availability_zones.az.names[0]
  key_pair          = var.key_name != "" ? var.key_name : null

  network { uuid = data.huaweicloud_vpc_subnet.default.id }

  user_data = <<-EOT
    #!/bin/bash
    set -e
    dnf install -y nginx git || yum install -y nginx git
    systemctl enable --now nginx
    ${var.repo_url != "" ? "git clone ${var.repo_url} /opt/app || true" : "# repo_url 为空，跳过代码拉取"}
    echo "deployed by terraform" > /usr/share/nginx/html/index.html
  EOT

  tags = { project = "ict-competition", problem = "20" }
}

# 3) 公网 EIP 并绑定
resource "huaweicloud_vpc_eip" "web" {
  publicip { type = "5_bgp" }
  bandwidth {
    name        = "ict-web-bw"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_compute_eip_associate" "web" {
  public_ip   = huaweicloud_vpc_eip.web.address
  instance_id = huaweicloud_compute_instance.web.id
}

# 4) 代码归档桶（用于留存构建产物与快照）
resource "huaweicloud_obs_bucket" "archive" {
  bucket        = "ict-web-code-archive-2026"
  storage_class = "STANDARD"
  acl           = "private"
  tags          = { project = "ict-competition", problem = "20" }
}
