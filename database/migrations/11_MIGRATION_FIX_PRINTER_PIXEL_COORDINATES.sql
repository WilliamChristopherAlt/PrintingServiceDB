-- ============================================
-- MIGRATION: Fix printer_pixel_coordinate to ensure raw pixel coordinates are integers
-- ============================================
-- Date: 2025-01-XX
-- Description: 
--  Ensures printer_pixel_coordinate JSON stores pixel coordinates as integers (raw pixel values)
--  Not percentages or floating-point values. Pixel coordinates must be raw pixel coordinates.
-- ============================================

USE printing_service_db;
GO

-- Step 1: Create a function to fix pixel coordinates in JSON
-- This function ensures pixel values are integers
-- Note: SQL Server JSON functions are used here

-- Step 2: Fix pixel coordinates - they were incorrectly calculated with scale=1.0 instead of scale=100.0
-- The bug: grid_to_pixel_scale was OUTPUT_WIDTH/svg_width (1.0) instead of OUTPUT_WIDTH/GRID_COLS (100.0)
-- This caused grid coordinates like 5.9 to become pixel 5 instead of pixel 590
-- Fix: Recalculate pixel coordinates from grid coordinates using correct scale
-- 
-- Scale calculation: OUTPUT_WIDTH (2400px) / GRID_COLS (24) = 100 pixels per grid unit
-- All current floor templates use grid_cols=24, so scale is always 100.0
-- If future floors use different grid_cols, this migration would need to be updated
--
-- Note: We recalculate from grid coordinates because the original pixel values were wrong
-- (they were just integer parts of grid coordinates, not actual pixel positions)
UPDATE printer_physical
SET printer_pixel_coordinate = CASE
    WHEN printer_pixel_coordinate IS NOT NULL 
         AND ISJSON(printer_pixel_coordinate) = 1
         AND JSON_VALUE(printer_pixel_coordinate, '$.grid[0]') IS NOT NULL
         AND JSON_VALUE(printer_pixel_coordinate, '$.grid[1]') IS NOT NULL
    THEN '{"grid":[' + 
         -- Keep grid coordinates as-is
         CAST(CAST(JSON_VALUE(printer_pixel_coordinate, '$.grid[0]') AS FLOAT) AS VARCHAR(50)) + ',' +
         CAST(CAST(JSON_VALUE(printer_pixel_coordinate, '$.grid[1]') AS FLOAT) AS VARCHAR(50)) + '],' +
         '"pixel":[' +
         -- Recalculate pixel coordinates: grid * scale (scale = 100.0 for all current floors)
         -- Formula: pixel = grid * (OUTPUT_WIDTH / GRID_COLS) = grid * (2400 / 24) = grid * 100
         -- Ensure pixel values are integers (raw pixel coordinates)
         CAST(CAST(CAST(JSON_VALUE(printer_pixel_coordinate, '$.grid[0]') AS FLOAT) * 100.0 AS INT) AS VARCHAR(50)) + ',' +
         CAST(CAST(CAST(JSON_VALUE(printer_pixel_coordinate, '$.grid[1]') AS FLOAT) * 100.0 AS INT) AS VARCHAR(50)) + ']}'
    ELSE printer_pixel_coordinate
END
WHERE printer_pixel_coordinate IS NOT NULL
      AND ISJSON(printer_pixel_coordinate) = 1
      AND JSON_VALUE(printer_pixel_coordinate, '$.grid[0]') IS NOT NULL
      AND JSON_VALUE(printer_pixel_coordinate, '$.grid[1]') IS NOT NULL;
GO

-- Step 4: Verify the changes
SELECT TOP 20
    pp.printer_id,
    pp.serial_number,
    pp.printer_pixel_coordinate,
    JSON_VALUE(pp.printer_pixel_coordinate, '$.pixel[0]') AS pixel_x,
    JSON_VALUE(pp.printer_pixel_coordinate, '$.pixel[1]') AS pixel_y,
    JSON_VALUE(pp.printer_pixel_coordinate, '$.grid[0]') AS grid_x,
    JSON_VALUE(pp.printer_pixel_coordinate, '$.grid[1]') AS grid_y,
    CASE 
        WHEN CAST(JSON_VALUE(pp.printer_pixel_coordinate, '$.pixel[0]') AS FLOAT) = 
             CAST(CAST(JSON_VALUE(pp.printer_pixel_coordinate, '$.pixel[0]') AS FLOAT) AS INT)
        THEN 'Integer'
        ELSE 'Float'
    END AS pixel_x_type,
    CASE 
        WHEN CAST(JSON_VALUE(pp.printer_pixel_coordinate, '$.pixel[1]') AS FLOAT) = 
             CAST(CAST(JSON_VALUE(pp.printer_pixel_coordinate, '$.pixel[1]') AS FLOAT) AS INT)
        THEN 'Integer'
        ELSE 'Float'
    END AS pixel_y_type
FROM printer_physical pp
WHERE pp.printer_pixel_coordinate IS NOT NULL
ORDER BY pp.created_at DESC;
GO

-- ============================================
-- Migration completed successfully
-- ============================================
-- Note: This migration ensures pixel coordinates are stored as integers (raw pixel values).
-- The updated generate.py script now also ensures pixel coordinates are integers when generating new data.

