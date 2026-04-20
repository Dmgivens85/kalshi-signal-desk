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
      "name": "api",
      "image": "${image}",
      "essential": true,
      "portMappings": [
        { "containerPort": 8000, "hostPort": 8000, "protocol": "tcp" }
      ],
      "readonlyRootFilesystem": true,
      "user": "app",
      "environment": ${environment_json},
      "secrets": ${secrets_json},
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${log_group}",
          "awslogs-region": "${aws_region}",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import sys,urllib.request;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=3).status == 200 else 1)\""],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 20
      }
    }
  ]
}
