variable "POSTGRES_PASSWORD" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "MINIO_ROOT_USER" {
  description = "MinIO root user"
  type        = string
  default     = "neura-minio"
}

variable "MINIO_ROOT_PASSWORD" {
  description = "MinIO root password"
  type        = string
  sensitive   = true
}

variable "S3_BUCKET" {
  description = "S3 bucket name"
  type        = string
  default     = "neuaraai-media"
}
