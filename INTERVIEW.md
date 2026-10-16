# URL shortener DevOps lab: reviewer guide

A Flask application with tests, GitHub Actions, Terraform, Ansible, a Helm chart, Argo CD material, and monitoring configuration.

## Start the review

Trace application tests to image delivery and GitOps reconciliation. Separate running features from monitoring and hardening plans.

| Source | Review focus |\n| --- | --- |\n| [.github/workflows/ci.yml](.github/workflows/ci.yml) | Triggers, credentials, failure handling, and deploy conditions |\n| [infra/.gitignore](infra/.gitignore) | Inputs, state, permissions, cost, and resource lifecycle |\n| [infra/ansible/ansible.cfg](infra/ansible/ansible.cfg) | Inputs, state, permissions, cost, and resource lifecycle |\n| [infra/ansible/site.yml](infra/ansible/site.yml) | Inputs, state, permissions, cost, and resource lifecycle |\n| [infra/terraform/.terraform.lock.hcl](infra/terraform/.terraform.lock.hcl) | Inputs, state, permissions, cost, and resource lifecycle |\n| [infra/terraform/main.tf](infra/terraform/main.tf) | Inputs, state, permissions, cost, and resource lifecycle |

## A useful interview walkthrough

1. State the problem and the specific part you implemented or changed.
2. Open the source above and follow one request, release, or failure from start to finish.
3. Show a reproducible result, including an actual failure and the observation that confirms recovery.
4. Explain one tradeoff and one limitation. Distinguish a local test from a live deployment.

## Evidence and limits

This guide is based on the default-branch source inspected on 16 October 2026. It is a source review, not a fresh deployment or a certification of every feature. Existing CI runs and tests should be checked at the commit being demonstrated. Do not present screenshots, inherited code, planned features, or old README statements as proof of a current deployment.
