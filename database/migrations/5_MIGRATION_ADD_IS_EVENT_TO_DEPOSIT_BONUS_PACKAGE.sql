-- ============================================
-- MIGRATION: Add is_event field to deposit_bonus_package table
-- ============================================
-- Date: 2025-12-19
-- Description: Adds is_event BIT field to deposit_bonus_package table to distinguish
--              between regular packages and event-based packages (e.g., Christmas, New Year)
-- ============================================

USE printing_service_db;
GO

-- Step 1: Add the is_event column with default value 0 (false)
ALTER TABLE deposit_bonus_package
ADD is_event BIT NOT NULL DEFAULT 0;
GO

-- Step 2: Update existing data based on package codes
-- Set is_event = 1 for event-based packages (e.g., XMAS_25 for Christmas)
UPDATE deposit_bonus_package
SET is_event = 1
WHERE code IN ('XMAS_25');  -- Add other event package codes here as needed
GO

-- Step 3: Verify the changes
-- Uncomment the following to verify:
-- SELECT package_id, code, package_name, is_active, is_event, created_at
-- FROM deposit_bonus_package
-- ORDER BY is_event DESC, amount_cap ASC;
-- GO

-- ============================================
-- MIGRATION: Remove dot prefix from file extensions in permitted_file_type table
-- ============================================
-- Description: Updates file_extension column to remove leading dot (e.g., ".pdf" -> "pdf")
--              This ensures consistency with the updated data generation script
-- ============================================

-- Step 4: Remove dot prefix from file extensions
-- SQL Server: Remove leading dot if present
UPDATE permitted_file_type
SET file_extension = CASE 
    WHEN file_extension LIKE '.%' THEN SUBSTRING(file_extension, 2, LEN(file_extension))
    ELSE file_extension
END
WHERE file_extension LIKE '.%';
GO

-- Step 5: Verify the file extension changes
-- Uncomment the following to verify:
-- SELECT file_type_id, file_extension, mime_type, description, is_permitted
-- FROM permitted_file_type
-- ORDER BY file_extension;
-- GO

-- ============================================
-- Migration completed successfully
-- ============================================

