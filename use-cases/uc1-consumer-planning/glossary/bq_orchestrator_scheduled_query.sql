-- =============================================================================
-- DEPRECATED — use Orchestrator Cloud Run agent (agents/orchestrator/) instead.
-- SQL fallback only. Production: POST /run on uc1-orchestrator service.
-- =============================================================================
-- UC1 OrchestratorAgent — SCHEDULED QUERY (not used in standard deployment)
-- Name: UC1 – orchestrator
-- Schedule: hourly, 5–10 min AFTER refresh signal_delta
-- Destination: None (script writes via INSERT)
-- Project: demandsensinglayer | Dataset: dsl_dataset
-- =============================================================================

DECLARE run_id STRING DEFAULT CONCAT(
  'run_', FORMAT_TIMESTAMP('%Y%m%d_%H%M', CURRENT_TIMESTAMP()), '_', SUBSTR(GENERATE_UUID(), 1, 8)
);
DECLARE started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP();
DECLARE gates_passed BOOL DEFAULT TRUE;
DECLARE last_completed TIMESTAMP;
DECLARE scope_json STRING;
DECLARE scope_count INT64;
DECLARE cs_hours INT64;
DECLARE df_hours INT64;
DECLARE mh_hours INT64;

SET cs_hours = (
  SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(last_updated_dt), HOUR)
  FROM `demandsensinglayer.dsl_dataset.clickstream_agg`
);
SET df_hours = (
  SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(last_updated_dt), HOUR)
  FROM `demandsensinglayer.dsl_dataset.demand_forecast_base`
);
SET mh_hours = (
  SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ds_model_refresh_dt), HOUR)
  FROM `demandsensinglayer.dsl_dataset.member_hub`
);

IF cs_hours > 2 OR df_hours > 2 OR mh_hours > 2 OR cs_hours IS NULL OR df_hours IS NULL THEN
  SET gates_passed = FALSE;
  INSERT INTO `demandsensinglayer.dsl_dataset.agent_run_history` (
    run_id, run_status, gates_passed, scope_json, agents_executed, started_at, completed_at
  )
  VALUES (
    run_id, 'skipped', FALSE, '[]', '["BQ","ORCH"]', started_at, CURRENT_TIMESTAMP()
  );

ELSE
  SET last_completed = (
    SELECT MAX(completed_at)
    FROM `demandsensinglayer.dsl_dataset.agent_run_history`
    WHERE run_status = 'completed'
  );

  CREATE TEMP TABLE scope_rows AS
  SELECT DISTINCT
    sd.product_cd,
    COALESCE(df.sku_id, CONCAT('SKU-', sd.product_cd)) AS sku_id,
    sd.region,
    COALESCE(sd.region_canonical, sd.region) AS region_canonical,
    sd.week
  FROM `demandsensinglayer.dsl_dataset.signal_delta` AS sd
  LEFT JOIN `demandsensinglayer.dsl_dataset.demand_forecast_base` AS df
    ON sd.product_cd = df.product_cd
   AND sd.region = df.region
   AND sd.week = df.week
  WHERE sd.detected_at > COALESCE(last_completed, TIMESTAMP('1970-01-01'));

  SET scope_count = (SELECT COUNT(*) FROM scope_rows);

  IF scope_count = 0 THEN
    INSERT INTO `demandsensinglayer.dsl_dataset.agent_run_history` (
      run_id, run_status, gates_passed, scope_json, agents_executed, started_at, completed_at
    )
    VALUES (
      run_id, 'skipped', TRUE, '[]', '["BQ","ORCH"]', started_at, CURRENT_TIMESTAMP()
    );

  ELSE
    SET scope_json = (
      SELECT TO_JSON_STRING(ARRAY(
        SELECT AS STRUCT product_cd, sku_id, region, region_canonical, week
        FROM scope_rows
      ))
    );

    INSERT INTO `demandsensinglayer.dsl_dataset.agent_run_history` (
      run_id, run_status, gates_passed, scope_json, agents_executed, started_at, completed_at
    )
    VALUES (
      run_id, 'completed', TRUE, scope_json, '["BQ","ORCH"]', started_at, CURRENT_TIMESTAMP()
    );
  END IF;
END IF;
