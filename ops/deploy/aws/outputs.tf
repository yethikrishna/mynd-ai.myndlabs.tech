output "public_ip" {
  value       = aws_eip.mynd.public_ip
  description = "Elastic IP — point your domain's A record here."
}

output "next_steps" {
  value = <<-EOT
    1. At your DNS registrar, add an A record:
         ${var.domain}      A   ${aws_eip.mynd.public_ip}
         www.${var.domain}  A   ${aws_eip.mynd.public_ip}   (optional)
    2. First boot builds + starts the stack (10-30 min on ARM). Watch:
         ssh ubuntu@${aws_eip.mynd.public_ip}
         tail -f /var/log/mynd-deploy.log
    3. Once DNS resolves, Let's Encrypt issues TLS and the app is live:
         https://${var.domain}   (products at /eng, /grc, /sales, /support, /people, /sre)
  EOT
}
