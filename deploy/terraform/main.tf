terraform {
  required_version = ">= 1.6"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# Network
resource "docker_network" "neuraai" {
  name = "neuraai_default"
}

# Volumes
resource "docker_volume" "postgres_data" {
  name = "neuraai_postgres_data"
}

resource "docker_volume" "redis_data" {
  name = "neuraai_redis_data"
}

resource "docker_volume" "minio_data" {
  name = "neuraai_minio_data"
}

resource "docker_volume" "certbot_www" {
  name = "neuraai_certbot_www"
}

resource "docker_volume" "letsencrypt_data" {
  name = "neuraai_letsencrypt_data"
}

# Postgres
resource "docker_container" "postgres" {
  name  = "neura-postgres"
  image = "postgres:15-alpine"
  network_mode = "container:neura-postgres"

  env = [
    "POSTGRES_DB=neuaraai",
    "POSTGRES_USER=neura",
    "POSTGRES_PASSWORD=${var.POSTGRES_PASSWORD}",
  ]

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U neura -d neuaraai"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# Redis
resource "docker_container" "redis" {
  name  = "neura-redis"
  image = "redis:7-alpine"
  command = ["redis-server", "--appendonly", "yes"]

  volumes {
    volume_name    = docker_volume.redis_data.name
    container_path = "/data"
  }

  healthcheck {
    test     = ["CMD", "redis-cli", "ping"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# MinIO
resource "docker_container" "minio" {
  name  = "neura-minio"
  image = "minio/minio:latest"
  command = "server /data --console-address \":9001\""

  env = [
    "MINIO_ROOT_USER=${var.MINIO_ROOT_USER}",
    "MINIO_ROOT_PASSWORD=${var.MINIO_ROOT_PASSWORD}",
  ]

  volumes {
    volume_name    = docker_volume.minio_data.name
    container_path = "/data"
  }
}

# MinIO create bucket
resource "docker_container" "create_bucket" {
  name    = "neura-create-bucket"
  image   = "minio/mc:latest"
  command = "sh -c 'until mc alias set local http://minio:9000 ${var.MINIO_ROOT_USER} ${var.MINIO_ROOT_PASSWORD}; do sleep 1; done && mc mb --ignore-existing local/${var.S3_BUCKET} && mc anonymous set public local/${var.S3_BUCKET}'"

  depends_on = [docker_container.minio]
}
