# ---- OCI auth (from your Oracle Cloud API key) ----
variable "tenancy_ocid" { type = string }
variable "user_ocid" { type = string }
variable "fingerprint" { type = string }
variable "private_key_path" {
  type        = string
  description = "Path to the OCI API private key (.pem)."
}
variable "region" {
  type        = string
  description = "OCI region, e.g. eu-frankfurt-1. Pick one with Always-Free A1 capacity."
}
variable "compartment_ocid" {
  type        = string
  description = "Compartment to create resources in (root compartment = tenancy_ocid is fine to start)."
}

# ---- Instance shape (Always Free Ampere A1) ----
# The free tier allows up to 4 OCPUs / 24 GB across A1 instances. Onyx's full
# stack (api, background, web, 2 model servers, opensearch, postgres, redis,
# minio, nginx) wants ~10-14 GB, so use the whole free allotment.
variable "instance_ocpus" {
  type    = number
  default = 4
}
variable "instance_memory_gb" {
  type    = number
  default = 24
}
variable "boot_volume_gb" {
  type    = number
  default = 100 # Always Free includes up to 200 GB block volume total
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key for the 'ubuntu' user (contents, not a path)."
}

# ---- App deployment ----
variable "domain" {
  type        = string
  description = "Public domain, e.g. ai.myndlabs.tech (A record points here after apply)."
}
variable "letsencrypt_email" {
  type        = string
  description = "Email for Let's Encrypt expiry notices."
}
variable "repo_url" {
  type        = string
  description = "HTTPS git URL of this repo."
  default     = "https://github.com/yethikrishna/mynd-ai.myndlabs.tech.git"
}
variable "repo_branch" {
  type    = string
  default = "claude/mynd-core-architecture-j7jgyt"
}
variable "github_token" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Optional GitHub PAT to clone a private repo. Leave empty if the repo is public."
}
variable "mynd_product" {
  type        = string
  default     = ""
  description = "Leave empty for shared multi-product mode (ai.myndlabs.tech/<slug>). Set to one slug (e.g. eng) for a standalone single-product deployment."
}
