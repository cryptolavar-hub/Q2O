# Documentation Organization Plan
**Date**: November 27, 2025  
**Status**: In Progress

## Overview

Complete reorganization of all project documentation according to:
1. All markdown docs → `docs/` folder
2. README.md in every folder explaining contents
3. Old/irrelevant docs → `docs/archive/`
4. Changed but related docs → `docs/md_docs/`
5. Current docs → `docs/`

## Folder Structure

```
docs/
├── README.md (Main index)
├── archive/ (Old/irrelevant docs)
│   ├── historical/ (Historical sessions, old analysis)
│   ├── resolved_issues/ (Fixed bugs/issues)
│   └── outdated_2025/ (Pre-November 2025 outdated docs)
├── md_docs/ (Changed but related docs)
│   ├── README.md
│   └── [agent guides, testing, deployment, etc.]
├── status_reports/ (Current status reports)
│   └── README.md
├── implementation_summaries/ (Implementation docs)
│   └── README.md
├── addon_portal_review/ (Licensing system reviews)
│   └── README.md
└── website_content/ (Marketing content)
    └── README.md
```

## Assessment Criteria

### Current/Relevant → `docs/`
- Recent fixes (November 2025+)
- Current status reports
- Active implementation guides
- Current architecture docs
- Recent QA/testing docs

### Changed but Related → `docs/md_docs/`
- Agent guides (still relevant but evolved)
- Testing guides (still relevant but updated)
- Deployment guides (still relevant but changed)
- VCS integration guides

### Archive → `docs/archive/`
- Pre-November 2025 outdated content
- Historical sessions
- Resolved issues (already fixed)
- Old analysis documents

## Execution Steps

1. ✅ Create organization plan
2. ⬜ Assess all markdown files
3. ⬜ Move files to appropriate locations
4. ⬜ Create README.md files for all folders
5. ⬜ Update root README.md
6. ⬜ Update all links

