-- Migration Script: Fix Vietnamese Text Encoding in system_configuration
-- =====================================================================
-- Issue: Vietnamese text in description column is corrupted when queried
-- Solution: Ensure proper collation and fix data with explicit Unicode
-- IMPORTANT: Run this script with UTF-8 encoding in your SQL client
-- =====================================================================

BEGIN TRANSACTION;

-- Step 0: Ensure column has proper Unicode collation
-- This ensures the column can store Vietnamese characters correctly
ALTER TABLE system_configuration
ALTER COLUMN description NVARCHAR(200) COLLATE SQL_Latin1_General_CP1_CI_AS;

ALTER TABLE system_configuration
ALTER COLUMN config_value NVARCHAR(200) COLLATE SQL_Latin1_General_CP1_CI_AS;

-- Method: Use UPDATE statements to fix encoding for existing records
-- This preserves foreign key relationships and fixes the encoding issue
UPDATE system_configuration 
SET description = CAST(N'Hệ số giá in 2 mặt (0.8 = giảm 20% so với 1 mặt)' AS NVARCHAR(200))
WHERE config_key = N'duplex_price_factor';

UPDATE system_configuration 
SET description = CAST(N'Thời gian hết hạn mã QR thanh toán (phút)' AS NVARCHAR(200))
WHERE config_key = N'qr_expiration_minutes';

UPDATE system_configuration 
SET description = CAST(N'Kích thước file tối đa được phép upload (MB)' AS NVARCHAR(200))
WHERE config_key = N'max_file_size_mb';

UPDATE system_configuration 
SET description = CAST(N'Số tiền nạp tối thiểu (VNĐ)' AS NVARCHAR(200))
WHERE config_key = N'min_deposit_amount';

UPDATE system_configuration 
SET description = CAST(N'Số tiền nạp tối đa mỗi lần (VNĐ)' AS NVARCHAR(200))
WHERE config_key = N'max_deposit_amount';

UPDATE system_configuration 
SET description = CAST(N'Ngưỡng số dư thấp để cảnh báo (VNĐ)' AS NVARCHAR(200))
WHERE config_key = N'low_balance_threshold';

UPDATE system_configuration 
SET description = CAST(N'Thời gian timeout lệnh in pending (phút)' AS NVARCHAR(200))
WHERE config_key = N'print_job_timeout_minutes';

UPDATE system_configuration 
SET description = CAST(N'Thời gian ước tính in mỗi trang (giây)' AS NVARCHAR(200))
WHERE config_key = N'page_printing_rate_seconds';

UPDATE system_configuration 
SET description = CAST(N'Ngày trong tháng phát bonus học kỳ tự động' AS NVARCHAR(200))
WHERE config_key = N'semester_bonus_distribution_day';

UPDATE system_configuration 
SET description = CAST(N'Thời gian hết hạn token reset mật khẩu (phút)' AS NVARCHAR(200))
WHERE config_key = N'password_reset_token_expiry_minutes';

UPDATE system_configuration 
SET description = CAST(N'Thời gian hết hạn refresh token (ngày)' AS NVARCHAR(200))
WHERE config_key = N'refresh_token_expiry_days';

-- If records don't exist, insert them (fallback)
IF NOT EXISTS (SELECT 1 FROM system_configuration WHERE config_key = N'duplex_price_factor')
BEGIN
    INSERT INTO system_configuration (config_id, config_key, config_value, description, updated_at) VALUES
    (CAST('DDD92F9A-8461-4318-AC64-40346847B5DD' AS UNIQUEIDENTIFIER), N'duplex_price_factor', N'0.8', CAST(N'Hệ số giá in 2 mặt (0.8 = giảm 20% so với 1 mặt)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('B816B439-7EF1-4E4F-BA3F-C4D45EEA0041' AS UNIQUEIDENTIFIER), N'qr_expiration_minutes', N'10', CAST(N'Thời gian hết hạn mã QR thanh toán (phút)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('ECFE0B6A-3C3D-45BE-8BFD-C2EDE3D9ED8D' AS UNIQUEIDENTIFIER), N'max_file_size_mb', N'50', CAST(N'Kích thước file tối đa được phép upload (MB)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('684319EE-3F69-47F1-B7FB-56ED39641FE9' AS UNIQUEIDENTIFIER), N'min_deposit_amount', N'10000', CAST(N'Số tiền nạp tối thiểu (VNĐ)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('C61A8B7D-09F9-4AC5-B5F6-B4FF2241A920' AS UNIQUEIDENTIFIER), N'max_deposit_amount', N'5000000', CAST(N'Số tiền nạp tối đa mỗi lần (VNĐ)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('C960963D-93D9-4398-8BDE-3FA59E10195A' AS UNIQUEIDENTIFIER), N'low_balance_threshold', N'5000', CAST(N'Ngưỡng số dư thấp để cảnh báo (VNĐ)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('1D679C8A-2260-431D-80F4-FB0CFC791337' AS UNIQUEIDENTIFIER), N'print_job_timeout_minutes', N'30', CAST(N'Thời gian timeout lệnh in pending (phút)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('9121A32C-27B9-40D2-9B47-B55B58E36D1A' AS UNIQUEIDENTIFIER), N'page_printing_rate_seconds', N'10', CAST(N'Thời gian ước tính in mỗi trang (giây)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('F5F5986C-7DD9-4B5A-B8AA-84F56BF5FE07' AS UNIQUEIDENTIFIER), N'semester_bonus_distribution_day', N'1', CAST(N'Ngày trong tháng phát bonus học kỳ tự động' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('EFB28CA8-52C0-46CC-8754-B051BAC7B419' AS UNIQUEIDENTIFIER), N'password_reset_token_expiry_minutes', N'30', CAST(N'Thời gian hết hạn token reset mật khẩu (phút)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME)),
    (CAST('AF952E88-498F-4FFE-A273-22243CC3A039' AS UNIQUEIDENTIFIER), N'refresh_token_expiry_days', N'7', CAST(N'Thời gian hết hạn refresh token (ngày)' AS NVARCHAR(200)), CAST('2025-12-19 00:36:07' AS DATETIME));
END

-- Step 3: Verify the data is correctly inserted
-- Run this query to confirm Vietnamese text displays correctly
SELECT 
    config_key,
    config_value,
    description,
    CASE 
        WHEN description LIKE N'%Hệ%' OR description LIKE N'%Thời%' OR description LIKE N'%Kích%' 
             OR description LIKE N'%Số%' OR description LIKE N'%Ngưỡng%' OR description LIKE N'%Ngày%'
        THEN 'OK - Vietnamese characters detected'
        ELSE 'WARNING - May have encoding issues'
    END AS encoding_check
FROM system_configuration
ORDER BY config_key;

-- Step 5: Detailed verification query
-- This should show all descriptions with proper Vietnamese characters
-- Note: Using DATALENGTH only to avoid TEXT/NVARCHAR compatibility issues
SELECT 
    config_id,
    config_key,
    config_value,
    description,
    DATALENGTH(description) / 2 AS description_char_count,
    DATALENGTH(description) AS description_bytes
FROM system_configuration
ORDER BY config_key;

-- Expected results:
-- All descriptions should show proper Vietnamese text:
-- - "Hệ số giá in 2 mặt..."
-- - "Thời gian hết hạn mã QR..."
-- - "Kích thước file tối đa..."
-- - "Số tiền nạp tối thiểu..."
-- - etc.

COMMIT TRANSACTION;

-- If verification fails, rollback:
-- ROLLBACK TRANSACTION;

