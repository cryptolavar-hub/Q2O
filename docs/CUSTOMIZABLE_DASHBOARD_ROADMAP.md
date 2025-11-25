# Customizable Widget Dashboard - Roadmap

## Overview
Plan for implementing a fully customizable widget dashboard system where users can:
- Add/remove widgets
- Rearrange widgets via drag-and-drop
- Configure widget settings
- Save custom layouts per user/role
- Add new widget types dynamically

## Current State (2025)
- **Fixed Layout**: Widgets arranged in predefined rows
- **5 Widgets**: Activation Codes, Devices, Projects, Tenants, Success Rate
- **Responsive Grid**: 4 columns on desktop, 2 on tablet, 1 on mobile
- **Left-aligned**: All widgets align to the left for consistency

## Future State (2026+)

### Phase 1: Widget System Foundation
- [ ] Widget registry system
- [ ] Widget configuration schema
- [ ] Widget component abstraction
- [ ] Widget data fetching layer

### Phase 2: Drag-and-Drop Layout
- [ ] Grid layout system (react-grid-layout or similar)
- [ ] Drag-and-drop functionality
- [ ] Resize widgets
- [ ] Save layout to database

### Phase 3: Widget Customization
- [ ] Widget settings panel
- [ ] Custom widget configurations
- [ ] Widget templates
- [ ] Widget marketplace/plugins

### Phase 4: Multi-User Layouts
- [ ] Per-user layouts
- [ ] Role-based default layouts
- [ ] Layout sharing
- [ ] Layout versioning

## Technical Requirements

### Widget Structure
```typescript
interface Widget {
  id: string;
  type: string;
  title: string;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, any>;
  dataSource: string;
  refreshInterval?: number;
}
```

### Layout Storage
- Store in database: `user_dashboard_layouts` table
- JSON format for flexibility
- Version control for layout changes

### Widget Types
1. **Stat Cards** (current)
2. **Charts** (line, bar, pie)
3. **Tables** (data grids)
4. **Activity Feeds**
5. **Maps** (geographic data)
6. **Custom HTML** (user-defined)

## Related Documentation
- `docs/UI_UX_MODERNIZATION_PLAN.md` - UI modernization plans
- `docs/md_docs/DASHBOARD_IMPLEMENTATION.md` - Dashboard implementation details
- Research: `Tenant_Projects/.../Custom_analytics_widgets_*.md` - Custom widgets research

## Notes
- Current layout is left-aligned to prepare for grid system
- Widget sizing is consistent to support drag-and-drop
- Grid system will use same responsive breakpoints

