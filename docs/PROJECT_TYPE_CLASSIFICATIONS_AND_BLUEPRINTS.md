# Project Type Classifications and Blueprints

**Date**: November 29, 2025  
**Status**: ✅ **DOCUMENTED**

---

## Overview

The Q2O platform uses an LLM-powered classification system to identify project types and build structure blueprints. This document outlines:

1. **All project types the LLM can classify**
2. **Which types have explicit blueprint definitions**
3. **The classification structure returned by the LLM**

---

## Project Types the LLM Can Classify

The Orchestrator's LLM prompt asks it to classify projects into one of these types (and more):

### Primary Types (with explicit blueprints):
1. ✅ **`mobile_app`** - Mobile applications (React Native, Expo, iOS, Android)
2. ✅ **`web_app`** - Web applications (Next.js, React)
3. ✅ **`api_service`** - Backend API services (FastAPI, Python)
4. ✅ **`saas_platform`** - Software-as-a-Service platforms
5. ✅ **`data_pipeline`** - Data processing pipelines
6. ✅ **`microservice`** - Microservice architectures
7. ✅ **`desktop_app`** - Desktop applications
8. ✅ **`cli_tool`** - Command-line interface tools
9. ✅ **`library`** - Code libraries/packages
10. ✅ **`infrastructure`** - Infrastructure-as-Code (Terraform, Kubernetes)
11. ✅ **`blockchain_app`** - Blockchain applications
12. ✅ **`ml_service`** - Machine Learning services

### Future Types (LLM can classify, but no explicit blueprint yet):
13. **`etc.`** - The LLM can classify other types as needed (will use tech stack fallback)

---

## Classification Structure

When the LLM classifies a project, it returns an `objective_classification` object with this structure:

```json
{
  "objective_classification": {
    "type": "mobile_app" | "web_app" | "saas_platform" | "api_service" | etc.,
    "platforms": ["android", "ios"] | ["web"] | ["desktop"] | ["cloud"] | ["serverless"] | ["multi-platform"] | etc.,
    "domain": "finance" | "healthcare" | "ecommerce" | "education" | "productivity" | "supply_chain" | etc.,
    "complexity": "low" | "medium" | "high",
    "key_features": ["authentication", "payments", "real-time", "offline", "collaboration", etc.],
    "tech_stack": ["React Native", "TypeScript"] | ["Python", "FastAPI"] | ["Next.js", "React"] | etc.
  }
}
```

### Classification Fields Explained

#### `type` (Required)
The primary project type classification. Examples:
- `mobile_app` - Mobile applications
- `web_app` - Web applications  
- `api_service` - Backend API services
- `saas_platform` - SaaS platforms
- `data_pipeline` - Data processing
- `microservice` - Microservices
- `desktop_app` - Desktop apps
- `cli_tool` - CLI tools
- `library` - Code libraries
- `infrastructure` - Infrastructure code
- `blockchain_app` - Blockchain apps
- `ml_service` - ML services

#### `platforms` (Array, Optional)
Target platforms for the project:
- `android` - Android mobile
- `ios` - iOS mobile
- `web` - Web browser
- `desktop` - Desktop OS (Windows, macOS, Linux)
- `cloud` - Cloud platforms
- `serverless` - Serverless functions
- `multi-platform` - Multiple platforms

#### `domain` (String, Optional)
Industry/domain classification:
- `finance` - Financial services
- `healthcare` - Healthcare
- `ecommerce` - E-commerce
- `education` - Education
- `productivity` - Productivity tools
- `supply_chain` - Supply chain
- `social` - Social media
- `gaming` - Games
- `enterprise` - Enterprise software
- etc.

#### `complexity` (String, Required)
Project complexity level:
- `low` - Simple projects, few features
- `medium` - Moderate complexity, multiple features
- `high` - Complex projects, many features, integrations

#### `key_features` (Array, Optional)
Key features/requirements:
- `authentication` - User authentication
- `payments` - Payment processing
- `real-time` - Real-time updates
- `offline` - Offline functionality
- `collaboration` - Collaborative features
- `analytics` - Analytics/reporting
- `notifications` - Push notifications
- `file_upload` - File handling
- `search` - Search functionality
- etc.

