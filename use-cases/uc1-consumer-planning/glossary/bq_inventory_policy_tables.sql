-- =============================================================================
-- UC1/UC2 Inventory Policy — Location, Inventory Position, inventory_recommendation
-- =============================================================================
-- Project: demandsensinglayer
-- Dataset: dsl_dataset
--
-- Run after bq_orchestration_tables.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. location — store / DC master (UC2 hub, demo seed)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `dsl_dataset.location` (
  location_id STRING NOT NULL,
  location_type STRING NOT NULL,
  region_canonical STRING NOT NULL,
  parent_dc_id STRING,
  location_nm STRING,
  last_updated_dt TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 2. inventory_position — on-hand snapshot per sku × location
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `dsl_dataset.inventory_position` (
  location_id STRING NOT NULL,
  sku_id STRING NOT NULL,
  units_on_hand INT64,
  units_in_transit INT64,
  lead_time_days INT64,
  snapshot_dt TIMESTAMP NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. inventory_recommendation — written by InventoryPolicyAgent
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `dsl_dataset.inventory_recommendation` (
  inventory_rec_id STRING NOT NULL,
  run_id STRING NOT NULL,
  sku_id STRING NOT NULL,
  location_id STRING NOT NULL,
  safety_stock_units INT64,
  exception_priority_flag BOOL,
  reorder_qty INT64,
  policy_rule_version STRING,
  inputs_used STRING,
  last_updated_dt TIMESTAMP NOT NULL
);

-- -----------------------------------------------------------------------------
-- Demo seed — US-PNW: 2 stores + 1 DC (idempotent: delete + insert)
-- -----------------------------------------------------------------------------

DELETE FROM `dsl_dataset.location` WHERE location_id IN ('STORE-102', 'STORE-118', 'DC-PNW-01');

INSERT INTO `dsl_dataset.location` (
  location_id, location_type, region_canonical, parent_dc_id, location_nm, last_updated_dt
)
VALUES
  ('STORE-102', 'store', 'US-PNW', 'DC-PNW-01', 'Portland Flagship', CURRENT_TIMESTAMP()),
  ('STORE-118', 'store', 'US-PNW', 'DC-PNW-01', 'Seattle Downtown', CURRENT_TIMESTAMP()),
  ('DC-PNW-01', 'dc', 'US-PNW', NULL, 'PNW Distribution Center', CURRENT_TIMESTAMP());

-- Demo inventory for hero SKUs already in demand_forecast_base (US-PNW)
DELETE FROM `dsl_dataset.inventory_position`
WHERE location_id IN ('STORE-102', 'STORE-118', 'DC-PNW-01');

INSERT INTO `dsl_dataset.inventory_position` (
  location_id, sku_id, units_on_hand, units_in_transit, lead_time_days, snapshot_dt
)
SELECT
  loc.location_id,
  df.sku_id,
  CASE loc.location_type WHEN 'store' THEN 18 ELSE 240 END AS units_on_hand,
  CASE loc.location_type WHEN 'store' THEN 6 ELSE 0 END AS units_in_transit,
  CASE loc.location_type WHEN 'store' THEN 2 ELSE 5 END AS lead_time_days,
  CURRENT_TIMESTAMP() AS snapshot_dt
FROM `dsl_dataset.location` AS loc
CROSS JOIN (
  SELECT DISTINCT sku_id
  FROM `dsl_dataset.demand_forecast_base` AS df
  LEFT JOIN `dsl_dataset.geo_region` AS gr ON df.region = gr.enterprise_region
  WHERE gr.region_canonical = 'US-PNW'
    AND df.sku_id IS NOT NULL
  LIMIT 5
) AS df
WHERE loc.region_canonical = 'US-PNW';
