# Research Report: * Environment variable blueprint
**Date**: 2025-11-24T21:50:15.445561
**Task**: task_0719_researcher - Research: NBA Env Variable Best Practices
**Depth**: quick
**Confidence Score**: 60/100
**Cached**: No

---

## Summary

### Key Findings

- **Configuration-Code Separation is Paramount:** Environment variables are the primary mechanism for separating configuration from application code, adhering to the 12-Factor App methodology. This enhances portability and deployability.
- **Never Commit Secrets to Version Control:** Hardcoding sensitive information (API keys, database credentials) directly into code or configuration files that are committed to Git is a critical security vulnerability. Utilize dedicated secret management solutions.
- **Leverage Cloud-Native Secret Management:** For cloud deployments, always use services like AWS Secrets Manager, Azure Key Vault, or Google Secret Manager. These provide secure storage, access control, rotation, and auditing capabilities.
- **Scope Environment Variables Appropriately:** Define variables at the narrowest possible scope (e.g., per service, per container, per environment) to minimize exposure and facilitate granular access control.
- **Validate Environment Variables at Startup:** Implement checks in your application to ensure all required environment variables are present and correctly formatted during application startup. Fail fast if critical configuration is missing.
- **Prioritize Least Privilege Access:** Grant only the necessary permissions to applications and users to access specific environment variables or secrets. Use IAM roles/policies in cloud environments.
- **Standardize Naming Conventions:** Adopt a consistent naming convention (e.g., `APP_SERVICE_DB_HOST`, `API_KEY`) for environment variables across your projects to improve readability and maintainability.
- **Use .env Files for Local Development Only:** For local development, `.env` files (managed by tools like `python-dotenv` or `direnv`) are convenient but must be explicitly excluded from version control (`.gitignore`).

### Official Documentation

- https://12factor.net/config
- https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
- https://learn.microsoft.com/en-us/azure/key-vault/general/overview
- https://cloud.google.com/secret-manager/docs/overview
- https://docs.docker.com/compose/environment-variables/
- https://kubernetes.io/docs/concepts/configuration/secret/
- https://pypi.org/project/python-dotenv/

### Search Results

### Code Examples

#### Example 1
**Description**: Reading a single environment variable in Python
```
import os

# Access an environment variable
db_host = os.getenv('DATABASE_HOST')

if db_host is None:
    print("Error: DATABASE_HOST environment variable not set.")
    # In a real application, you might raise an exception or exit
else:
    print(f"Database Host: {db_host}")

# Provide a default value if not set
port = os.getenv('APP_PORT', '8080')
print(f"Application Port: {port}")
```

#### Example 2
**Description**: Using python-dotenv for local development with a .env file
```
# .env file content (DO NOT COMMIT THIS!)
# DATABASE_HOST=localhost
# API_KEY=your_dev_api_key_123

# Python code
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

db_host = os.getenv('DATABASE_HOST')
api_key = os.getenv('API_KEY')

print(f"DB Host (from .env or system): {db_host}")
print(f"API Key (from .env or system): {api_key}")

# Note: System environment variables take precedence over .env file variables.
```

#### Example 3
**Description**: Docker Compose example using environment variables
```
version: '3.8'
services:
  web:
    image: my-app:latest
    ports:
      - "80:8000"
    environment:
      - DATABASE_HOST=${DB_HOST}
      - API_KEY=${MY_API_KEY}
    # Alternatively, use an env_file for non-sensitive variables
    # env_file:
    #   - .env
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

#### Example 4
**Description**: Kubernetes Deployment using Secrets as environment variables
```
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secrets
type: Opaque
stringData:
  api-key: "super-secret-api-key"
  db-password: "db-pass-123"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-deployment
spec:
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app-container
        image: my-app:latest
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: my-app-secrets
              key: api-key
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: my-app-secrets
              key: db-password
        # For non-sensitive config maps
        # envFrom:
        #   - configMapRef:
        #       name: my-app-config
```

---

*Research conducted by ResearcherAgent (researcher_main)*
*Sources consulted: llm_research, llm_research*