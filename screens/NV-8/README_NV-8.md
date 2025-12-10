## Notes before implementing NV-8 (Quản lý quỹ tiền in)

- You asked to:  
  1) Write NV-8-Quản lý quỹ tiền in in `requirements/NV-8.txt` in the same detailed format as NV-5 (UI breakdown, interactive flows, use cases).  
  2) Create a corresponding view in `screens/NV-8/` consistent with existing styles (see `screens/NV-5/base.html`).  
  3) Keep the view simple (avoid over-scoping), include pagination/search/filter/order and export to Excel/PDF for funds.

- Relevant context:  
  - Existing UI pattern: `screens/NV-5/base.html` (layout, cards, filters, table, pagination).  
  - Data: fund tables exist (`fund_source`, `supplier_paper_purchase`, `paper_purchase_item`), but the page is focused on viewing funds, overall stats, and export.

- What to produce:  
  - `requirements/NV-8.txt`:  
    * Section 1: What’s on the page (UI components, stats, filters, table).  
    * Section 2: Interactive flow (user actions: load, search/filter, sort, paginate, view detail modal).  
    * Section 3: Use case tables (two use cases: view funds; export Excel/PDF).  
  - `screens/NV-8/base.html`: a single-page mockup following the NV-5 style: header, sidebar, stats cards, filters (search, type, date), table with pagination, and export buttons.

- Keep scope tight: only funds (from `fund_source`), with simple filters (type, date range, search by name/note), sortable columns, and export actions.

