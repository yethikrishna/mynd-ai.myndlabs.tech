# Single EC2 (Graviton/ARM) running the full Onyx + mynd stack, in the default
# VPC, with a stable Elastic IP and Let's Encrypt TLS. Mirrors the Oracle module.

# --- Network: reuse the account's default VPC + a public subnet ---
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# --- Latest Ubuntu 22.04 ARM64 AMI (Canonical, via SSM) ---
data "aws_ssm_parameter" "ubuntu_arm64" {
  name = "/aws/service/canonical/ubuntu/server/22.04/stable/current/arm64/hvm/ebs-gp2/ami-id"
}

# --- SSH key ---
resource "aws_key_pair" "mynd" {
  key_name   = "mynd-core"
  public_key = var.ssh_public_key
}

# --- Security group: SSH (restrictable) + HTTP/HTTPS ---
resource "aws_security_group" "mynd" {
  name        = "mynd-core-sg"
  description = "mynd Core: ssh + http/https"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }
  ingress {
    description = "HTTP (Let's Encrypt + redirect)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

locals {
  user_data = base64encode(templatefile("${path.module}/../free/oracle/cloud-init.yaml.tftpl", {
    domain       = var.domain
    email        = var.letsencrypt_email
    repo_url     = var.repo_url
    repo_branch  = var.repo_branch
    github_token = var.github_token
    mynd_product = var.mynd_product
  }))
}

resource "aws_instance" "mynd" {
  ami                         = data.aws_ssm_parameter.ubuntu_arm64.value
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.mynd.id]
  key_name                    = aws_key_pair.mynd.key_name
  associate_public_ip_address = true
  user_data_base64            = local.user_data

  root_block_device {
    volume_size = var.root_volume_gb
    volume_type = "gp3"
  }

  dynamic "instance_market_options" {
    for_each = var.use_spot ? [1] : []
    content {
      market_type = "spot"
      spot_options {
        max_price                      = var.spot_max_price != "" ? var.spot_max_price : null
        spot_instance_type             = "persistent"
        instance_interruption_behavior = "stop"
      }
    }
  }

  tags = {
    Name = "mynd-core"
    app  = "mynd-core"
  }
}

# Stable public IP so the DNS A record survives stop/start.
resource "aws_eip" "mynd" {
  instance = aws_instance.mynd.id
  domain   = "vpc"
  tags     = { Name = "mynd-core" }
}
