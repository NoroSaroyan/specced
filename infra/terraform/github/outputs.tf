output "repository_full_name" {
  description = "owner/name of the managed repository."
  value       = github_repository.specced.full_name
}

output "repository_html_url" {
  description = "Web URL of the repository."
  value       = github_repository.specced.html_url
}

output "ssh_clone_url" {
  description = "SSH clone URL."
  value       = github_repository.specced.ssh_clone_url
}

output "http_clone_url" {
  description = "HTTPS clone URL."
  value       = github_repository.specced.http_clone_url
}
