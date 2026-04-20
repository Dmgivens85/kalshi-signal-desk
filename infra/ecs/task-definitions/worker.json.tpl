{
  "family": "${family}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "${cpu}",
  "memory": "${memory}",
  "executionRoleArn": "${execution_role_arn}",
  "taskRoleArn": "${task_role_arn}",
  "containerDefinitions": [
    {
      "name": "${container_name}",
      "image": "${image}",
      "essential": true,
      "readonlyRootFilesystem": true,
      "user": "app",
      "environment": ${environment_json},
      "secrets": ${secrets_json},
      "command": ["sh", "-c", "python -m ${service_module}"],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${log_group}",
          "awslogs-region": "${aws_region}",
          "awslogs-stream-prefix": "${container_name}"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import os,sys,urllib.request;port=os.environ.get('SERVICE_HEALTH_PORT','9090');sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/ready', timeout=3).status == 200 else 1)\""],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 20
      }
    }
  ]
}
