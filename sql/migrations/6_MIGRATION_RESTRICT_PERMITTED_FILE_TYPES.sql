-- ============================================
-- MIGRATION: Restrict permitted file types to pdf, docx, pptx, jpg, png only
-- ============================================
-- Date: 2025-12-19
-- Description: Removes all file types except pdf, docx, pptx, jpg, png from permitted_file_type table
--              This restricts the system to only allow these 5 file types for uploads
-- ============================================

USE printing_service_db;
GO

-- Step 1: Delete all file types except the allowed ones (pdf, docx, pptx, jpg, png)
DELETE FROM permitted_file_type
WHERE file_extension NOT IN ('pdf', 'docx', 'pptx', 'jpg', 'png');
GO

-- Step 2: Verify the changes
-- Uncomment the following to verify:
-- SELECT file_type_id, file_extension, mime_type, description, is_permitted
-- FROM permitted_file_type
-- ORDER BY file_extension;
-- GO

-- Expected result: Only 5 rows should remain:
-- - pdf
-- - docx
-- - pptx
-- - jpg
-- - png

-- ============================================
-- Migration completed successfully
-- ============================================

