-- =============================================================================
-- UC1 ForecastSignalBQAgent — SCHEDULED QUERY
-- =============================================================================
-- Name: UC1 – refresh signal_delta
-- Schedule: hourly (e.g. :00)
-- Destination: None (script writes via INSERT)
-- Project: demandsensinglayer | Dataset: dsl_dataset
-- =============================================================================

DECLARE intent_threshold FLOAT64 DEFAULT 0.15;
DECLARE baseline_threshold FLOAT64 DEFAULT 0.10;
DECLARE now_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP();
DECLARE snapshot_count INT64;

SET snapshot_count = (
  SELECT COUNT(*) FROM `demandsensinglayer.dsl_dataset.signal_delta_snapshot`
);

CREATE TEMP TABLE current_metrics AS
SELECT
  cs.product_cd,
  cs.region,
  cs.week,
  COALESCE(cs.weighted_intent_score, 0) AS weighted_intent_score,
  COALESCE(df.units_forecast, 0) AS units_forecast,
  COALESCE(gr.region_canonical, cs.region) AS region_canonical
FROM `demandsensinglayer.dsl_dataset.clickstream_agg` AS cs
LEFT JOIN `demandsensinglayer.dsl_dataset.demand_forecast_base` AS df
  ON cs.product_cd = df.product_cd
 AND cs.region = df.region
 AND cs.week = df.week
LEFT JOIN `demandsensinglayer.dsl_dataset.geo_region` AS gr
  ON cs.region = gr.enterprise_region
 AND gr.source_system = 'OMS';

IF snapshot_count = 0 THEN
  INSERT INTO `demandsensinglayer.dsl_dataset.signal_delta_snapshot` (
    product_cd, region, week, weighted_intent_score, units_forecast, snapshot_at
  )
  SELECT
    product_cd, region, week, weighted_intent_score, units_forecast, now_ts
  FROM current_metrics;

ELSE
  INSERT INTO `demandsensinglayer.dsl_dataset.signal_delta` (
    signal_delta_id, product_cd, region, region_canonical, week,
    delta_type, delta_magnitude, source_table, prior_value, current_value, detected_at
  )
  SELECT
    GENERATE_UUID(),
    c.product_cd, c.region, c.region_canonical, c.week,
    IF(c.weighted_intent_score >= s.weighted_intent_score, 'intent_spike', 'intent_drop'),
    IF(
      s.weighted_intent_score = 0,
      IF(c.weighted_intent_score > 0, 1.0, 0.0),
      ABS(c.weighted_intent_score - s.weighted_intent_score) / ABS(s.weighted_intent_score)
    ),
    'clickstream_agg',
    s.weighted_intent_score,
    c.weighted_intent_score,
    now_ts
  FROM current_metrics AS c
  INNER JOIN `demandsensinglayer.dsl_dataset.signal_delta_snapshot` AS s
    ON c.product_cd = s.product_cd AND c.region = s.region AND c.week = s.week
  WHERE
    (s.weighted_intent_score = 0 AND c.weighted_intent_score > 0)
    OR (
      s.weighted_intent_score != 0
      AND ABS(c.weighted_intent_score - s.weighted_intent_score) / ABS(s.weighted_intent_score) >= intent_threshold
    );

  INSERT INTO `demandsensinglayer.dsl_dataset.signal_delta` (
    signal_delta_id, product_cd, region, region_canonical, week,
    delta_type, delta_magnitude, source_table, prior_value, current_value, detected_at
  )
  SELECT
    GENERATE_UUID(),
    c.product_cd, c.region, c.region_canonical, c.week,
    'baseline_shift',
    IF(
      s.units_forecast = 0,
      IF(c.units_forecast > 0, 1.0, 0.0),
      ABS(c.units_forecast - s.units_forecast) / ABS(s.units_forecast)
    ),
    'demand_forecast_base',
    s.units_forecast,
    c.units_forecast,
    now_ts
  FROM current_metrics AS c
  INNER JOIN `demandsensinglayer.dsl_dataset.signal_delta_snapshot` AS s
    ON c.product_cd = s.product_cd AND c.region = s.region AND c.week = s.week
  WHERE
    (s.units_forecast = 0 AND c.units_forecast > 0)
    OR (
      s.units_forecast != 0
      AND ABS(c.units_forecast - s.units_forecast) / ABS(s.units_forecast) >= baseline_threshold
    );

  TRUNCATE TABLE `demandsensinglayer.dsl_dataset.signal_delta_snapshot`;

  INSERT INTO `demandsensinglayer.dsl_dataset.signal_delta_snapshot` (
    product_cd, region, week, weighted_intent_score, units_forecast, snapshot_at
  )
  SELECT
    product_cd, region, week, weighted_intent_score, units_forecast, now_ts
  FROM current_metrics;

END IF;
