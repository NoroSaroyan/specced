terraform {
  required_version = ">= 1.5"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  # For shared/team use, configure a remote backend (state holds no secrets but
  # should be locked + shared). Example:
  #
  # backend "s3" {
  #   bucket = "my-tf-state"
  #   key    = "github/specced.tfstate"
  #   region = "us-east-1"
  # }
}
