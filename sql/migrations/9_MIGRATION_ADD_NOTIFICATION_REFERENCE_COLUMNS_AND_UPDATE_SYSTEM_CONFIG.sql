-- ============================================
-- Migration: Add reference columns to notification table and update system_configuration data
-- Date: 2025-01-XX
-- ============================================

-- ============================================
-- Part 1: Add reference columns to notification table
-- ============================================
-- Check if column exists before adding
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'notification' AND COLUMN_NAME = 'reference_id')
BEGIN
    ALTER TABLE notification ADD reference_id UNIQUEIDENTIFIER NULL;
    PRINT 'Added column: reference_id';
END
ELSE
BEGIN
    PRINT 'Column reference_id already exists';
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'notification' AND COLUMN_NAME = 'reference_type')
BEGIN
    ALTER TABLE notification ADD reference_type NVARCHAR(50) NULL;
    PRINT 'Added column: reference_type';
END
ELSE
BEGIN
    PRINT 'Column reference_type already exists';
END
GO

-- Create index for better query performance (optional)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_notification_reference' AND object_id = OBJECT_ID('notification'))
BEGIN
    CREATE INDEX idx_notification_reference ON notification(reference_id, reference_type) WHERE reference_id IS NOT NULL;
    PRINT 'Created index: idx_notification_reference';
END
ELSE
BEGIN
    PRINT 'Index idx_notification_reference already exists';
END
GO

-- ============================================
-- Part 2: Update system_configuration data
-- ============================================
-- Delete existing system_configuration data
DELETE FROM system_configuration;
PRINT 'Deleted existing system_configuration data';
GO

-- Insert new system_configuration data
INSERT INTO system_configuration (config_id, config_key, config_value, description, updated_at) VALUES
(NEWID(), 'duplex_price_factor', '0.8', N'Hệ số giá in 2 mặt (0.8 = giảm 20% so với 1 mặt)', GETDATE()),
(NEWID(), 'qr_expiration_minutes', '10', N'Thời gian hết hạn mã QR thanh toán (phút)', GETDATE()),
(NEWID(), 'max_file_size_mb', '50', N'Kích thước file tối đa được phép upload (MB)', GETDATE()),
(NEWID(), 'min_deposit_amount', '10000', N'Số tiền nạp tối thiểu (VNĐ)', GETDATE()),
(NEWID(), 'max_deposit_amount', '5000000', N'Số tiền nạp tối đa mỗi lần (VNĐ)', GETDATE()),
(NEWID(), 'low_balance_threshold', '5000', N'Ngưỡng số dư thấp để cảnh báo (VNĐ)', GETDATE()),
(NEWID(), 'print_job_timeout_minutes', '30', N'Thời gian timeout lệnh in pending (phút)', GETDATE()),
(NEWID(), 'page_printing_rate_seconds', '10', N'Thời gian ước tính in mỗi trang (giây)', GETDATE()),
(NEWID(), 'semester_bonus_distribution_day', '1', N'Ngày trong tháng phát bonus học kỳ tự động', GETDATE()),
(NEWID(), 'password_reset_token_expiry_minutes', '30', N'Thời gian hết hạn token reset mật khẩu (phút)', GETDATE()),
(NEWID(), 'refresh_token_expiry_days', '7', N'Thời gian hết hạn refresh token (ngày)', GETDATE());
PRINT 'Inserted new system_configuration data';
GO

PRINT 'Migration completed successfully!';
GO

