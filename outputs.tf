output "bucket_domain" { value = huaweicloud_obs_bucket.site.bucket_domain_name }
output "website_url" { value = "http://${huaweicloud_obs_bucket.site.bucket_domain_name}/index.html" }
output "object_keys" { value = sort(keys(huaweicloud_obs_bucket_object.files)) }
