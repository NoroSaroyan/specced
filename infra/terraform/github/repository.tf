resource "github_repository" "specced" {
  name         = var.repo_name
  description  = var.description
  homepage_url = var.homepage_url
  visibility   = var.visibility
  topics       = var.topics

  has_issues      = true
  has_discussions = true
  has_projects    = false
  has_wiki        = false

  # Pull-request hygiene: squash-only with tidy titles; auto-delete merged branches.
  allow_squash_merge     = true
  allow_merge_commit     = false
  allow_rebase_merge     = false
  allow_auto_merge       = true
  delete_branch_on_merge = true

  squash_merge_commit_title   = "PR_TITLE"
  squash_merge_commit_message = "PR_BODY"

  # The repo is populated by pushing existing local history — do not auto-init,
  # or GitHub creates a conflicting initial commit.
  auto_init = false

  lifecycle {
    # Guard against accidental deletion of the repository via Terraform.
    prevent_destroy = true
  }
}

resource "github_actions_repository_permissions" "specced" {
  repository      = github_repository.specced.name
  enabled         = true
  allowed_actions = "all"
}

resource "github_repository_vulnerability_alerts" "specced" {
  repository = github_repository.specced.name
  enabled    = true
}
