# Definicja dostawcy (Azure)
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

# 1. Tworzenie Grupy Zasobów (Resource Group) - kontenera na nasz klaster
resource "azurerm_resource_group" "rg" {
  name     = "rg-voting-app-thesis"
  location = "polandcentral" # Możesz zmienić na najbliższy region, np. polandcentral
}

# 2. Tworzenie klastra AKS
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-voting-cluster"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "votingapp-k8s"

  # Konfiguracja puli węzłów (Node Pool)
  default_node_pool {
    name       = "default"
    node_count = 2                  # Dokładnie 2 węzły, aby udowodnić rozproszenie systemu
    vm_size    = "Standard_D2s_v3"  # Optymalny rozmiar (2 vCPU, 8GB RAM) pod aplikacje i metryki
  }

  # Przypisanie tożsamości zarządzanej (Managed Identity) dla klastra
  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = "Thesis-Testing"
  }
}

# Wyjście (Output) - Terraform wypisze nam nazwę klastra po zakończeniu pracy
output "kubernetes_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}