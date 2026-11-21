provider "elasticstack" {
  elasticsearch {
    endpoints = [var.elasticsearch_url]
    username  = var.elasticsearch_username
    password  = var.elasticsearch_password
  }

  kibana {
    endpoints = [var.kibana_url]
    username  = var.elasticsearch_username
    password  = var.elasticsearch_password
  }
}
