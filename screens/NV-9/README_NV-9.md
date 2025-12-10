## Notes before implementing NV-9 (Quản lý chi tiền mua giấy)

- You asked to create a view for NV-9: managing spend for purchasing paper, following existing styles (see `screens/NV-5/base.html`, `screens/NV-8/base.html`) and keeping the UI in English while requirement text stays Vietnamese.
- What to produce:
  - `requirements/NV-9.txt`: detailed spec similar to NV-5/NV-8 (UI breakdown, interaction flows, use cases).
  - `screens/NV-9/base.html`: static mock view with header/sidebar, stats, filters, table, pagination, actions (view/update/delete), and modals (detail, create, update, delete), plus export buttons in the table header.
- Scope (keep it simple):
  - List paper purchases (supplier, dates, amounts, payment method/status, invoice, notes).
  - Filters: search (supplier/invoice/notes), status, method, date range.
  - Actions: view detail, create purchase, update purchase, delete purchase; export PDF/Excel.
- Reuse styling patterns from NV-8 (cards, table, badges, action icon buttons, modals).

