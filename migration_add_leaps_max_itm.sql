-- Migration: Add leaps_max_itm_percent field to strategy_filter_criteria table
-- Run this if you have an existing database without this field

-- Add the new column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategy_filter_criteria' 
        AND column_name = 'leaps_max_itm_percent'
    ) THEN
        ALTER TABLE strategy_filter_criteria 
        ADD COLUMN leaps_max_itm_percent DECIMAL(10,4) NOT NULL DEFAULT 50.0000;
        
        RAISE NOTICE 'Added leaps_max_itm_percent column';
    ELSE
        RAISE NOTICE 'Column leaps_max_itm_percent already exists';
    END IF;
END $$;

-- Update the check constraint to include the new field
ALTER TABLE strategy_filter_criteria 
DROP CONSTRAINT IF EXISTS chk_itm_percent;

ALTER TABLE strategy_filter_criteria 
ADD CONSTRAINT chk_itm_percent 
CHECK (leaps_min_itm_percent <= leaps_max_itm_percent);

-- Update existing records to have the new field set to 50% (default)
UPDATE strategy_filter_criteria 
SET leaps_max_itm_percent = 50.0000 
WHERE leaps_max_itm_percent IS NULL;

SELECT 'Migration completed successfully!' AS status;
