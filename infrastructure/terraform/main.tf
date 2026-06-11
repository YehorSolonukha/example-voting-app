terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-voting-app-thesis"
  location = "polandcentral"
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-voting-cluster"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "votingapp-k8s"

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2s_v3"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = "Thesis-Testing"
  }
}

output "kubernetes_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}