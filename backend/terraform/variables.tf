variable "gcp_project_id" {
  description = "O ID do seu projeto no GCP."
  type        = string
  # Exemplo: "smartface-123456"
}

variable "gcp_region" {
  description = "A região do GCP para os recursos principais."
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "A zona do GCP para recursos zonais (como a instância Cloud SQL)."
  type        = string
  default     = "us-central1-a" # Escolha uma zona dentro da sua gcp_region
}

variable "db_instance_name" {
  description = "Nome para a instância do Cloud SQL."
  type        = string
  default     = "smartface-postgres-db"
}

variable "db_name" {
  description = "Nome para o banco de dados dentro da instância Cloud SQL."
  type        = string
  default     = "reconhecimento_facial" # Conforme usado nos seus scripts Python
}

variable "db_user" {
  description = "Usuário padrão para o banco de dados Cloud SQL."
  type        = string
  default     = "meu_usuario" # Conforme usado nos seus scripts Python
}

variable "db_password" {
  description = "Senha para o usuário padrão do banco de dados Cloud SQL."
  type        = string
  sensitive   = true
  # Você fornecerá este valor no arquivo terraform.tfvars
}

variable "storage_bucket_name" {
  description = "Nome para o bucket do Cloud Storage (deve ser globalmente único)."
  type        = string
  # Exemplo: "smartface-images-bucket-seuidentificadorunico"
  # Você fornecerá este valor no arquivo terraform.tfvars
}

variable "cloud_run_service_name" {
  description = "Nome para o serviço do Cloud Run."
  type        = string
  default     = "smartface-backend"
}

variable "cloud_run_image" {
  description = "A imagem Docker a ser usada para o serviço Cloud Run."
  type        = string
  default     = "gcr.io/cloudrun/hello" # Imagem de exemplo inicial
                                        # Você precisará substituir pela imagem do seu app
                                        # Ex: "gcr.io/SEU_PROJECT_ID/smartface-backend:latest"
}