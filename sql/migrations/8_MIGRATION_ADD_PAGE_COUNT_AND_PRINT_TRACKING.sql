-- ============================================
-- MIGRATION: Add page_count to uploaded_file and print tracking to print_job_page
-- ============================================
-- Date: 2025-12-20
-- Description: 
--  1. Adds page_count INT column to uploaded_file table
--  2. Adds is_printed BIT and printed_at DATETIME2 columns to print_job_page table
--  3. Adds performance indexes for print job queries
-- ============================================

USE printing_service_db;
GO

-- Step 1: Add page_count column to uploaded_file table
ALTER TABLE uploaded_file
ADD page_count INT NULL;
GO

-- Step 2: Update existing records with estimated page counts based on file_type and file_size_kb
-- For PDF: estimate ~50KB per page
-- For DOCX/PPTX: estimate ~30KB per page
-- For images: 1 page
UPDATE uploaded_file
SET page_count = CASE
    WHEN file_type = 'pdf' THEN NULLIF(CEILING(CAST(file_size_kb AS FLOAT) / 50.0), 0)
    WHEN file_type IN ('docx', 'pptx') THEN NULLIF(CEILING(CAST(file_size_kb AS FLOAT) / 30.0), 0)
    WHEN file_type IN ('jpg', 'png') THEN 1
    ELSE NULLIF(CEILING(CAST(file_size_kb AS FLOAT) / 40.0), 0)
END
WHERE page_count IS NULL;
GO

-- Step 3: Set default value for page_count (set to 1 if still NULL after estimation)
UPDATE uploaded_file
SET page_count = 1
WHERE page_count IS NULL;
GO

-- Step 4: Make page_count NOT NULL after populating data
ALTER TABLE uploaded_file
ALTER COLUMN page_count INT NOT NULL;
GO

-- Step 5: Add is_printed column to print_job_page table
ALTER TABLE print_job_page
ADD is_printed BIT DEFAULT 0 NOT NULL;
GO

-- Step 6: Add printed_at column to print_job_page table
ALTER TABLE print_job_page
ADD printed_at DATETIME2 NULL;
GO

-- Step 7: Update existing print_job_page records based on print_job status
-- Mark pages as printed if the job is completed
UPDATE pjp
SET pjp.is_printed = 1,
    pjp.printed_at = CASE 
        WHEN pj.end_time IS NOT NULL THEN pj.end_time
        WHEN pj.start_time IS NOT NULL THEN pj.start_time
        ELSE NULL
    END
FROM print_job_page pjp
INNER JOIN print_job pj ON pjp.job_id = pj.job_id
WHERE pj.print_status = 'completed';
GO

-- Step 8: For printing jobs, mark some pages as printed (random distribution)
UPDATE pjp
SET pjp.is_printed = CASE 
    WHEN pjp.page_number <= (SELECT COUNT(*) FROM print_job_page pjp2 WHERE pjp2.job_id = pjp.job_id) / 2 THEN 1
    ELSE 0
END,
    pjp.printed_at = CASE 
    WHEN pjp.page_number <= (SELECT COUNT(*) FROM print_job_page pjp2 WHERE pjp2.job_id = pjp.job_id) / 2 
    THEN pj.start_time
    ELSE NULL
END
FROM print_job_page pjp
INNER JOIN print_job pj ON pjp.job_id = pj.job_id
WHERE pj.print_status = 'printing' AND pj.start_time IS NOT NULL;
GO

-- Step 9: Add index for performance (counting printed pages)
CREATE INDEX idx_print_job_page_job_printed 
ON print_job_page(job_id, is_printed);
GO

-- Step 10: Add composite index for queue queries (optimize finding queued/printing jobs by printer)
CREATE INDEX idx_print_job_printer_status_created 
ON print_job(printer_id, print_status, created_at);
GO

-- Step 11: Add index for progress queries (optimize finding printing jobs)
CREATE INDEX idx_print_job_status_start_time 
ON print_job(print_status, start_time);
GO

-- Step 12: Verify the changes
-- Uncomment the following to verify:
-- SELECT TOP 10 
--     uf.uploaded_file_id, 
--     uf.file_name, 
--     uf.file_type, 
--     uf.file_size_kb, 
--     uf.page_count
-- FROM uploaded_file uf
-- ORDER BY uf.created_at DESC;
-- GO
--
-- SELECT TOP 10
--     pjp.page_record_id,
--     pjp.job_id,
--     pjp.page_number,
--     pjp.is_printed,
--     pjp.printed_at,
--     pj.print_status
-- FROM print_job_page pjp
-- INNER JOIN print_job pj ON pjp.job_id = pj.job_id
-- ORDER BY pj.created_at DESC;
-- GO

-- ============================================
-- Migration completed successfully
-- ============================================