#### `tech_stack` (Array, Required)
Technology stack:
- Frontend: `React Native`, `Expo`, `Next.js`, `React`, `TypeScript`, `JavaScript`
- Backend: `Python`, `FastAPI`, `Node.js`, `Express`
- Database: `PostgreSQL`, `MongoDB`, `SQLite`
- Infrastructure: `Terraform`, `Kubernetes`, `Docker`
- etc.

---

## Blueprint Definitions

Currently, **12 project types** have explicit blueprint definitions in `_build_structure_blueprint()`:

### 1. Mobile App (`mobile_app`)

**Triggered when**: 
- `project_type == "mobile_app"` OR
- `"react native" in tech_stack` OR
- `"expo" in tech_stack`

**Expected Directories** (11):
- `src/screens` (required) - Mobile app screens/pages
- `src/components` (required) - Reusable UI components
- `src/navigation` (required) - Navigation setup
- `src/services` (required) - API clients, Firebase services
- `src/hooks` (required) - Custom React hooks
- `src/store` (required) - State management (Redux/Zustand)
- `src/theme` (required) - Colors, typography, spacing
- `src/types` (required) - TypeScript type definitions
- `src/utils` (required) - Helper functions
- `assets/images` (optional) - Image assets
- `assets/fonts` (optional) - Font assets

**Expected Files** (5):
- `App.tsx` (required) - Main app entry point
- `package.json` (required) - Dependencies and scripts
- `tsconfig.json` (required) - TypeScript configuration
- `android/app/src/main/AndroidManifest.xml` (optional) - Android manifest
- `ios/Info.plist` (optional) - iOS info plist

---

### 2. Web App (`web_app`)

**Triggered when**: 
- `project_type == "web_app"` OR
- `"next.js" in tech_stack` OR
- `("react" in tech_stack AND "next" in tech_stack)`

**Expected Directories** (8):
- `src/pages` (required) - Next.js route pages
- `src/components` (required) - Reusable UI components
- `src/app/api` (optional) - Backend API endpoints
- `src/services` (required) - API clients, external integrations
- `src/hooks` (required) - Custom React hooks
- `src/utils` (required) - Helper functions
- `src/types` (required) - TypeScript definitions
- `src/styles` (optional) - CSS/styled-components configuration

**Expected Files** (3):
- `package.json` (required) - Dependencies and scripts
- `tsconfig.json` (required) - TypeScript configuration
- `next.config.js` (optional) - Next.js configuration

---

### 3. API Service (`api_service`)

**Triggered when**: 
- `project_type == "api_service"` OR
- `"fastapi" in tech_stack` OR
- `("python" in tech_stack AND "api" in tech_stack)`

**Expected Directories** (7):
- `src/api` (required) - API route handlers
- `src/models` (required) - Database models (SQLAlchemy)
- `src/schemas` (required) - Pydantic schemas
- `src/services` (required) - Business logic services
- `src/utils` (required) - Helper functions
- `src/config` (required) - Configuration management
- `src/middleware` (optional) - Custom middleware

**Expected Files** (3):
- `main.py` (required) - FastAPI application entry point
- `requirements.txt` (required) - Python dependencies
- `.env.example` (optional) - Environment variables template

---

## Common Directories/Files (All Types)

All project types include these common directories:
- `tests` (optional) - Test files
- `docs` (optional) - Documentation

---

## Fallback Behavior

### For Unsupported Project Types

If a project is classified as a type **without** an explicit blueprint (future types not yet predicted):

1. **Blueprint Builder**: Returns a minimal blueprint with:
   - `project_type`: The classified type
   - `tech_stack`: From classification
   - `platforms`: From classification
   - `key_features`: From classification
   - `expected_directories`: Only common directories (`tests`, `docs`)
   - `expected_files`: Empty

2. **QA Agent**: Falls back to hardcoded expectations based on tech stack:
   - If `"React Native"` or `"Expo"` → Uses mobile app expectations
   - If `"Next.js"` or `"React"` → Uses web app expectations
   - If `"FastAPI"` or `"Python"` → Uses API service expectations
   - Otherwise → Uses minimal expectations

