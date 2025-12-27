# Diagram Visualization

This directory contains all PlantUML diagrams for the Smart Printing Service database and use cases.

## Directory Structure

```
visualize/
├── render_diagrams.py          # Main script to render all diagrams
├── database/                    # Database schema diagrams
│   ├── db_diagram.puml
│   └── db_diagram.png
├── activity_diagrams/          # Activity diagrams (workflow/process flow)
│   ├── print_document_activity_diagram.puml
│   ├── print_document_activity_diagram.png
│   ├── cancel_print_job_activity_diagram.puml
│   ├── cancel_print_job_activity_diagram.png
│   ├── deposit_to_account_activity_diagram.puml
│   └── deposit_to_account_activity_diagram.png
├── sequence_diagrams/           # Sequence diagrams (message interactions)
│   ├── print_document_sequence_diagram.puml
│   ├── print_document_sequence_diagram.png
│   ├── cancel_print_job_sequence_diagram.puml
│   ├── cancel_print_job_sequence_diagram.png
│   ├── deposit_to_account_sequence_diagram.puml
│   └── deposit_to_account_sequence_diagram.png
├── class_diagrams/              # Class diagrams (object structure)
│   ├── print_document_class_diagram.puml
│   └── print_document_class_diagram.png
└── modules/                    # Module-specific diagrams
    └── (various module diagrams)
```

## Usage

### Render All Diagrams

```bash
python render_diagrams.py
```

This will render all PlantUML (.puml) files to PNG images.

### Rendering Methods

The script supports three rendering methods (configured in `render_diagrams.py`):

1. **kroki** (default) - Fast and reliable online service
2. **local** - Requires Java and plantuml.jar installed locally
3. **plantuml** - Official PlantUML server (slower)

## Diagram Types

### Activity Diagrams
Show the workflow and process flow with swimlanes for different actors (User, System, Printer).

### Sequence Diagrams
Show message interactions between components over time (User, Web UI, Backend API, Database, Printer, Payment Gateway).

### Class Diagrams
Show the object structure and relationships between classes/entities involved in a use case.

### Database Diagram
Shows the complete database schema with all tables and relationships.

## Adding New Diagrams

1. Create the `.puml` file in the appropriate directory
2. Add entry to `DIAGRAMS` list in `render_diagrams.py`
3. Run `python render_diagrams.py` to generate PNG

