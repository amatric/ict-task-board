terraform {
  required_version = ">= 1.5"
  required_providers {
    huaweicloud = { source = "huaweicloud/huaweicloud", version = "~> 1.60" }
  }
}

variable "region" { default = "cn-north-4" }
variable "vpc_cidr" { default = "192.168.0.0/16" }
variable "subnet_cidr" { default = "192.168.1.0/24" }
variable "instance_count" { default = 2 }
variable "key_name" { default = "" }

provider "huaweicloud" { region = var.region }

# 1) VPC
resource "huaweicloud_vpc" "main" {
  name = "ict-vpc"
  cidr = var.vpc_cidr
}

# 2) 子网
resource "huaweicloud_vpc_subnet" "app" {
  name       = "ict-subnet-app"
  vpc_id     = huaweicloud_vpc.main.id
  cidr       = var.subnet_cidr
  gateway_ip = cidrhost(var.subnet_cidr, 1)
}

# 3) 安全组：只放行 SSH 与 HTTP，出方向全开
resource "huaweicloud_networking_secgroup" "app" {
  name        = "ict-sg-app"
  description = "ICT lab: ssh + http only"
}

resource "huaweicloud_networking_secgroup_rule" "ssh" {
  security_group_id = huaweicloud_networking_secgroup.app.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
}

resource "huaweicloud_networking_secgroup_rule" "http" {
  security_group_id = huaweicloud_networking_secgroup.app.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
}

# 4) 计算实例
data "huaweicloud_availability_zones" "az" {}

data "huaweicloud_compute_flavors" "app" {
  availability_zone = data.huaweicloud_availability_zones.az.names[0]
  performance_type  = "normal"
  cpu_core_count    = 2
  memory_size       = 4
}

data "huaweicloud_images_image" "os" {
  name_regex  = "^Huawei Cloud EulerOS 2\\.0"
  most_recent = true
}

resource "huaweicloud_compute_instance" "app" {
  count             = var.instance_count
  name              = "ict-app-${format("%02d", count.index + 1)}"
  image_id          = data.huaweicloud_images_image.os.id
  flavor_id         = data.huaweicloud_compute_flavors.app.ids[0]
  security_groups   = [huaweicloud_networking_secgroup.app.name]
  availability_zone = data.huaweicloud_availability_zones.az.names[0]
  key_pair          = var.key_name != "" ? var.key_name : null

  network {
    uuid = huaweicloud_vpc_subnet.app.id
  }

  tags = { project = "ict-competition", problem = "18" }
}
