variable "region" {
  type    = string
  default = "us-east-1"
}

# Graviton/ARM (t4g) matches the arm64 images we build from source and is the
# cheapest way to get enough RAM. t4g.xlarge = 4 vCPU / 16 GB (comfortable).
# Cheaper: t4g.large (8 GB) + the onyx-lite compose. See README.
variable "instance_type" {
  type    = string
  default = "t4g.xlarge"
}

variable "use_spot" {
  type        = bool
  default     = false
  description = "Run as a Spot instance (~60-70% cheaper, can be interrupted)."
}

variable "spot_max_price" {
  type        = string
  default     = ""
  description = "Optional max Spot price (USD/hr). Empty = on-demand price cap."
}

variable "root_volume_gb" {
  type    = number
  default = 100
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key contents for the 'ubuntu' user."
}

variable "allowed_ssh_cidr" {
  type        = string
  default     = "0.0.0.0/0"
  description = "Lock SSH (22) to your IP, e.g. 1.2.3.4/32. 80/443 stay open to the world."
}

# ---- App deployment (same knobs as the Oracle module) ----
variable "domain" {
  type        = string
  description = "Public domain, e.g. ai.myndlabs.tech (A record points at the Elastic IP)."
}
variable "letsencrypt_email" {
  type = string
}
variable "repo_url" {
  type    = string
  default = "https://github.com/yethikrishna/mynd-ai.myndlabs.tech.git"
}
variable "repo_branch" {
  type    = string
  default = "claude/mynd-core-architecture-j7jgyt"
}
variable "github_token" {
  type      = string
  default   = ""
  sensitive = true
}
variable "mynd_product" {
  type        = string
  default     = ""
  description = "Empty = shared multi-product. A slug (e.g. eng) = standalone single-product."
}
