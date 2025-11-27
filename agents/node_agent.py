"""
Node.js Agent - Handles Node.js/JavaScript/TypeScript development.
Generates code for Express.js, NestJS, Next.js, and other Node.js frameworks.
Supports Node.js 20.x LTS (latest stable version).
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from utils.template_renderer import get_renderer
from utils.project_layout import ProjectLayout, get_default_layout
from utils.language_detector import get_language_detector
import os
import logging
import json


class NodeAgent(BaseAgent):
    """Agent responsible for Node.js/JavaScript/TypeScript development."""
    
    # Node.js LTS version (latest stable as of 2024)
    NODEJS_LTS_VERSION = "20.11.0"  # Node.js 20.x LTS
    
    def __init__(self, agent_id: str = "node_main", workspace_path: str = ".", 
                 project_layout: Optional[ProjectLayout] = None,
                 project_id: Optional[str] = None,
                 tenant_id: Optional[int] = None,
                 orchestrator: Optional[Any] = None):
        super().__init__(agent_id, AgentType.NODEJS, project_layout,
                        project_id=project_id, tenant_id=tenant_id, orchestrator=orchestrator)
        self.workspace_path = workspace_path
        self.node_files: List[str] = []
        self.template_renderer = get_renderer()
        self.language_detector = get_language_detector(workspace_path)
    
    def process_task(self, task: Task) -> Task:
        """
        Process a Node.js task by generating code.
        
        Args:
            task: The Node.js task to process
            
        Returns:
            The updated task
        """
        try:
            self.logger.info(f"Processing Node.js task: {task.title}")
            
            description = task.description.lower()
            files_created = []
            
            # Detect Node.js framework
            framework = self._detect_framework(description, task.metadata)
            
            if "express" in description or framework == "express":
                files_created.extend(self._create_express_app(task))
            
            if "nestjs" in description or framework == "nestjs":
                files_created.extend(self._create_nestjs_app(task))
            
            if "package.json" in description or "npm" in description:
                files_created.append(self._create_package_json(task))
            
            if "server" in description or "api" in description:
                files_created.append(self._create_server_file(task, framework))
            
            if "route" in description or "endpoint" in description:
                files_created.append(self._create_route_file(task, framework))
            
            if "middleware" in description:
                files_created.append(self._create_middleware(task))
            
            # Update task metadata
            task.metadata["node_files"] = files_created
            task.metadata["nodejs_version"] = self.NODEJS_LTS_VERSION
            task.metadata["framework"] = framework
            
            task.result = {
                "files_created": files_created,
                "framework": framework,
                "nodejs_version": self.NODEJS_LTS_VERSION,
                "status": "completed"
            }
            
            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed Node.js task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing Node.js task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
        
        return task
    
    def _detect_framework(self, description: str, metadata: Dict[str, Any]) -> str:
        """Detect Node.js framework from description or metadata."""
        # Check metadata first
        if "framework" in metadata:
            return metadata["framework"]
        
        # Detect from description
        if "nestjs" in description or "nest" in description:
            return "nestjs"
        elif "express" in description:
            return "express"
        elif "nextjs" in description or "next.js" in description:
            return "nextjs"
        elif "koa" in description:
            return "koa"
        elif "fastify" in description:
            return "fastify"
        
        # Default to Express
        return "express"
    
    def _create_package_json(self, task: Task) -> str:
        """Create package.json for Node.js project."""
        file_path = os.path.join(self.workspace_path, "package.json")
        
        # Detect existing package.json or create new
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
        else:
            package_data = {
                "name": "q2o-nodejs-project",
                "version": "1.0.0",
                "description": "Multi-Platform to Odoo Node.js integration",
                "main": "src/index.js",
                "type": "module",  # ESM modules
                "engines": {
                    "node": f">={self.NODEJS_LTS_VERSION}"
                },
                "scripts": {},
                "dependencies": {},
                "devDependencies": {}
            }
        
        # Ensure Node.js version requirement
        if "engines" not in package_data:
            package_data["engines"] = {}
        package_data["engines"]["node"] = f">={self.NODEJS_LTS_VERSION}"
        
        # Add common scripts
        if "scripts" not in package_data:
            package_data["scripts"] = {}
        
        # Add framework-specific dependencies and scripts
        framework = task.metadata.get("framework", "express")
        if framework == "express" and "express" not in package_data.get("dependencies", {}):
            package_data["dependencies"]["express"] = "^4.18.2"
            package_data["scripts"]["start"] = "node src/index.js"
            package_data["scripts"]["dev"] = "node --watch src/index.js"
        
        elif framework == "nestjs":
            if "@nestjs/core" not in package_data.get("dependencies", {}):
                package_data["dependencies"]["@nestjs/core"] = "^10.0.0"
                package_data["dependencies"]["@nestjs/common"] = "^10.0.0"
                package_data["dependencies"]["@nestjs/platform-express"] = "^10.0.0"
            package_data["scripts"]["start"] = "nest start"
            package_data["scripts"]["dev"] = "nest start --watch"
        
        # Write package.json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(package_data, f, indent=2)
        
        self.node_files.append("package.json")
        return "package.json"
    
    def _create_express_app(self, task: Task) -> List[str]:
        """Create Express.js application files."""
        files_created = []
        
        # Main app file
        app_file = os.path.join(self.project_layout.api_app_dir, "app.js")
        full_path = os.path.join(self.workspace_path, app_file)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = '''/**
 * Express.js Application
 * Generated by NodeAgent
 * Node.js ${NODEJS_VERSION} LTS
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/api', (req, res) => {
  res.json({ message: 'Multi-Platform to Odoo Migration API', version: '1.0.0' });
});

// Error handling
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: err.message });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

export default app;
'''.replace("${NODEJS_VERSION}", self.NODEJS_LTS_VERSION)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        files_created.append(app_file)
        self.node_files.append(app_file)
        
        return files_created
    
    def _create_nestjs_app(self, task: Task) -> List[str]:
        """Create NestJS application files."""
        files_created = []
        
        # Main module
        module_file = os.path.join(self.project_layout.api_app_dir, "app.module.ts")
        full_path = os.path.join(self.workspace_path, module_file)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = f'''/**
 * NestJS Application Module
 * Generated by NodeAgent
 * Node.js {self.NODEJS_LTS_VERSION} LTS
 */

import {{ Module }} from '@nestjs/common';
import {{ AppController }} from './app.controller';
import {{ AppService }} from './app.service';

@Module({{
  imports: [],
  controllers: [AppController],
  providers: [AppService],
}})
export class AppModule {{}}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        files_created.append(module_file)
        self.node_files.append(module_file)
        
        return files_created
    
    def _create_server_file(self, task: Task, framework: str) -> str:
        """Create server entry point file."""
        if framework == "nestjs":
            ext = ".ts"
            content = '''import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(3000);
}
bootstrap();
'''
        else:
            ext = ".js"
            content = '''import app from './app.js';

// Server is started in app.js
'''
        
        file_path = os.path.join(self.project_layout.api_app_dir, f"index{ext}")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.node_files.append(file_path)
        return file_path
    
    def _create_route_file(self, task: Task, framework: str) -> str:
        """Create route/endpoint file."""
        route_name = task.title.lower().replace(' ', '_')
        
        if framework == "nestjs":
            ext = ".ts"
            content = f'''import {{ Controller, Get, Post }} from '@nestjs/common';

@Controller('api/{route_name}')
export class {route_name.title().replace('_', '')}Controller {{
  @Get()
  findAll() {{
    return {{ message: '{route_name} endpoint' }};
  }}
  
  @Post()
  create() {{
    return {{ message: 'Created' }};
  }}
}}
'''
        else:
            ext = ".js"
            content = f'''/**
 * {route_name} Routes
 * Generated by NodeAgent
 */

import express from 'express';

const router = express.Router();

router.get('/', (req, res) => {{
  res.json({{ message: '{route_name} endpoint' }});
}});

router.post('/', (req, res) => {{
  res.json({{ message: 'Created', data: req.body }});
}});

export default router;
'''
        
        file_path = os.path.join(self.project_layout.api_app_dir, "routes", f"{route_name}{ext}")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.node_files.append(file_path)
        return file_path
    
    def _create_middleware(self, task: Task) -> str:
        """Create middleware file."""
        middleware_name = task.title.lower().replace(' ', '_')
        
        file_path = os.path.join(self.project_layout.api_app_dir, "middleware", f"{middleware_name}.js")
        full_path = os.path.join(self.workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        content = f'''/**
 * {middleware_name} Middleware
 * Generated by NodeAgent
 */

export default function {middleware_name.replace('-', '_')}(req, res, next) {{
  // Middleware logic
  next();
}}
'''
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.node_files.append(file_path)
        return file_path

