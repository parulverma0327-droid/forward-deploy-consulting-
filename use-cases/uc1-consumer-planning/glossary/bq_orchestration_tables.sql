-- =============================================================================
-- UC1 Orchestration — signal_delta + agent_run_history + snapshot
-- =============================================================================
-- Project: demandsensinglayer
-- Dataset: dsl_dataset
--
-- Run after bq_demand_sensing_tables.sql (requires clickstream_agg, demand_forecast_base)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. signal_delta — written by ForecastSignalBQAgent
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `dsl_dataset.signal_delta` (
  signal_delta_id STRING NOT NULL,
  product_cd STRING NOT NULL,
  region STRING NOT NULL,
  region_canonical STRING,
  week STRING NOT NULL,
  delta_type STRING NOT NULL,
  delta_magnitude FLOAT64,
  source_table STRING NOT NULL,
  prior_value FLOAT64,
  current_value FLOAT64,
  detected_at TIMESTAMP NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. signal_delta_snapshot — prior metrics for delta detection (internal)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `dsl_dataset.signal_delta_snapshot` (
  product_cd STRING NOT NULL,
  region STRING NOT NULL,
  week STRING NOT NULL,
  weighted_intent_score FLOAT64,
  units_forecast FLOAT64,
  snapshot_at TIMESTAMP NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. agent_run_history — written by OrchestratorAgent
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `dsl_dataset.agent_run_history` (
  run_id STRING NOT NULL,
  run_status STRING NOT NULL,
  gates_passed BOOL NOT NULL,
  scope_json STRING,
  agents_executed STRING,
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP
);
