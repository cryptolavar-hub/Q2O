# Q2O Admin Portal Design System

Foundational tokens and UI primitives used to deliver the modernized admin experience.

## Folder Structure

```
src/design-system/
├── tokens.ts          # Color palette, gradients, spacing, shadows, typography
├── utils.ts           # Shared helpers (class name merge)
├── Card.tsx           # Rounded card wrapper with glass/soft variants
├── Button.tsx         # Gradient-aware button component
├── Badge.tsx          # Status badges (success/warning/info/etc.)
├── StatCard.tsx       # Metric card built on Card + Badge
└── index.ts           # Barrel exports for easy imports (`@/design-system`)
```

## Usage

```tsx
import { Card, Button, StatCard } from '@/design-system';

<Card className="p-6">
  <h2 className="text-lg font-semibold">Tenant Summary</h2>
  <p className="text-gray-500">Review tenant activity at a glance.</p>
  <Button className="mt-4">Add Tenant</Button>
</Card>

<StatCard
  title="Active Tenants"
  value={12}
  subtitle="+3 in the last 7 days"
  trend={{ value: 14.5, direction: 'up' }}
  icon="👥"
/>
```

## Roadmap Alignment

- **Task 1.3 (Day 1 Afternoon)** – this folder establishes the shared tokens and the initial component set (Card, Button, Badge, StatCard) to be consumed when modernizing the dashboard and analytics pages.
- Additional primitives (e.g., inputs, tabs, skeletons) can be layered here as we progress through Week 1 UI polish.

## Notes

- Components rely on Tailwind utility classes; ensure new pages import them from `@/design-system` rather than re-declaring custom styles.
- `Button` supports `variant`, `size`, `loading`, and optional icons to standardize actions across the portal.
- `StatCard` will replace ad-hoc metric cards currently hard-coded in `index.tsx` during Task 1.5.