---

## Example Classifications

### Example 1: Mobile App
```json
{
  "type": "mobile_app",
  "platforms": ["android", "ios"],
  "domain": "productivity",
  "complexity": "medium",
  "key_features": ["authentication", "offline", "notifications"],
  "tech_stack": ["React Native", "TypeScript", "Firebase"]
}
```
**Blueprint**: ✅ Full mobile app blueprint (11 directories, 5 files)

---

### Example 2: Web App
```json
{
  "type": "web_app",
  "platforms": ["web"],
  "domain": "ecommerce",
  "complexity": "high",
  "key_features": ["authentication", "payments", "real-time"],
  "tech_stack": ["Next.js", "React", "TypeScript", "Stripe"]
}
```
**Blueprint**: ✅ Full web app blueprint (8 directories, 3 files)

---

### Example 3: API Service
```json
{
  "type": "api_service",
  "platforms": ["cloud"],
  "domain": "finance",
  "complexity": "high",
  "key_features": ["authentication", "payments", "webhooks"],
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Stripe"]
}
```
**Blueprint**: ✅ Full API service blueprint (7 directories, 3 files)

---

### Example 4: SaaS Platform
```json
{
  "type": "saas_platform",
  "platforms": ["web", "cloud"],
  "domain": "enterprise",
  "complexity": "high",
  "key_features": ["authentication", "multi-tenancy", "analytics"],
  "tech_stack": ["Next.js", "Python", "FastAPI", "PostgreSQL"]
}
```
**Blueprint**: ✅ Full SaaS platform blueprint (10 directories, 4 files)

---

### Example 5: Data Pipeline
```json
{
  "type": "data_pipeline",
  "platforms": ["cloud"],
  "domain": "analytics",
  "complexity": "medium",
  "key_features": ["data_processing", "scheduling", "monitoring"],
  "tech_stack": ["Python", "Apache Airflow", "PostgreSQL"]
}
```
**Blueprint**: ✅ Full data pipeline blueprint (9 directories, 3 files)

---

### Example 6: Microservice
```json
{
  "type": "microservice",
  "platforms": ["cloud"],
  "domain": "finance",
  "complexity": "high",
  "key_features": ["authentication", "api", "scalability"],
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"]
}
```
**Blueprint**: ✅ Full microservice blueprint (9 directories, 4 files)

---

## Adding New Blueprint Types

To add a new blueprint type:

1. **Add condition** in `_build_structure_blueprint()`:
```python
elif project_type == "new_type" or "technology" in tech_stack_str:
    blueprint["expected_directories"] = [
        {"path": "src/...", "required": True, "description": "..."},
        ...
    ]
    blueprint["expected_files"] = [
        {"path": "...", "required": True, "description": "..."},
        ...
    ]
```

2. **Update documentation** (this file)

3. **Test** with sample projects

---

## Summary

| Project Type | LLM Can Classify | Has Blueprint | Directories | Files |
|-------------|------------------|---------------|-------------|-------|
| `mobile_app` | ✅ | ✅ | 11 | 5 |
| `web_app` | ✅ | ✅ | 8 | 3 |
| `api_service` | ✅ | ✅ | 7 | 3 |
| `saas_platform` | ✅ | ✅ | 10 | 4 |
| `data_pipeline` | ✅ | ✅ | 9 | 3 |
| `microservice` | ✅ | ✅ | 9 | 4 |
| `desktop_app` | ✅ | ✅ | 8 | 4 |
| `cli_tool` | ✅ | ✅ | 5 | 4 |
| `library` | ✅ | ✅ | 5 | 5 |
| `infrastructure` | ✅ | ✅ | 6 | 5 |
| `blockchain_app` | ✅ | ✅ | 7 | 4 |
| `ml_service` | ✅ | ✅ | 10 | 5 |
| Other types | ✅ | ❌ | 2 (common) | 0 |

---

**Documented By**: QA Engineer (Terminator Bug Killer)  
**Date**: November 29, 2025

