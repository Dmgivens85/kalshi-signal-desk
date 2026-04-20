terraform {
  required_version = ">= 1.6.0"
}

# Production should default to EXECUTION_MODE=disabled until operators complete
# a manual live-readiness checklist. Wire this environment to dedicated
# networking, ECS, RDS, Redis, observability, and secrets modules.
