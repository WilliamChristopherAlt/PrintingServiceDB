-- ============================================
-- Delete all deposits and payments for leanhtuank16 account
-- ============================================
-- This script removes all financial transaction data (deposits, payments, and related ledger entries)
-- for the student account: leanhtuank16@siu.edu.vn
-- ============================================
-- Note: This script is for Azure SQL Database (no USE statement needed)
-- ============================================

-- Find the student_id for leanhtuank16@siu.edu.vn and perform all deletions in one batch
DECLARE @leanhtuan_student_id UNIQUEIDENTIFIER;
DECLARE @leanhtuan_email NVARCHAR(100) = 'leanhtuank16@siu.edu.vn';
DECLARE @deleted_ledger_count INT;
DECLARE @deleted_payment_count INT;
DECLARE @deleted_deposit_count INT;
DECLARE @remaining_deposits INT;
DECLARE @remaining_payments INT;
DECLARE @remaining_ledger INT;

-- Find student_id
SELECT @leanhtuan_student_id = s.student_id
FROM student s
INNER JOIN [user] u ON s.user_id = u.user_id
WHERE u.email = @leanhtuan_email;

IF @leanhtuan_student_id IS NULL
BEGIN
    PRINT 'ERROR: Student account not found for email: ' + @leanhtuan_email;
    RETURN;
END

PRINT 'Found student_id: ' + CAST(@leanhtuan_student_id AS VARCHAR(36));
PRINT 'Starting deletion of deposits and payments...';
PRINT '';

-- Step 1: Delete ledger entries related to deposits and payments for this student
-- (Ledger entries reference deposits/payments via source_table and source_id)
PRINT 'Step 1: Deleting ledger entries for deposits and payments...';

DELETE FROM student_wallet_ledger
WHERE student_id = @leanhtuan_student_id
  AND source_type IN ('DEPOSIT', 'PAYMENT')
  AND (
    -- Delete entries referencing deposits
    (source_type = 'DEPOSIT' AND source_table = 'deposit')
    OR
    -- Delete entries referencing payments
    (source_type = 'PAYMENT' AND source_table = 'payment')
  );

SET @deleted_ledger_count = @@ROWCOUNT;
PRINT '  Deleted ' + CAST(@deleted_ledger_count AS VARCHAR(10)) + ' ledger entries.';

-- Step 2: Delete payments for this student
-- Note: Payments reference print_job via job_id, but we're not deleting print_jobs
PRINT 'Step 2: Deleting payments...';

DELETE FROM payment
WHERE student_id = @leanhtuan_student_id;

SET @deleted_payment_count = @@ROWCOUNT;
PRINT '  Deleted ' + CAST(@deleted_payment_count AS VARCHAR(10)) + ' payment records.';

-- Step 3: Delete deposits for this student
PRINT 'Step 3: Deleting deposits...';

DELETE FROM deposit
WHERE student_id = @leanhtuan_student_id;

SET @deleted_deposit_count = @@ROWCOUNT;
PRINT '  Deleted ' + CAST(@deleted_deposit_count AS VARCHAR(10)) + ' deposit records.';

-- Verification: Check remaining records (using variables to avoid subquery in PRINT)
SELECT @remaining_deposits = COUNT(*) FROM deposit WHERE student_id = @leanhtuan_student_id;
SELECT @remaining_payments = COUNT(*) FROM payment WHERE student_id = @leanhtuan_student_id;
SELECT @remaining_ledger = COUNT(*) 
FROM student_wallet_ledger 
WHERE student_id = @leanhtuan_student_id 
  AND source_type IN ('DEPOSIT', 'PAYMENT');

PRINT '';
PRINT 'Verification:';
PRINT '  Remaining deposits: ' + CAST(@remaining_deposits AS VARCHAR(10));
PRINT '  Remaining payments: ' + CAST(@remaining_payments AS VARCHAR(10));
PRINT '  Remaining ledger entries (DEPOSIT/PAYMENT): ' + CAST(@remaining_ledger AS VARCHAR(10));

PRINT '';
PRINT 'Deletion complete!';
PRINT 'Note: Print jobs for this student remain intact (only deposits and payments were deleted).';

