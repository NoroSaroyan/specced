# Auth: export a token with `repo` scope (add `delete_repo` only if you disable
# the prevent_destroy lifecycle below). The provider reads GITHUB_TOKEN.
#
#   export GITHUB_TOKEN=ghp_xxxxx
#
provider "github" {
  owner = var.github_owner
}
