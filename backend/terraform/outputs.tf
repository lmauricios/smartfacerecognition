output "cloud_sql_instance_name" {
  description = "O nome da instância do Cloud SQL."
  value       = google_sql_database_instance.postgres_db.name
}

output "cloud_sql_instance_connection_name" {
  description = "O nome de conexão da instância do Cloud SQL (para usar com o Cloud SQL Proxy)."
  value       = google_sql_database_instance.postgres_db.connection_name
}

output "cloud_sql_instance_public_ip_address" {
  description = "O endereço IP público da instância do Cloud SQL."
  value       = google_sql_database_instance.postgres_db.public_ip_address
  sensitive   = true # O IP pode ser considerado informação sensível
}

output "cloud_sql_database_name" {
  description = "O nome do banco de dados criado na instância."
  value       = google_sql_database.default_db.name
}

output "cloud_storage_bucket_url" {
  description = "A URL gs:// do bucket do Cloud Storage."
  value       = google_storage_bucket.images_bucket.url
}

output "cloud_run_service_url" {
  description = "A URL do serviço Cloud Run."
  value       = google_cloud_run_v2_service.backend_service.uri
}