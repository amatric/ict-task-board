output "vpc_id" { value = huaweicloud_vpc.main.id }
output "subnet_id" { value = huaweicloud_vpc_subnet.app.id }
output "security_group_id" { value = huaweicloud_networking_secgroup.app.id }
output "instance_ids" { value = huaweicloud_compute_instance.app[*].id }
output "instance_private_ips" { value = huaweicloud_compute_instance.app[*].access_ip_v4 }
