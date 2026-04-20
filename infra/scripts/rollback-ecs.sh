#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:?AWS_REGION is required}"
ECS_CLUSTER="${ECS_CLUSTER:?ECS_CLUSTER is required}"
ECS_SERVICE="${ECS_SERVICE:?ECS_SERVICE is required}"
PREVIOUS_TASK_DEFINITION_ARN="${PREVIOUS_TASK_DEFINITION_ARN:?PREVIOUS_TASK_DEFINITION_ARN is required}"

aws ecs update-service \
  --region "${AWS_REGION}" \
  --cluster "${ECS_CLUSTER}" \
  --service "${ECS_SERVICE}" \
  --task-definition "${PREVIOUS_TASK_DEFINITION_ARN}" \
  --force-new-deployment

aws ecs wait services-stable \
  --region "${AWS_REGION}" \
  --cluster "${ECS_CLUSTER}" \
  --services "${ECS_SERVICE}"
