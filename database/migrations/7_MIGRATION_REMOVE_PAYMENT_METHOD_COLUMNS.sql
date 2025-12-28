-- ============================================
-- MIGRATION: Remove payment_method columns from deposit, payment, and supplier_paper_purchase tables
-- ============================================
-- Date: 2025-12-19
-- Description: Removes payment_method columns from all tables since there is only one payment method
--              Affected tables: deposit, payment, supplier_paper_purchase
-- ============================================

USE printing_service_db;
GO

-- Step 1: Remove payment_method column from deposit table
ALTER TABLE deposit
DROP COLUMN payment_method;
GO

-- Step 2: Remove payment_method column from payment table
ALTER TABLE payment
DROP COLUMN payment_method;
GO

-- Step 3: Remove payment_method column from supplier_paper_purchase table
ALTER TABLE supplier_paper_purchase
DROP COLUMN payment_method;
GO

-- Step 4: Verify the changes
-- Uncomment the following to verify:
-- 
-- -- Check deposit table structure
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'deposit'
-- ORDER BY ORDINAL_POSITION;
-- GO
--
-- -- Check payment table structure
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'payment'
-- ORDER BY ORDINAL_POSITION;
-- GO
--
-- -- Check supplier_paper_purchase table structure
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'supplier_paper_purchase'
-- ORDER BY ORDINAL_POSITION;
-- GO

-- ============================================
-- Migration completed successfully
-- ============================================
-- Note: After running this migration, update your application code to remove
--       references to payment_method column in INSERT/UPDATE statements
-- ============================================

