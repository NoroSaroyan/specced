# specced — GitHub repo as code

Terraform that manages the `specced` GitHub repository and its settings — branch
protection, merge policy, topics, Actions — with the
[`integrations/github`](https://registry.terraform.io/providers/integrations/github/latest)
provider.

## Prerequisites

- Terraform >= 1.5 (or OpenTofu >= 1.6).
- A GitHub token with `repo` scope (add `delete_repo` only if you remove the
  `prevent_destroy` lifecycle). Export it:

  ```bash
  export GITHUB_TOKEN=ghp_xxxxx
  ```

## Usage

```bash
cd infra/terraform/github
cp terraform.tfvars.example terraform.tfvars   # edit if needed
terraform init
terraform plan
terraform apply
```

## First-push flow

The repository is created **empty** (`auto_init = false`); push your existing local
history into it:

```bash
git remote add origin git@github.com:NoroSaroyan/specced.git
git push -u origin main
```

Branch protection targets `main`, which must exist on the remote. If `terraform apply`
reports the branch isn't found, push first and re-run `terraform apply`.

## What it manages

| Resource | What |
|---|---|
| `github_repository.specced` | description, topics, homepage, visibility, squash-only merges, auto-delete merged branches, vulnerability alerts; `prevent_destroy` guards against accidental deletion |
| `github_actions_repository_permissions.specced` | Actions enabled, all actions allowed |
| `github_branch_protection.main` | required CI checks (strict), linear history, conversation resolution, no force-push/deletion; PR reviews opt-in via `required_approving_reviews` |

## Knobs

- `required_status_checks` — must match the CI check contexts. The workflow
  `.github/workflows/ci.yml` produces `test (3.10)`…`test (3.13)` and `smoke`.
- `required_approving_reviews` — `0` (default, solo) or `1+` (team).
- `enforce_admins` — `false` (default) or `true` (team).

## Importing an existing repo

If you create the repo by hand first, import it before `apply`:

```bash
terraform import github_repository.specced specced
```

## State

State holds no secrets but should be shared + locked for team use — configure a remote
`backend` in `versions.tf` (an example is included, commented). The provider lock file
`.terraform.lock.hcl` is committed; `*.tfvars` and `*.tfstate` are git-ignored.
