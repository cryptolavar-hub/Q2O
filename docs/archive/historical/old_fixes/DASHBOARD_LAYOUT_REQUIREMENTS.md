# Dashboard Layout Requirements

## Widget Layout Structure

The Admin Dashboard stat cards are arranged in a **two-row layout**:

### First Row
- **4 widgets** displayed in a responsive grid:
  - Activation Codes
  - Authorized Devices
  - Active Projects
  - Tenants
- **Grid Layout**: `grid-cols-1 md:grid-cols-2 xl:grid-cols-4`
  - Mobile: 1 column (stacked)
  - Tablet: 2 columns (2x2 grid)
  - Desktop: 4 columns (all in one row)

### Second Row
- **1 widget** (Success Rate) displayed left-aligned:
  - Same grid system as first row (`grid-cols-1 md:grid-cols-2 xl:grid-cols-4`)
  - Same height and width as first row widgets
  - Left-aligned for consistency and future expandability
  - Maintains same card styling and appearance

## Rationale

1. **Visual Balance**: Prevents clustering too many widgets in one row
2. **Clean Design**: Success Rate gets visual emphasis in its own row
3. **Responsive**: Works well on all screen sizes
4. **Consistent Styling**: All widgets maintain the same card style and appearance
5. **Future-Proof**: Left-aligned layout prepares for customizable dashboard system
6. **Consistent Sizing**: All widgets same size for drag-and-drop compatibility

## Implementation Notes

- First row uses `mainMetrics` array (4 items)
- Second row uses `successRateMetric` object (single item)
- Loading states match the widget count (4 for first row, 1 for second row)
- Animation delays staggered for visual appeal

## Files Affected

- `addon_portal/apps/admin-portal/src/pages/index.tsx`

## Future Changes

If adding more widgets:
- Use same grid system (`xl:grid-cols-4`) for all rows
- Widgets left-aligned for consistency
- All widgets same size (height and width)
- Additional widgets fill rows left-to-right, top-to-bottom
- See `docs/CUSTOMIZABLE_DASHBOARD_ROADMAP.md` for full customization plans

