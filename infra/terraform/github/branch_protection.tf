# Protects the default branch. NOTE: the branch must exist on the remote, so apply
# this after the first `git push` (or apply, push, then re-apply — the required
# checks attach as CI reports them).
resource "github_branch_protection" "main" {
  repository_id = github_repository.specced.node_id
  pattern       = var.default_branch

  enforce_admins                  = var.enforce_admins
  required_linear_history         = true
  allows_force_pushes             = false
  allows_deletions                = false
  require_conversation_resolution = true

  required_status_checks {
    strict   = true
    contexts = var.required_status_checks
  }

  # Review requirement is opt-in (0 = off, for solo repos). Set
  # required_approving_reviews >= 1 to enforce PR review.
  dynamic "required_pull_request_reviews" {
    for_each = var.required_approving_reviews > 0 ? [1] : []
    content {
      required_approving_review_count = var.required_approving_reviews
      dismiss_stale_reviews           = true
      require_code_owner_reviews      = false
    }
  }
}
