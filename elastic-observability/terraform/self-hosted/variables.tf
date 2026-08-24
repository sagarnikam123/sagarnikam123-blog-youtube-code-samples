variable "elasticsearch_url" {
  description = "URL of the self-hosted Elasticsearch instance"
  type        = string
  default     = "http://localhost:9200"
}

variable "kibana_url" {
  description = "URL of the self-hosted Kibana instance"
  type        = string
  default     = "http://localhost:5601"
}

variable "elasticsearch_username" {
  description = "Elasticsearch username"
  type        = string
  default     = "elastic"
}

variable "elasticsearch_password" {
  description = "Elasticsearch password"
  type        = string
  sensitive   = true
}
