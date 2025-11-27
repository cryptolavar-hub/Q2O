#!/usr/bin/env python
"""Check projects data in database to understand Active Projects count."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from addon_portal.api.core.db import AsyncSessionLocal
from addon_portal.api.models.llm_config import LLMProjectConfig
from sqlalchemy import select, func

async def check_projects():
    async with AsyncSessionLocal() as db:
        # Total projects
        result = await db.execute(select(func.count(LLMProjectConfig.id)))
        total = result.scalar()
        
        # Active projects (is_active=True)
        result = await db.execute(
            select(func.count(LLMProjectConfig.id)).where(LLMProjectConfig.is_active == True)
        )
        active_is_active = result.scalar()
        
        # Projects with project_status='active'
        result = await db.execute(
            select(func.count(LLMProjectConfig.id)).where(LLMProjectConfig.project_status == 'active')
        )
        active_status = result.scalar()
        
        # Projects with execution_status='running'
        result = await db.execute(
            select(func.count(LLMProjectConfig.id)).where(LLMProjectConfig.execution_status == 'running')
        )
        running = result.scalar()
        
        # Sample projects
        result = await db.execute(
            select(LLMProjectConfig.project_id, LLMProjectConfig.client_name, 
                   LLMProjectConfig.is_active, LLMProjectConfig.project_status, 
                   LLMProjectConfig.execution_status).limit(10)
        )
        projects = result.all()
        
        print("=" * 60)
        print("PROJECTS DATA ANALYSIS")
        print("=" * 60)
        print(f"Total projects: {total}")
        print(f"Active projects (is_active=True): {active_is_active}")
        print(f"Projects with project_status='active': {active_status}")
        print(f"Projects with execution_status='running': {running}")
        print("\nSample projects:")
        print("-" * 60)
        for p in projects:
            print(f"  {p.project_id}")
            print(f"    Client: {p.client_name}")
            print(f"    is_active: {p.is_active}")
            print(f"    project_status: {p.project_status}")
            print(f"    execution_status: {p.execution_status}")
            print()

if __name__ == "__main__":
    asyncio.run(check_projects())

