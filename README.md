# PMTM Database Project

Smart Printing Service System (SSPS) - Database Schema and Scripts

## Project Structure

```
pmtm_database/
├── docs/                    # Documentation
│   ├── DEVELOPER_GUIDE.md   # Developer guide
│   ├── README_FLOOR_DIAGRAMS.md
│   └── requirements/        # Project requirements
├── database/                # Database files
│   ├── schema/             # Schema definitions
│   ├── migrations/         # Migration scripts
│   ├── change_logs/       # Change logs
│   └── scripts/            # Utility scripts
├── scripts/                # Python scripts
│   ├── pipeline/           # Data generation
│   ├── maps/               # Floor diagram generation
│   └── visualize/          # Diagram rendering
├── tests/                  # Test files
└── assets/                 # Media files
    ├── docs/
    └── profile_pics/
```

## Quick Start

See `docs/DEVELOPER_GUIDE.md` for detailed information.

## Database

- Schema: `database/schema/design.sql`
- Initial data: `database/schema/insert.sql`
- Migrations: `database/migrations/`

## Scripts

- Data generation: `scripts/pipeline/generate.py`
- Diagram rendering: `scripts/visualize/render_diagrams.py`
