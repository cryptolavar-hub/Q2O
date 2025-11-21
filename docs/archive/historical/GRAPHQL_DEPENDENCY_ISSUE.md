# GraphQL Dependency Compatibility Issue

## Problem
The backend API fails to start with:
```
ModuleNotFoundError: No module named 'strawberry'
```

After installing strawberry-graphql, there's a compatibility issue:
```
ImportError: cannot import name 'is_new_type' from 'pydantic._internal._typing_extra'
```

## Root Cause
- **strawberry-graphql 0.236.0** is incompatible with **pydantic 2.7.1**
- The `is_new_type` function was removed/changed in pydantic 2.x
- Strawberry 0.236.0 was built for an older pydantic version

## Solutions

### Option 1: Install Latest Strawberry (Recommended)
```bash
python -m pip uninstall -y strawberry-graphql strawberry
python -m pip install "strawberry-graphql[fastapi]>=0.220.0" --upgrade
```

### Option 2: Use Compatible Version
```bash
python -m pip install "strawberry-graphql[fastapi]==0.227.0"
```

### Option 3: Temporarily Disable GraphQL (Quick Fix)
Comment out the GraphQL router import in `addon_portal/api/main.py`:
```python
# from .graphql import router as graphql_router
# base_app.include_router(graphql_router.router)  # GraphQL API
```

## Current Status
- ✅ Frontend GraphQL dependencies installed (`urql`, `graphql-ws`)
- ❌ Backend GraphQL dependencies need compatibility fix
- ⏳ Backend API cannot start until strawberry is properly installed

## Next Steps
1. Install compatible strawberry version
2. Verify import: `python -c "from strawberry.fastapi import GraphQLRouter; print('OK')"`
3. Restart backend API
4. Test GraphQL endpoint: `http://localhost:8080/graphql`

