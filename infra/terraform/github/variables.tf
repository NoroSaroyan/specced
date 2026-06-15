variable "github_owner" {
  description = "GitHub user or org that owns the repository."
  type        = string
  default     = "NoroSaroyan"
}

variable "repo_name" {
  description = "Repository name."
  type        = string
  default     = "specced"
}

variable "description" {
  description = "Repository description."
  type        = string
  default     = "Interview-driven bootstrap for a reusable agentic coding setup: proof-loop engine + project rules + skills, installed into any repo."
}

variable "homepage_url" {
  description = "Repository homepage URL."
  type        = string
  default     = "https://github.com/NoroSaroyan/specced"
}

variable "visibility" {
  description = "Repository visibility: public or private."
  type        = string
  default     = "public"

  validation {
    condition     = contains(["public", "private"], var.visibility)
    error_message = "visibility must be \"public\" or \"private\"."
  }
}

variable "topics" {
  description = "Repository topics."
  type        = list(string)
  default = [
    "claude-code",
    "agentic",
    "coding-agent",
    "scaffold",
    "proof-loop",
    "spec-driven",
    "codex",
    "developer-tools",
  ]
}

variable "default_branch" {
  description = "Default branch to protect."
  type        = string
  default     = "main"
}

variable "required_status_checks" {
  description = "Status-check contexts that must pass before merging to the default branch (match the CI job names in .github/workflows/ci.yml)."
  type        = list(string)
  default = [
    "test (3.10)",
    "test (3.11)",
    "test (3.12)",
    "test (3.13)",
    "smoke",
  ]
}

variable "required_approving_reviews" {
  description = "Approving reviews required to merge. 0 disables the review requirement (handy for a solo repo); set to 1+ for a team."
  type        = number
  default     = 0
}

variable "enforce_admins" {
  description = "Apply branch protection to admins/owners too."
  type        = bool
  default     = false
}
