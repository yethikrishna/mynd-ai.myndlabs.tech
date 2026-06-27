output "public_ip" {
  value       = oci_core_instance.mynd.public_ip
  description = "Create an A record for your domain pointing here, then TLS provisions automatically."
}

output "next_steps" {
  value = <<-EOT
    1. At your DNS registrar, add an A record:
         ${var.domain}      A   ${oci_core_instance.mynd.public_ip}
         www.${var.domain}  A   ${oci_core_instance.mynd.public_ip}   (optional)
    2. Wait for DNS to propagate (check: dig +short ${var.domain}).
    3. The VM auto-builds and starts the stack on first boot (10-30 min on ARM).
       SSH in to watch:  ssh ubuntu@${oci_core_instance.mynd.public_ip}
                         tail -f /var/log/mynd-deploy.log
    4. Once DNS resolves, TLS is issued by Let's Encrypt and the app is live at
       https://${var.domain}  (products at /eng, /grc, /sales, /support, /people, /sre).
  EOT
}
