# Project Structure

This document describes the organization of the PMTM Database project.

## Directory Structure

```
pmtm_database/
├── README.md                    # Main project README
├── docs/                        # Documentation
│   ├── DEVELOPER_GUIDE.md      # Comprehensive developer guide
│   ├── README_FLOOR_DIAGRAMS.md # Floor diagram documentation
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── requirements/            # Project requirements
│       ├── *.txt                # Requirement documents
│       └── *.pdf                # Requirement PDFs
│
├── database/                    # Database-related files
│   ├── schema/                  # Database schema definitions
│   │   ├── design.sql          # Main schema definition
│   │   └── insert.sql          # Initial data insertion
│   ├── migrations/              # Database migration scripts
│   │   └── *_MIGRATION_*.sql   # Migration files
│   ├── change_logs/            # Schema change documentation
│   │   └── *_CHANGELOG_*.md    # Change log files
│   └── scripts/                 # Database utility scripts
│       ├── delete.sql          # Cleanup scripts
│       └── pricing_balance_notes.txt
│
├── scripts/                     # Python scripts
│   ├── pipeline/               # Data generation pipeline
│   │   ├── generate.py         # Main data generator
│   │   ├── execute_sql_file.py # SQL execution utility
│   │   ├── generate_module_diagrams.py
│   │   ├── specs.yaml          # Generation specifications
│   │   └── test_query.sql
│   ├── maps/                    # Floor diagram generation
│   │   ├── floor_generator.py  # Main floor generator
│   │   ├── driver.py
│   │   ├── convert_svgs_to_png.py
│   │   ├── generate_test_output.py
│   │   ├── specs/              # Floor templates (JSON)
│   │   ├── floors_diagrams/    # Generated floor diagrams
│   │   ├── output/             # Test output
│   │   └── output_test/        # Test output
│   └── visualize/              # Diagram rendering
│       ├── render_diagrams.py  # Main diagram renderer
│       ├── fix_diagram_dimensions.py
│       ├── visualize.py
│       ├── README.md
│       ├── DIAGRAM_DESCRIPTIONS.md
│       ├── ARCHITECTURE_DESIGN.md
│       ├── database/           # Database diagrams
│       ├── activity_diagrams/  # Activity diagrams
│       ├── sequence_diagrams/  # Sequence diagrams
│       ├── class_diagrams/     # Class diagrams
│       ├── component_diagrams/# Component diagrams
│       ├── architecture_diagrams/# Architecture diagrams
│       └── modules/            # Module diagrams
│
├── tests/                       # Test files
│   ├── test_db_connection.py  # Database connection tests
│   └── requirements_db_test.txt
│
├── assets/                      # Media and asset files
│   ├── docs/                   # Document assets
│   └── profile_pics/           # Profile picture assets
│
├── screens/                     # Screen mockups/templates
│   └── [screen_name]/
│       └── base.html
│
└── document_tasks/              # Task documentation
    └── *.txt
```

## Key Directories

### `docs/`
Contains all project documentation including developer guides, requirements, and technical documentation.

### `database/`
All database-related files:
- **schema/**: Core database schema and initial data
- **migrations/**: Version-controlled database changes
- **change_logs/**: Documentation of schema changes
- **scripts/**: Utility scripts for database operations

### `scripts/`
Python scripts organized by purpose:
- **pipeline/**: Data generation and SQL execution
- **maps/**: Floor diagram generation tools
- **visualize/**: UML diagram rendering

### `tests/`
Test files and test requirements.

### `assets/`
Static assets used by the application (documents, images, etc.).

## File Naming Conventions

- **SQL files**: `*_MIGRATION_*.sql` for migrations, descriptive names for others
- **Documentation**: `*.md` for Markdown, `*.txt` for plain text
- **Diagrams**: `*_diagram.puml` for PlantUML source, `*_diagram.png` for rendered output
- **Scripts**: `snake_case.py` for Python scripts

## Path References

When writing scripts, use relative paths from the script's location:
- From `scripts/pipeline/`: `../database/schema/` for database files
- From `scripts/visualize/`: `./` for diagram files in the same directory
- From `scripts/maps/`: `./specs/` for template files

## Migration Guide

If you're updating paths in existing scripts:
- Old: `../sql/` → New: `../database/schema/`
- Old: `../medias/` → New: `../assets/`
- Old: `../pipeline/` → New: `./` (if in scripts/pipeline/)

