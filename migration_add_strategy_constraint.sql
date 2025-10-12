-- ============================================
-- Migration: Add Strategy Type Constraint
-- Purpose: Ensure only valid strategy types are allowed
-- Date: October 12, 2025
-- ============================================

BEGIN;

-- Add constraint to ensure only valid strategy types
ALTER TABLE strategy_filter_criteria 
ADD CONSTRAINT chk_trade_type 
CHECK (type_of_trade IN ('Poor Mans Covered Call', 'Poor Mans Covered Put'));

-- Verify constraint was added
SELECT 'Strategy type constraint added successfully!' AS status;

COMMIT;
