output "web_public_ip" { value = huaweicloud_vpc_eip.web.address }
output "web_url" { value = "http://${huaweicloud_vpc_eip.web.address}:${var.app_port}" }
output "security_group_id" { value = huaweicloud_networking_secgroup.web.id }
output "archive_bucket" { value = huaweicloud_obs_bucket.archive.bucket }
