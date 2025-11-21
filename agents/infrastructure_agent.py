"""
Infrastructure Agent - Handles Infrastructure as Code tasks.
Generates Terraform configurations, Helm charts, and Kubernetes manifests.
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from utils.infrastructure_validator import InfrastructureValidator, get_validator
from utils.template_renderer import get_renderer
from utils.project_layout import ProjectLayout, get_default_layout
import os
import logging
import json


class InfrastructureAgent(BaseAgent):
    """Agent responsible for infrastructure as code tasks."""

    def __init__(self, agent_id: str = "infrastructure_main", workspace_path: str = ".", 
                 project_layout: Optional[ProjectLayout] = None,
                 project_id: Optional[str] = None,
                 tenant_id: Optional[int] = None):
        super().__init__(agent_id, AgentType.INFRASTRUCTURE, project_layout, 
                        project_id=project_id, tenant_id=tenant_id)
        self.workspace_path = workspace_path
        self.infrastructure_files: List[str] = []
        self.validator = get_validator(workspace_path)
        self.template_renderer = get_renderer()

    def process_task(self, task: Task) -> Task:
        """
        Process an infrastructure task by generating IaC configurations.
        
        Args:
            task: The infrastructure task to process
            
        Returns:
            The updated task
        """
        try:
            self.logger.info(f"Processing infrastructure task: {task.title}")
            
            # Extract task information
            description = task.description
            metadata = task.metadata
            infrastructure_type = metadata.get("infrastructure_type", "terraform")
            
            # Generate infrastructure configuration
            files_created = []
            
            if "terraform" in infrastructure_type or "azure" in description.lower():
                files_created.extend(self._create_terraform_config(task))
            
            if "helm" in infrastructure_type or "kubernetes" in description.lower() or "k8s" in description.lower():
                files_created.extend(self._create_helm_config(task))
            
            if "kubernetes" in infrastructure_type or "k8s" in description.lower():
                files_created.extend(self._create_k8s_manifests(task))
            
            # Validate infrastructure if validation tools available
            validation_results = {}
            if any("terraform" in f.lower() or f.endswith(".tf") for f in files_created):
                terraform_result = self.validator.validate_terraform()
                validation_results["terraform"] = terraform_result
                self.logger.info(f"Terraform validation: {terraform_result['status']}")
            
            if any("helm" in f.lower() or "Chart.yaml" in f or "values.yaml" in f for f in files_created):
                helm_result = self.validator.validate_helm()
                validation_results["helm"] = helm_result
                self.logger.info(f"Helm validation: {helm_result['status']}")
            
            # Update task metadata
            task.metadata["infrastructure_files"] = files_created
            task.metadata["validation_results"] = validation_results
            task.result = {
                "files_created": files_created,
                "infrastructure_type": infrastructure_type,
                "validation_results": validation_results,
                "status": "completed"
            }

            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed infrastructure task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing infrastructure task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
            
        return task

    def _create_terraform_config(self, task: Task) -> List[str]:
        """Create Terraform configuration files."""
        files_created = []
        description = task.description.lower()
        metadata = task.metadata
        
        # Determine what Terraform resources are needed
        if "waf" in description or "front door" in description:
            files_created.append(self._create_terraform_waf(task))
        
        if "app insights" in description or "observability" in description:
            files_created.append(self._create_terraform_appinsights(task))
        
        if "private endpoint" in description or "postgres" in description:
            files_created.append(self._create_terraform_private_endpoint(task))
        
        if "key vault" in description or "secrets" in description:
            files_created.append(self._create_terraform_keyvault(task))
        
        # Always create variables.tf and main.tf if Terraform is involved
        if "terraform" in description or files_created:
            files_created.append(self._create_terraform_main(task))
            files_created.append(self._create_terraform_variables(task))
        
        return files_created

    def _create_terraform_waf(self, task: Task) -> str:
        """Create Terraform WAF configuration."""
        file_path = os.path.join(self.project_layout.terraform_azure_dir, "waf.tf")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Try to use template, fall back to inline
        if self.template_renderer.template_exists("infrastructure/terraform_waf.j2"):
            content = self.template_renderer.render("infrastructure/terraform_waf.j2", {})
        else:
            # Fallback inline template
            content = '''# Azure Front Door WAF Configuration
# Generated by InfrastructureAgent

resource "azurerm_frontdoor_firewall_policy" "q2o_waf" {
  name                = "${var.project_name}-waf-policy"
  resource_group_name = azurerm_resource_group.main.name
  location            = "Global"

  enabled = true

  # OWASP ruleset
  custom_rule {
    name     = "OWASP"
    priority = 1
    rule_type = "MatchRule"
    enabled   = true

    match_conditions {
      match_variables {
        variable_name = "RequestMethod"
      }
      operator = "Equal"
      values    = ["POST", "PUT", "DELETE"]
    }

    action = "Block"
  }

  # Rate limiting
  custom_rule {
    name     = "RateLimit"
    priority = 2
    rule_type = "RateLimitRule"
    enabled   = true
    rate_limit_duration_in_minutes = 1
    rate_limit_threshold            = 100

    match_conditions {
      match_variables {
        variable_name = "RemoteAddr"
      }
      operator = "IPMatch"
      values    = ["*"]
    }

    action = "Block"
  }

  # Geo filtering
  custom_rule {
    name     = "GeoFilter"
    priority = 3
    rule_type = "MatchRule"
    enabled   = true

    match_conditions {
      match_variables {
        variable_name = "RemoteAddr"
      }
      operator = "GeoMatch"
      values   = var.allowed_countries
    }

    action = "Allow"
  }

  # Allow Stripe webhook path
  custom_rule {
    name     = "AllowStripeWebhook"
    priority = 10
    rule_type = "MatchRule"
    enabled   = true

    match_conditions {
      match_variables {
        variable_name = "RequestUri"
      }
      operator = "Contains"
      values    = ["/api/billing/webhook"]
    }

    action = "Allow"
  }

  # IP allowlist (if specified)
  dynamic "custom_rule" {
    for_each = length(var.ip_allowlist) > 0 ? [1] : []
    content {
      name     = "IPAllowlist"
      priority = 20
      rule_type = "MatchRule"
      enabled   = true

      match_conditions {
        match_variables {
          variable_name = "RemoteAddr"
        }
        operator = "IPMatch"
        values    = var.ip_allowlist
      }

      action = "Allow"
    }
  }
}

output "waf_policy_id" {
  value = azurerm_frontdoor_firewall_policy.q2o_waf.id
}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_terraform_appinsights(self, task: Task) -> str:
        """Create Terraform Application Insights configuration."""
        file_path = os.path.join(self.project_layout.terraform_azure_dir, "appinsights.tf")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = '''# Azure Application Insights Configuration
# Generated by InfrastructureAgent

resource "azurerm_application_insights" "q2o" {
  name                = "${var.project_name}-appinsights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
}

# Alert for API 5xx spikes
resource "azurerm_monitor_metric_alert" "api_5xx_spike" {
  name                = "${var.project_name}-api-5xx-spike"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights.q2o.id]
  description         = "Alert on API 5xx error spikes"

  criteria {
    metric_namespace = "Microsoft.Insights/components"
    metric_name      = "requests/failed"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Alert for WAF blocks
resource "azurerm_monitor_metric_alert" "waf_blocks" {
  name                = "${var.project_name}-waf-blocks"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_frontdoor_firewall_policy.q2o_waf.id]
  description         = "Alert on WAF blocks"

  criteria {
    metric_namespace = "Microsoft.Network/frontdoorWebApplicationFirewallPolicies"
    metric_name      = "WebApplicationFirewallRequestCount"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 50
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

resource "azurerm_monitor_action_group" "main" {
  name                = "${var.project_name}-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "q2o-alerts"

  email_receiver {
    name          = "admin"
    email_address = var.alert_email
  }
}

output "app_insights_instrumentation_key" {
  value     = azurerm_application_insights.q2o.instrumentation_key
  sensitive = true
}

output "app_insights_connection_string" {
  value     = azurerm_application_insights.q2o.connection_string
  sensitive = true
}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_terraform_private_endpoint(self, task: Task) -> str:
        """Create Terraform Private Endpoint configuration."""
        file_path = os.path.join(self.project_layout.terraform_azure_dir, "private_endpoint.tf")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = '''# Private Endpoint Configuration for Postgres
# Generated by InfrastructureAgent

resource "azurerm_private_endpoint" "postgres" {
  name                = "${var.project_name}-postgres-pe"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private.id

  private_service_connection {
    name                           = "${var.project_name}-postgres-psc"
    private_connection_resource_id = azurerm_postgresql_server.main.id
    subresource_names               = ["postgresqlServer"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "${var.project_name}-postgres-dns"
    private_dns_zone_ids = [azurerm_private_dns_zone.postgres.id]
  }
}

resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.project_name}-postgres-dns-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

output "private_endpoint_id" {
  value = azurerm_private_endpoint.postgres.id
}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_terraform_keyvault(self, task: Task) -> str:
        """Create Terraform Key Vault configuration."""
        file_path = os.path.join(self.project_layout.terraform_azure_dir, "keyvault.tf")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = '''# Azure Key Vault Configuration
# Generated by InfrastructureAgent

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}-kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
    ]

    certificate_permissions = [
      "Get", "List", "Create", "Delete", "Update"
    ]
  }

  enabled_for_deployment          = true
  enabled_for_template_deployment = true
  enabled_for_disk_encryption     = true
}

output "key_vault_id" {
  value = azurerm_key_vault.main.id
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_terraform_main(self, task: Task) -> str:
        """Create Terraform main configuration."""
        file_path = os.path.join(self.project_layout.terraform_azure_dir, "main.tf")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Try to use template, fall back to inline
        if self.template_renderer.template_exists("infrastructure/terraform_main.j2"):
            content = self.template_renderer.render("infrastructure/terraform_main.j2", {})
        else:
            # Fallback inline template
            content = '''# Main Terraform Configuration
# Generated by InfrastructureAgent

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    # Configure backend in terraform.tfvars or environment variables
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# Subnets
resource "azurerm_subnet" "private" {
  name                 = "${var.project_name}-private-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "delegation"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_subnet" "public" {
  name                 = "${var.project_name}-public-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_terraform_variables(self, task: Task) -> str:
        """Create Terraform variables file."""
        file_path = os.path.join(self.project_layout.terraform_azure_dir, "variables.tf")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Try to use template, fall back to inline
        if self.template_renderer.template_exists("infrastructure/terraform_variables.j2"):
            content = self.template_renderer.render("infrastructure/terraform_variables.j2", {})
        else:
            # Fallback inline template
            content = '''# Terraform Variables
# Generated by InfrastructureAgent

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "q2o"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "allowed_countries" {
  description = "List of allowed countries for geo-filtering"
  type        = list(string)
  default     = ["US", "CA", "GB", "JM"]
}

variable "ip_allowlist" {
  description = "List of allowed IP addresses"
  type        = list(string)
  default     = []
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = "admin@quick2odoo.online"
}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_helm_config(self, task: Task) -> List[str]:
        """Create Helm chart configuration."""
        files_created = []
        description = task.description.lower()
        
        # Create values.yaml
        files_created.append(self._create_helm_values(task))
        
        # Create Chart.yaml
        files_created.append(self._create_helm_chart(task))
        
        # Create templates
        files_created.append(self._create_helm_secret_provider(task))
        
        return files_created

    def _create_helm_values(self, task: Task) -> str:
        """Create Helm values.yaml."""
        file_path = os.path.join(self.project_layout.helm_q2o_dir, "values.yaml")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Try to use template, fall back to inline
        if self.template_renderer.template_exists("infrastructure/helm_values.j2"):
            content = self.template_renderer.render("infrastructure/helm_values.j2", {})
        else:
            # Fallback inline template
            content = '''# Helm Values Configuration
# Generated by InfrastructureAgent

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: app.quick2odoo.online
      paths:
        - path: /
          pathType: Prefix
    - host: api.quick2odoo.online
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: q2o-tls
      hosts:
        - app.quick2odoo.online
        - api.quick2odoo.online

api:
  image:
    repository: q2o/api
    tag: latest
  env:
    NEXT_PUBLIC_API_URL: "https://api.quick2odoo.online"
    NEXTAUTH_URL: "https://app.quick2odoo.online"
    DATABASE_URL: ""
    TEMPORAL_ADDRESS: ""
    TEMPORAL_NAMESPACE: "default"
    TEMPORAL_TASK_QUEUE: "q2o-sync"
    Q2O_ALLOWED_ORIGINS: "https://app.quick2odoo.online"
  
worker:
  image:
    repository: q2o/worker
    tag: latest
  env:
    DATABASE_URL: ""
    TEMPORAL_ADDRESS: ""
    TEMPORAL_NAMESPACE: "default"
    TEMPORAL_TASK_QUEUE: "q2o-sync"

secrets:
  # Use Key Vault CSI or Kubernetes secrets
  keyVault:
    enabled: true
    vaultName: ""
    objects:
      - objectName: DATABASE_URL
        objectType: secret
      - objectName: NEXTAUTH_SECRET
        objectType: secret
      - objectName: QBO_CLIENT_ID
        objectType: secret
      - objectName: QBO_CLIENT_SECRET
        objectType: secret
      - objectName: STRIPE_SECRET
        objectType: secret
      - objectName: STRIPE_WEBHOOK_SECRET
        objectType: secret
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_helm_chart(self, task: Task) -> str:
        """Create Helm Chart.yaml."""
        file_path = os.path.join(self.project_layout.helm_q2o_dir, "Chart.yaml")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Try to use template, fall back to inline
        if self.template_renderer.template_exists("infrastructure/helm_chart.j2"):
            content = self.template_renderer.render("infrastructure/helm_chart.j2", {})
        else:
            # Fallback inline template
            content = '''apiVersion: v2
name: q2o
description: Quick2Odoo Online Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"

dependencies:
  - name: ingress-nginx
    version: "4.0.0"
    repository: "https://kubernetes.github.io/ingress-nginx"
    condition: ingress.enabled
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_helm_secret_provider(self, task: Task) -> str:
        """Create Helm SecretProviderClass template."""
        file_path = os.path.join(self.project_layout.helm_templates_dir, "secretproviderclass.yaml")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = '''# Key Vault CSI SecretProviderClass
# Generated by InfrastructureAgent
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: q2o-secrets
  namespace: {{ .Values.namespace | default "default" }}
spec:
  provider: azure
  secretObjects:
  - secretName: q2o-secrets
    type: Opaque
    data:
    - objectName: DATABASE_URL
      key: DATABASE_URL
    - objectName: NEXTAUTH_SECRET
      key: NEXTAUTH_SECRET
    - objectName: QBO_CLIENT_ID
      key: QBO_CLIENT_ID
    - objectName: QBO_CLIENT_SECRET
      key: QBO_CLIENT_SECRET
    - objectName: STRIPE_SECRET
      key: STRIPE_SECRET
    - objectName: STRIPE_WEBHOOK_SECRET
      key: STRIPE_WEBHOOK_SECRET
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: ""
    keyvaultName: {{ .Values.secrets.keyVault.vaultName | quote }}
    objects: |
      array:
      {{- range .Values.secrets.keyVault.objects }}
      - |
        objectName: {{ .objectName }}
        objectType: {{ .objectType }}
      {{- end }}
    tenantId: ""
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.infrastructure_files.append(file_path)
        return file_path

    def _create_k8s_manifests(self, task: Task) -> List[str]:
        """Create Kubernetes manifests."""
        # Kubernetes manifests are typically generated from Helm templates
        # This method can create basic manifests if needed
        return []

