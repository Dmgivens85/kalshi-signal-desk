terraform {
  required_version = ">= 1.6.0"
}

# Staging should run in paper mode only and use demo Kalshi credentials.
# Wire this environment to shared networking, ECS, RDS, Redis, and secrets modules.
