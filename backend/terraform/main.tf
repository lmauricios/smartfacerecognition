# Habilita as APIs necessárias para os serviços
resource "google_project_service" "run_api" {
  project            = var.gcp_project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false # Mantém a API habilitada mesmo se o recurso Terraform for destruído
}

resource "google_project_service" "sqladmin_api" {
  project            = var.gcp_project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "storage_api" {
  project            = var.gcp_project_id
  service            = "storage.googleapis.com" # API para Cloud Storage
  disable_on_destroy = false
}

resource "google_project_service" "iam_api" {
  project            = var.gcp_project_id
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudresourcemanager_api" {
  project            = var.gcp_project_id
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

# --- Cloud SQL para PostgreSQL (Instância db-f1-micro "Always Free") ---
resource "google_sql_database_instance" "postgres_db" {
  project          = var.gcp_project_id
  name             = var.db_instance_name
  region           = var.gcp_region
  database_version = "POSTGRES_17" # Verifique a versão mais recente suportada para db-f1-micro

  settings {
    tier    = "db-f1-micro" # Chave para o nível "Always Free"
    # A zona é herdada do provider ou pode ser especificada aqui:
    # availability_type = "ZONAL"
    # zone = var.gcp_zone

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "allow-all-for-dev"
        value = "0.0.0.0/0" # ATENÇÃO: Permite acesso de qualquer IP.
                            # Ideal para desenvolvimento inicial.
                            # RESTRINJA em produção para os IPs do seu Cloud Run ou outros necessários!
      }
    }
    backup_configuration {
      enabled            = true
      # Para db-f1-micro, point_in_time_recovery_enabled deve ser false
      # ou binary_log_enabled deve ser true.
      # Manter point_in_time_recovery_enabled = false para evitar custos com binary logs.
      point_in_time_recovery_enabled = false
      binary_log_enabled             = false # Garante que não haja custos de binary log
    }
    # db-f1-micro não suporta alta disponibilidade (REGIONAL)
    availability_type = "ZONAL"
  }

  # Facilita a exclusão durante testes. Mude para true em produção.
  deletion_protection = false

  # Garante que a API SQL Admin esteja habilitada antes de criar a instância
  depends_on = [google_project_service.sqladmin_api]
}

resource "google_sql_database" "default_db" {
  project  = var.gcp_project_id
  instance = google_sql_database_instance.postgres_db.name
  name     = var.db_name
}

resource "google_sql_user" "default_user" {
  project  = var.gcp_project_id
  instance = google_sql_database_instance.postgres_db.name
  name     = var.db_user
  password = var.db_password
}

# --- Cloud Storage Bucket ---
resource "google_storage_bucket" "images_bucket" {
  project                     = var.gcp_project_id
  name                        = var.storage_bucket_name # Deve ser globalmente único
  location                    = var.gcp_region          # Ex: US-CENTRAL1
  storage_class               = "STANDARD"              # Standard é elegível para o "Always Free" dentro dos limites
  uniform_bucket_level_access = true

  # Garante que a API Storage esteja habilitada
  depends_on = [google_project_service.storage_api]
}

# --- Cloud Run Service ---
resource "google_cloud_run_v2_service" "backend_service" {
  project  = var.gcp_project_id
  name     = var.cloud_run_service_name
  location = var.gcp_region

  template {
    containers {
      image = var.cloud_run_image
    }
    scaling {
      min_instance_count = 0 # Para escalar para zero e economizar (parte do "Always Free")
      max_instance_count = 1 # Limitar para o "Always Free" inicialmente (pode ser aumentado depois)
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # Garante que a API Run esteja habilitada
  depends_on = [google_project_service.run_api]
}

# Permissão para invocar o Cloud Run publicamente (se sua API for pública)
data "google_iam_policy" "noauth_policy_data" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers", # ATENÇÃO: Permite acesso público irrestrito.
                  # Considere restringir ou usar autenticação em produção.
    ]
  }
}

resource "google_cloud_run_v2_service_iam_policy" "allow_public_invocations" {
  project     = google_cloud_run_v2_service.backend_service.project
  location    = google_cloud_run_v2_service.backend_service.location
  name        = google_cloud_run_v2_service.backend_service.name
  policy_data = data.google_iam_policy.noauth_policy_data.policy_data
}