# Dual-Stack IPv4/IPv6 Explanation

## What Does "Two Instances" Mean?

When we say "two instances" for dual-stack support, we mean running **two separate uvicorn server processes** simultaneously:

### Instance 1: IPv4 Server
- **Binds to**: `0.0.0.0:8080`
- **Accepts**: IPv4 connections (127.0.0.1, localhost IPv4, etc.)
- **Process**: One uvicorn server instance

### Instance 2: IPv6 Server  
- **Binds to**: `[::]:8080`
- **Accepts**: IPv6 connections (::1, localhost IPv6, etc.)
- **Process**: Another uvicorn server instance

### How They Work Together

Both instances:
- Share the **same FastAPI application** (`api.main:app`)
- Listen on the **same port** (8080) but different address families
- Run **concurrently** in the same Python process using `asyncio.gather()`
- Handle requests **independently** - IPv4 requests go to Instance 1, IPv6 requests go to Instance 2

## Visual Diagram

```
┌─────────────────────────────────────────┐
│         Python Process                  │
│  ┌───────────────────────────────────┐  │
│  │   FastAPI App (api.main:app)     │  │
│  │   (Shared by both instances)      │  │
│  └───────────────────────────────────┘  │
│           ↕              ↕              │
│  ┌──────────────┐  ┌──────────────┐    │
│  │ Instance 1   │  │ Instance 2   │    │
│  │ IPv4 Server  │  │ IPv6 Server  │    │
│  │ 0.0.0.0:8080 │  │ [::]:8080    │    │
│  └──────────────┘  └──────────────┘    │
│         ↓                  ↓            │
│    IPv4 Traffic      IPv6 Traffic       │
└─────────────────────────────────────────┘
```

## Why Two Instances?

On Windows, uvicorn doesn't support true dual-stack sockets (one socket handling both IPv4 and IPv6). So we need:

1. **One socket** bound to IPv4 (`0.0.0.0`)
2. **Another socket** bound to IPv6 (`::`)

Both sockets can listen on the same port (8080) because they're different address families.

## How to Enable Dual-Stack

### Option 1: Environment Variable (Recommended)

Add to your root `.env` file:
```env
ENABLE_DUAL_STACK=true
```

Then restart the API server. It will automatically start both instances.

### Option 2: Manual Script

Use the dedicated dual-stack script:
```powershell
cd addon_portal
python start_api_windows_dual_stack.py
```

## Verification

After enabling dual-stack, check with:
```powershell
netstat -ano | findstr 8080
```

You should see **both**:
```
TCP    0.0.0.0:8080    0.0.0.0:0    LISTENING    <PID>
TCP    [::]:8080      [::]:0       LISTENING    <PID>
```

## Testing

### Test IPv4:
```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8080
curl http://127.0.0.1:8080/docs
```

### Test IPv6:
```powershell
Test-NetConnection -ComputerName ::1 -Port 8080
curl http://[::1]:8080/docs
```

## Performance Impact

- **Memory**: ~2x (two server instances)
- **CPU**: Minimal (both share the same event loop)
- **Connections**: Both instances can handle requests concurrently
- **Database**: Shared connection pool (no duplication)

## When to Use Dual-Stack

✅ **Enable dual-stack when:**
- You need IPv6 support
- Testing IPv6 connectivity
- Preparing for IPv6-only networks
- Future-proofing your infrastructure

❌ **Keep IPv4-only when:**
- IPv4 is sufficient (most common)
- Minimizing resource usage
- Simpler debugging
- Development/testing environments

## Default Behavior

By default, dual-stack is **disabled** (`ENABLE_DUAL_STACK=false`), so the API only listens on IPv4 (`0.0.0.0:8080`). This is the recommended setting for most use cases.

