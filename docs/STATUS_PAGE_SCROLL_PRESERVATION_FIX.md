# Status Page Scroll Preservation Fix

## Problem
The Status page (`/status`) was experiencing flickering and automatically scrolling back to the top whenever data reloaded. This was a critical UI/UX issue that occurred when:
- Users scrolled down to view tasks or agent activity
- Data updates occurred (every 2 seconds via polling)
- GraphQL subscriptions delivered real-time updates
- The page would automatically jump back to the top, disrupting user experience

## Root Cause
The page uses multiple data sources that trigger frequent re-renders:
1. **Polling interval**: Re-executes GraphQL query every 2 seconds
2. **GraphQL subscriptions**: Three subscriptions for agent activity, task updates, and system metrics
3. **State updates**: Multiple `useEffect` hooks that update state when data changes

When React re-renders the component due to state updates, the browser's default behavior can cause the page to scroll to the top, especially if:
- The DOM structure changes
- Focus is lost
- Component remounts occur

## Solution
Implemented scroll position preservation using React hooks:

### 1. Scroll Position Tracking
- Added a `scrollPositionRef` to continuously track the current scroll position
- Added a scroll event listener to update the ref whenever the user scrolls
- This ensures we always have the latest scroll position before any re-render

### 2. Scroll Restoration
- Added `shouldRestoreScrollRef` flag to indicate when scroll should be restored
- Used `useLayoutEffect` to restore scroll position synchronously after React renders
- Only restores scroll if the user was scrolled down (position > 0)

### 3. State Update Integration
- Modified all state update `useEffect` hooks to set `shouldRestoreScrollRef.current = true` before updating state
- This ensures scroll is restored after each data update:
  - Project query polling
  - Task updates subscription
  - Metrics stream subscription
  - Project data updates

## Implementation Details

### Files Modified
- `addon_portal/apps/tenant-portal/src/pages/status.tsx`

### Key Changes

```typescript
// Added imports
import { useState, useEffect, useRef, useLayoutEffect } from 'react';

// Scroll position preservation
const scrollPositionRef = useRef<number>(0);
const shouldRestoreScrollRef = useRef<boolean>(false);

// Track scroll position continuously
useEffect(() => {
  const handleScroll = () => {
    scrollPositionRef.current = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
  };
  
  window.addEventListener('scroll', handleScroll, { passive: true });
  return () => window.removeEventListener('scroll', handleScroll);
}, []);

// Restore scroll position after re-renders
useLayoutEffect(() => {
  if (shouldRestoreScrollRef.current && scrollPositionRef.current > 0) {
    window.scrollTo(0, scrollPositionRef.current);
    shouldRestoreScrollRef.current = false;
  }
});

// Example: Modified polling interval
useEffect(() => {
  if (!selectedProjectId) return;
  
  const interval = setInterval(() => {
    shouldRestoreScrollRef.current = true; // Mark for scroll restoration
    reexecuteProject({ requestPolicy: 'network-only' });
  }, 2000);
  
  return () => clearInterval(interval);
}, [selectedProjectId, reexecuteProject]);
```

## Benefits
1. **Improved UX**: Users can scroll down and stay at their position while data updates
2. **No Flickering**: Smooth updates without visual disruption
3. **Real-time Updates**: Data still updates in real-time, but scroll position is preserved
4. **Performance**: Uses `useLayoutEffect` for synchronous restoration (before paint)
5. **Non-intrusive**: Only restores scroll if user was scrolled down (doesn't interfere with top-of-page viewing)

## Testing
To verify the fix:
1. Navigate to `/status` page
2. Select a project
3. Scroll down to view tasks or agent activity
4. Wait for data updates (every 2 seconds)
5. Verify that scroll position is maintained and page doesn't jump to top
6. Verify that real-time updates still work (tasks, metrics, agents update)

## Related Issues
- GraphQL field conflict (fixed separately)
- Database connection leaks (fixed separately)
- Project edit page errors (fixed separately)

## Date
2025-11-26

