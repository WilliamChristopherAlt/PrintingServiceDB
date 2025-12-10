# NV-5: System Logs & Audit Page - Implementation Guide

## Overview
This document outlines the UI structure and requirements for the Printers Logs page (NV-5) based on the requirements document.

## Page Structure

### 1. Header Section
- **Title**: "System Logs & Audit"
- **Subtitle**: "View and search system logs for troubleshooting and auditing"
- **Warning Banner** (conditional):
  - Display if errors/warnings exist in the system
  - Icon: ⚠️
  - Text: "[X] error(s) and [Y] warning(s) in the system. Please review."
  - Background: Yellow (warning) or Red (error)
  - Close button (X) in top-right corner

### 2. Statistics Cards (3 cards in a row)
- **Card 1: Total Records**
  - Icon: 📊
  - Color: Blue
  - Value: Total number of log entries
  
- **Card 2: Errors**
  - Icon: ❌
  - Color: Red
  - Value: Count of logs with severity = 'error' or 'critical'
  
- **Card 3: Warnings**
  - Icon: ⚠️
  - Color: Yellow
  - Value: Count of logs with severity = 'warning'

### 3. Filter Section
- **Search Bar**:
  - Icon: 🔍
  - Placeholder: "Search by printer, description, error code..."
  - Auto-search after 500ms delay
  - Searches in: printer location, description, error code

- **Filter Dropdowns (2 columns)**:
  - **Column 1: Type**
    - Label: "Type"
    - Options: All Types (default), Print Job, Error, Maintenance, Status Change, Configuration, Admin Action
    - Single select
  
  - **Column 2: Severity**
    - Label: "Severity"
    - Options: All Levels (default), Info, Warning, Error, Critical
    - Single select

- **Date Range Filters (2 columns)**:
  - **Date From**: Date picker with placeholder "From date" and calendar icon 📅
  - **Date To**: Date picker with placeholder "To date" and calendar icon 📅

- **Action Buttons**:
  - **Apply**: Primary button to apply all filters
  - **Clear**: Secondary button to reset all filters

### 4. Table Section
- **Table Header**:
  - Title: "Log Entries"
  - Info: "Showing [X] of [Y] entries"
  - **Export Button**: Secondary button to export to PDF

- **Table Columns**:
  1. **Timestamp**: YYYY-MM-DD HH:MM format, sortable (default: descending)
  2. **Printer**: Location format "MÃ-TÒA-PHÒNG" (e.g., "LB-101", "SCI-202")
  3. **Type**: Badge with colors:
     - Print Job: Blue
     - Error: Red
     - Maintenance: Green
     - Status Change: Yellow
     - Configuration: Purple
     - Admin Action: Gray
  4. **Severity**: Badge with icon and color:
     - Info: Light blue, icon ℹ️
     - Warning: Yellow, icon ⚠️
     - Error: Red, icon ❌
     - Critical: Dark red, icon 🔴
  5. **Description**: Truncated to 80 characters with "..."
  6. **Actions**: "View" button or eye icon 👁️

- **Table Features**:
  - Hover effect on rows (light gray background)
  - Clickable rows (opens detail modal)
  - Responsive: Card layout on mobile

### 5. Pagination
- **Rows per page dropdown**: 10, 25, 50, 100 (default: 10)
- **Page info**: "Page [X] of [Y]"
- **Navigation buttons**:
  - First (⏮️)
  - Previous (◀️)
  - Page numbers (1, 2, 3, ...)
  - Next (▶️)
  - Last (⏭️)

### 6. Empty State
- **Icon**: 📋 with X
- **Title**: "No logs found"
- **Subtitle**: "Try adjusting your filters or search criteria"
- **Button**: "Clear Filters"

### 7. Loading State
- Skeleton loader for table rows
- Spinner in center
- Text: "Loading logs..."

### 8. Log Detail Modal
- **Header**:
  - Title: "Log Details"
  - Log ID badge (gray, monospace font)
  - Close button (X)

- **Body Sections** (6 sections):
  1. **Basic Information**:
     - Timestamp (full: YYYY-MM-DD HH:MM:SS)
     - Log Type (badge)
     - Severity (badge)
     - Status (badge: New/In Progress/Resolved/Closed)
  
  2. **Printer Information**:
     - Printer ID
     - Location: [Building]-[Room]
     - Printer Name: [Brand] [Model]
     - Serial Number
     - IP Address (if available)
  
  3. **Description & Details**:
     - Full description text
     - Error Code (badge, if exists)
     - Additional Details (JSON formatted with syntax highlighting, if exists)
  
  4. **Print Information** (if related to print job):
     - Print Job ID (clickable link)
     - User: Name ([ID])
     - Pages Printed
     - File Name
  
  5. **Resolution Information** (if resolved):
     - Resolved At: Timestamp
     - Resolved By: Staff Name ([Position])
     - Resolution Notes: Text
     - Actions Taken: Bullet points
  
  6. **Datetime**:
     - Created At: Timestamp
     - Last Updated: Timestamp (if exists)

- **Footer Buttons**:
  - Close (gray)
  - Mark as Resolved (blue, only if not resolved)
  - Add Note (yellow)

## UI Design Principles

### Color Scheme
- Use consistent color palette from existing pages
- Badges should have distinct colors for quick recognition
- Warning/Error states should be visually distinct

### Typography
- Clear hierarchy: Title > Section > Content
- Monospace font for IDs and timestamps
- Readable font sizes (14px for body, 12px for labels)

### Spacing & Layout
- Consistent padding and margins
- Grid layout for cards and filters
- Responsive breakpoints for mobile

### Interactions
- Smooth transitions (0.2s ease)
- Hover states on interactive elements
- Clear visual feedback for actions
- Disabled states for invalid actions

### Accessibility
- Proper ARIA labels
- Keyboard navigation support
- Screen reader friendly
- High contrast for text

## Data Flow

1. **Initial Load**:
   - Query logs from `printer_log_dashboard` view
   - Sort by `created_at` DESC
   - Limit to 10 records (default page size)
   - Calculate statistics (total, errors, warnings)
   - Show warning banner if errors/warnings in last 24h

2. **Search**:
   - Debounce 500ms
   - Search in: printer_location, description, error_code
   - Case-insensitive
   - Update table and statistics

3. **Filtering**:
   - Combine filters with AND logic
   - Update table and statistics
   - Reset to page 1

4. **Sorting**:
   - Click timestamp header to toggle: DESC → ASC → Default
   - Update table while maintaining filters

5. **Pagination**:
   - Change page size resets to page 1
   - Navigation updates OFFSET

6. **Export**:
   - Export current filtered results
   - PDF format (max 100 records)
   - Excel format (max 1000 records)

## Notes
- Follow the existing design patterns from SV-4 and SV-5 base.html
- Use the same CSS variable system
- Maintain consistency with sidebar, header, and card styles
- Ensure mobile responsiveness
- Implement proper error handling and loading states

