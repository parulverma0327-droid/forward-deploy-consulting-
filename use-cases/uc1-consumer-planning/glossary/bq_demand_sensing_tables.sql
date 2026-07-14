-- =============================================================================
-- UC1 Demand Sensing — BigQuery DDL + synthetic load
-- =============================================================================
-- Source: Business glossary-2.xlsx + Prasad clickstream pattern
--         (pdh_datahub_full_oracle_with_clickstream.sql)
--
-- Project: demandsensinglayer
-- Dataset: dsl_dataset
--
-- Prerequisites (already in BQ from Prasad):
--   • dsl_memberprofile, dsl_order
--   • product_global_line_plan, product_price, product_size_upc, product_region_season
--
-- Run order: execute top-to-bottom in BigQuery Studio.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Reference tables
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.retail_calendar` (
  week STRING NOT NULL,
  retail_year INT64,
  week_start_dt DATE NOT NULL,
  week_end_dt DATE NOT NULL,
  ly_week STRING,
  ly_week_start_dt DATE,
  ly_week_end_dt DATE,
  is_current_week_ind STRING,
  week_seq_nbr INT64,
  calendar_version STRING,
  effective_from_dt DATE,
  last_updated_dt TIMESTAMP
);

INSERT INTO `dsl_dataset.retail_calendar`
WITH weeks AS (
  SELECT
    week_start_dt,
    DATE_ADD(week_start_dt, INTERVAL 6 DAY) AS week_end_dt,
    DATE_SUB(week_start_dt, INTERVAL 364 DAY) AS ly_week_start_dt
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2025-10-06', DATE '2026-11-16', INTERVAL 7 DAY)) AS week_start_dt
)
SELECT
  FORMAT_DATE('%G-W%V', week_start_dt) AS week,
  EXTRACT(YEAR FROM week_start_dt) AS retail_year,
  week_start_dt,
  week_end_dt,
  FORMAT_DATE('%G-W%V', ly_week_start_dt) AS ly_week,
  ly_week_start_dt,
  DATE_ADD(ly_week_start_dt, INTERVAL 6 DAY) AS ly_week_end_dt,
  IF(week_start_dt <= CURRENT_DATE() AND week_end_dt >= CURRENT_DATE(), 'Y', 'N') AS is_current_week_ind,
  ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM week_start_dt) ORDER BY week_start_dt) AS week_seq_nbr,
  'FY26_v1' AS calendar_version,
  DATE '2026-01-01' AS effective_from_dt,
  CURRENT_TIMESTAMP() AS last_updated_dt
FROM weeks;


CREATE OR REPLACE TABLE `dsl_dataset.geo_region` (
  region_canonical STRING NOT NULL,
  region_display_nm STRING,
  client_region_cd STRING,
  source_system STRING,
  enterprise_cd STRING,
  enterprise_region STRING,
  country_cd STRING,
  state_province_cd STRING,
  timezone STRING,
  map_rule STRING,
  is_active_ind STRING,
  geo_version STRING,
  last_updated_dt TIMESTAMP
);

INSERT INTO `dsl_dataset.geo_region` VALUES
  ('US-PNW', 'Pacific Northwest', 'Pacific NW', 'OMS', 'NIKEUS', 'Pacific NW', 'US', 'OR', 'America/Los_Angeles', 'OMS|Pacific NW→US-PNW', 'Y', '2026Q2', CURRENT_TIMESTAMP()),
  ('US-WEST', 'West', 'West', 'OMS', 'NIKEUS', 'West', 'US', 'CA', 'America/Los_Angeles', 'OMS|West→US-WEST', 'Y', '2026Q2', CURRENT_TIMESTAMP()),
  ('US-MW', 'Midwest', 'Midwest', 'OMS', 'NIKEUS', 'Midwest', 'US', 'IL', 'America/Chicago', 'OMS|Midwest→US-MW', 'Y', '2026Q2', CURRENT_TIMESTAMP()),
  ('US-SOUTH', 'South', 'South', 'OMS', 'NIKEUS', 'South', 'US', 'TX', 'America/Chicago', 'OMS|South→US-SOUTH', 'Y', '2026Q2', CURRENT_TIMESTAMP()),
  ('US-NE', 'Northeast', 'Northeast', 'OMS', 'NIKEUS', 'Northeast', 'US', 'NY', 'America/New_York', 'OMS|Northeast→US-NE', 'Y', '2026Q2', CURRENT_TIMESTAMP());


CREATE OR REPLACE TABLE `dsl_dataset.promo_calendar` (
  promo_id STRING NOT NULL,
  week STRING NOT NULL,
  week_start_dt DATE,
  season_code STRING,
  category STRING,
  product_cd STRING,
  region_canonical STRING,
  promo_type STRING,
  promo_nm STRING,
  promo_start_dt DATE,
  promo_end_dt DATE,
  promo_factor FLOAT64,
  promo_factor_rule STRING,
  promo_calendar_version STRING,
  last_updated_dt TIMESTAMP
);

INSERT INTO `dsl_dataset.promo_calendar`
SELECT
  CONCAT('PROMO_FA26_W', CAST(week_seq_nbr AS STRING)) AS promo_id,
  week,
  week_start_dt,
  'FA26' AS season_code,
  'Footwear > Trail' AS category,
  CAST(NULL AS STRING) AS product_cd,
  'US-PNW' AS region_canonical,
  'BMSM' AS promo_type,
  'Trail Week BMSM' AS promo_nm,
  week_start_dt AS promo_start_dt,
  week_end_dt AS promo_end_dt,
  IF(week IN ('2026-W42', '2026-W43', '2026-W44'), 1.15, 1.0) AS promo_factor,
  'merchant_input' AS promo_factor_rule,
  'FA26_promo_v3' AS promo_calendar_version,
  CURRENT_TIMESTAMP() AS last_updated_dt
FROM `dsl_dataset.retail_calendar`
WHERE week BETWEEN '2026-W40' AND '2026-W48';


-- -----------------------------------------------------------------------------
-- 2. Member Hub (Gold) — built from dsl_memberprofile
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.member_hub` (
  member_id STRING NOT NULL,
  master_id STRING,
  as_of_dt DATE,
  preferred_retail_geo STRING,
  preferred_country STRING,
  territory STRING,
  region STRING,
  preferred_gender STRING,
  age_group STRING,
  registration_date DATE,
  registration_site_id STRING,
  rewards_program_enrolled_ind STRING,
  order_count_12m INT64,
  spend_12m_usd FLOAT64,
  units_12m INT64,
  aov_12m_usd FLOAT64,
  visit_count_12m INT64,
  last_purchase_dt DATE,
  membership_tier STRING,
  is_active_12m STRING,
  order_count_lifetime INT64,
  spend_lifetime_usd FLOAT64,
  first_purchase_dt DATE,
  tenure_days INT64,
  clv_score FLOAT64,
  clv_tier STRING,
  churn_risk_score FLOAT64,
  category_affinity_score FLOAT64,
  ds_model_refresh_dt TIMESTAMP
);

INSERT INTO `dsl_dataset.member_hub`
SELECT
  mp.member_id,
  CONCAT('mst_', SUBSTR(mp.member_id, 5)) AS master_id,
  CURRENT_DATE() AS as_of_dt,
  'NA' AS preferred_retail_geo,
  'USA' AS preferred_country,
  'US' AS territory,
  CASE MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 5)
    WHEN 0 THEN 'Pacific NW' WHEN 1 THEN 'West' WHEN 2 THEN 'Midwest' WHEN 3 THEN 'South' ELSE 'Northeast'
  END AS region,
  CASE MOD(CAST(SUBSTR(mp.member_id, -2) AS INT64), 2) WHEN 0 THEN 'MEN' ELSE 'WOMEN' END AS preferred_gender,
  CASE MOD(CAST(SUBSTR(mp.member_id, -2) AS INT64), 4)
    WHEN 0 THEN '18-24' WHEN 1 THEN '25-34' WHEN 2 THEN '35-44' ELSE '45-54'
  END AS age_group,
  mp.registration_date,
  mp.registration_site_id,
  mp.rewards_program_enrolled_ind,
  CAST(5 + MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 20) AS INT64) AS order_count_12m,
  ROUND(500 + MOD(CAST(SUBSTR(mp.member_id, -4) AS INT64), 5000), 2) AS spend_12m_usd,
  CAST(3 + MOD(CAST(SUBSTR(mp.member_id, -2) AS INT64), 30) AS INT64) AS units_12m,
  CAST(NULL AS FLOAT64) AS aov_12m_usd,
  CAST(10 + MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 80) AS INT64) AS visit_count_12m,
  DATE_SUB(CURRENT_DATE(), INTERVAL MOD(CAST(SUBSTR(mp.member_id, -2) AS INT64), 120) DAY) AS last_purchase_dt,
  CASE
    WHEN MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 10) >= 8 THEN 'High Value'
    WHEN MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 10) >= 5 THEN 'Growth Potential'
    WHEN MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 10) >= 2 THEN 'Scaled Development'
    ELSE 'Non Buyer'
  END AS membership_tier,
  'Y' AS is_active_12m,
  CAST(20 + MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 100) AS INT64) AS order_count_lifetime,
  ROUND(2000 + MOD(CAST(SUBSTR(mp.member_id, -4) AS INT64), 15000), 2) AS spend_lifetime_usd,
  DATE_ADD(mp.registration_date, INTERVAL 30 DAY) AS first_purchase_dt,
  DATE_DIFF(CURRENT_DATE(), mp.registration_date, DAY) AS tenure_days,
  ROUND(400 + MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 600), 2) AS clv_score,
  IF(MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 10) >= 7, 'High', IF(MOD(CAST(SUBSTR(mp.member_id, -3) AS INT64), 10) >= 4, 'Medium', 'Low')) AS clv_tier,
  ROUND(0.05 + MOD(CAST(SUBSTR(mp.member_id, -2) AS INT64), 40) / 100, 2) AS churn_risk_score,
  ROUND(0.3 + MOD(CAST(SUBSTR(mp.member_id, -2) AS INT64), 70) / 100, 2) AS category_affinity_score,
  CURRENT_TIMESTAMP() AS ds_model_refresh_dt
FROM `dsl_dataset.dsl_memberprofile` AS mp;

UPDATE `dsl_dataset.member_hub`
SET aov_12m_usd = ROUND(spend_12m_usd / NULLIF(order_count_12m, 0), 2)
WHERE TRUE;


-- -----------------------------------------------------------------------------
-- 3. Clickstream Base (Gold hub) — Prasad pattern, glossary column names
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.clickstream_base` (
  event_id STRING NOT NULL,
  event_timestamp TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  session_id STRING,
  visitor_id STRING,
  master_id STRING,
  login_status STRING,
  member_id STRING,
  event_type STRING,
  intent_weight FLOAT64,
  source_system STRING,
  source_event_nm STRING,
  channel STRING,
  device_type STRING,
  product_cd STRING,
  sku_id STRING,
  upc STRING,
  style_nm STRING,
  search_query STRING,
  category_path STRING,
  market_iso3_country_cd STRING,
  region STRING,
  geo_derived_from STRING,
  cart_abandon_ind INT64,
  abandon_reason_cd STRING,
  oos_ind INT64,
  size_unavailable_ind INT64,
  ingest_timestamp TIMESTAMP,
  event_lag_minutes INT64
);

INSERT INTO `dsl_dataset.clickstream_base`
WITH
  base AS (
    SELECT n FROM UNNEST(GENERATE_ARRAY(1, 10000)) AS n
  ),
  members AS (
    SELECT member_id, master_id FROM `dsl_dataset.member_hub`
  ),
  products AS (
    SELECT product_code AS product_cd, style_name AS style_nm
    FROM `dsl_dataset.product_global_line_plan`
    LIMIT 500
  ),
  seeded AS (
    SELECT
      n,
      (SELECT AS STRUCT m.member_id, m.master_id FROM members AS m ORDER BY RAND() LIMIT 1) AS mem,
      (SELECT AS STRUCT p.product_cd, p.style_nm FROM products AS p ORDER BY RAND() LIMIT 1) AS prod,
      CASE MOD(n, 6)
        WHEN 0 THEN 'search'
        WHEN 1 THEN 'pdp_view'
        WHEN 2 THEN 'wishlist_add'
        WHEN 3 THEN 'cart_add'
        WHEN 4 THEN 'cart_abandon'
        ELSE 'category_browse'
      END AS event_type,
      CASE MOD(n, 7)
        WHEN 0 THEN 'Pacific NW'
        WHEN 1 THEN 'West'
        WHEN 2 THEN 'Midwest'
        WHEN 3 THEN 'South'
        WHEN 4 THEN 'Northeast'
        WHEN 5 THEN 'EMEA'
        ELSE 'APAC'
      END AS region
    FROM base
  )
SELECT
  CONCAT('evt_', LPAD(CAST(n AS STRING), 8, '0')) AS event_id,
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL CAST(FLOOR(RAND() * 30 * 24 * 60) AS INT64) MINUTE) AS event_timestamp,
  DATE(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL CAST(FLOOR(RAND() * 30) AS INT64) DAY)) AS event_date,
  CONCAT('sess_', LPAD(CAST(MOD(n, 3000) AS STRING), 6, '0')) AS session_id,
  CONCAT('vid_', LPAD(CAST(MOD(n, 5000) AS STRING), 6, '0')) AS visitor_id,
  IF(RAND() < 0.55, mem.master_id, NULL) AS master_id,
  IF(RAND() < 0.55, 'logged_in', 'guest') AS login_status,
  IF(RAND() < 0.55, mem.member_id, NULL) AS member_id,
  event_type,
  CASE event_type
    WHEN 'search' THEN 0.2
    WHEN 'pdp_view' THEN 0.4
    WHEN 'wishlist_add' THEN 0.8
    WHEN 'cart_add' THEN 1.0
    WHEN 'category_browse' THEN 0.3
    ELSE 0.5
  END AS intent_weight,
  CASE MOD(n, 3) WHEN 0 THEN 'Adobe Analytics' WHEN 1 THEN 'GA4' ELSE 'SFCC' END AS source_system,
  CASE event_type
    WHEN 'search' THEN 'search'
    WHEN 'pdp_view' THEN 'productView'
    WHEN 'wishlist_add' THEN 'wishlistAdd'
    WHEN 'cart_add' THEN 'addToCart'
    WHEN 'category_browse' THEN 'categoryBrowse'
    ELSE 'cartAbandon'
  END AS source_event_nm,
  IF(RAND() < 0.7, 'web', 'mobile_app') AS channel,
  CASE MOD(n, 4) WHEN 0 THEN 'SMARTPHONE' WHEN 1 THEN 'DESKTOP' WHEN 2 THEN 'TABLET' ELSE 'OTHER' END AS device_type,
  prod.product_cd,
  CONCAT('SKU-', prod.product_cd) AS sku_id,
  LPAD(CAST(MOD(n, 99999999999) AS STRING), 11, '0') AS upc,
  prod.style_nm,
  IF(event_type = 'search',
     CASE MOD(n, 5)
       WHEN 0 THEN 'waterproof hiking boot' WHEN 1 THEN 'running shoes'
       WHEN 2 THEN 'hiking jacket' WHEN 3 THEN 'trail running' ELSE 'waterproof boots'
     END,
     NULL) AS search_query,
  IF(event_type = 'category_browse',
     CASE MOD(n, 4)
       WHEN 0 THEN 'Footwear > Hiking > Waterproof' WHEN 1 THEN 'Apparel > Jackets'
       WHEN 2 THEN 'Footwear > Running' ELSE 'Accessories > Socks'
     END,
     NULL) AS category_path,
  'USA' AS market_iso3_country_cd,
  region,
  CASE MOD(n, 3) WHEN 0 THEN 'ship_zip' WHEN 1 THEN 'loyalty_home_store' ELSE 'IP_geolocation' END AS geo_derived_from,
  IF(event_type = 'cart_abandon' OR (event_type = 'cart_add' AND RAND() < 0.15), 1, 0) AS cart_abandon_ind,
  IF(RAND() < 0.15,
     CASE MOD(n, 4) WHEN 0 THEN 'size_unavailable' WHEN 1 THEN 'price' WHEN 2 THEN 'shipping' ELSE 'unknown' END,
     NULL) AS abandon_reason_cd,
  IF(RAND() < 0.08, 1, 0) AS oos_ind,
  IF(RAND() < 0.06, 1, 0) AS size_unavailable_ind,
  CURRENT_TIMESTAMP() AS ingest_timestamp,
  CAST(FLOOR(RAND() * 120) AS INT64) AS event_lag_minutes
FROM seeded;


-- Boost hero SKU intent for demo (Targhee IV × Pacific NW × W42–48)
INSERT INTO `dsl_dataset.clickstream_base`
SELECT
  CONCAT('evt_hero_', LPAD(CAST(n AS STRING), 5, '0')),
  TIMESTAMP '2026-10-15 12:00:00',
  DATE '2026-10-15',
  CONCAT('sess_hero_', CAST(MOD(n, 200) AS STRING)),
  CONCAT('vid_hero_', CAST(MOD(n, 500) AS STRING)),
  mh.master_id,
  'logged_in',
  mh.member_id,
  IF(MOD(n, 3) = 0, 'cart_add', 'pdp_view'),
  IF(MOD(n, 3) = 0, 1.0, 0.4),
  'Adobe Analytics',
  IF(MOD(n, 3) = 0, 'addToCart', 'productView'),
  'web',
  'DESKTOP',
  p.product_code,
  CONCAT('SKU-', p.product_code),
  '019123456789',
  p.style_name,
  'waterproof hiking boot',
  'Footwear > Hiking > Waterproof',
  'USA',
  'Pacific NW',
  'loyalty_home_store',
  0,
  NULL,
  0,
  0,
  CURRENT_TIMESTAMP(),
  10
FROM UNNEST(GENERATE_ARRAY(1, 400)) AS n
CROSS JOIN (
  SELECT product_code, style_name
  FROM `dsl_dataset.product_global_line_plan`
  WHERE LOWER(style_name) LIKE '%targhee%'
  LIMIT 1
) AS p
CROSS JOIN (
  SELECT member_id, master_id FROM `dsl_dataset.member_hub` ORDER BY RAND() LIMIT 1
) AS mh;


-- -----------------------------------------------------------------------------
-- 4. Clickstream Agg (Gold hub) — Demand Sensing primary input
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.clickstream_agg` AS
WITH base AS (
  SELECT
    b.*,
    rc.week,
    rc.week_start_dt
  FROM `dsl_dataset.clickstream_base` AS b
  JOIN `dsl_dataset.retail_calendar` AS rc
    ON b.event_date BETWEEN rc.week_start_dt AND rc.week_end_dt
  WHERE b.product_cd IS NOT NULL
),
agg AS (
  SELECT
    product_cd,
    region,
    week,
    ANY_VALUE(week_start_dt) AS week_start_dt,
    COUNT(event_id) AS event_count,
    COUNT(DISTINCT session_id) AS session_count,
    COUNTIF(event_type = 'search') AS search_count,
    COUNTIF(event_type = 'pdp_view') AS pdp_view_count,
    COUNTIF(event_type = 'wishlist_add') AS wishlist_add_count,
    COUNTIF(event_type = 'cart_add') AS cart_add_count,
    SUM(intent_weight) AS weighted_intent_score,
    COUNT(DISTINCT IF(cart_abandon_ind = 1, session_id, NULL)) AS session_unconverted_cart_count,
    APPROX_TOP_COUNT(IF(event_type = 'search', search_query, NULL), 1)[SAFE_OFFSET(0)].value AS top_search_query,
    COUNTIF(login_status = 'logged_in') AS member_intent_count,
    COUNTIF(login_status = 'guest') AS guest_intent_count,
    COUNT(DISTINCT IF(login_status = 'logged_in', session_id, NULL)) AS logged_in_session_count,
    IF(SUM(intent_weight) > 0, 1, 0) AS active_sku_coverage_ind
  FROM base
  GROUP BY product_cd, region, week
)
SELECT
  a.*,
  prs.season_code,
  SAFE_DIVIDE(a.weighted_intent_score, MAX(a.weighted_intent_score) OVER (PARTITION BY a.region, a.week)) AS browse_score,
  CAST(NULL AS INT64) AS unmet_cart_add_count_7d,
  CAST(NULL AS FLOAT64) AS search_spike_pct,
  CURRENT_TIMESTAMP() AS last_updated_dt
FROM agg AS a
LEFT JOIN `dsl_dataset.product_region_season` AS prs
  ON a.product_cd = prs.product_code
 AND a.region = prs.region;


-- -----------------------------------------------------------------------------
-- 5. DemandForecast_Base (Run 1 / As-Is)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.demand_forecast_base` AS
WITH
  product_scope AS (
    SELECT DISTINCT
      prs.product_code AS product_cd,
      prs.region,
      prs.season_code,
      prs.product_name AS category
    FROM `dsl_dataset.product_region_season` AS prs
    WHERE prs.region IN ('Pacific NW', 'West', 'Midwest', 'South', 'Northeast')
  ),
  week_scope AS (
    SELECT week, week_start_dt, ly_week
    FROM `dsl_dataset.retail_calendar`
    WHERE week BETWEEN '2026-W40' AND '2026-W48'
  ),
  grid AS (
    SELECT p.product_cd, p.region, p.season_code, p.category, w.week, w.week_start_dt, w.ly_week
    FROM product_scope AS p
    CROSS JOIN week_scope AS w
  ),
  ly_sales AS (
    -- Synthetic LY units at grain. After order_line is stable, replace with:
    -- SUM(sale_qty) FROM order_line grouped by product_cd, enterprise_region, ly_week.
    SELECT
      g.product_cd,
      g.region,
      g.ly_week,
      CAST(GREATEST(1, 120 + MOD(ABS(FARM_FINGERPRINT(CONCAT(g.product_cd, g.region, g.ly_week))), 100)) AS INT64) AS ly_units
    FROM grid AS g
  )
SELECT
  GENERATE_UUID() AS forecast_id,
  g.product_cd,
  CONCAT('SKU-', g.product_cd) AS sku_id,
  g.region,
  g.week,
  g.week_start_dt,
  g.season_code,
  g.category,
  CAST(ROUND(COALESCE(ly.ly_units, 150 + MOD(ABS(FARM_FINGERPRINT(CONCAT(g.product_cd, g.region, g.week))), 120)) *
       COALESCE(p.promo_factor, 1.0)) AS INT64) AS units_forecast,
  COALESCE(ly.ly_units, 150 + MOD(ABS(FARM_FINGERPRINT(CONCAT(g.product_cd, g.region, g.week))), 120)) AS ly_same_week_sales,
  COALESCE(p.promo_factor, 1.0) AS promo_factor,
  'LY_x_promo' AS forecast_method,
  CAST(NULL AS INT64) AS actual_units_wtd,
  CAST(NULL AS INT64) AS planner_override_units,
  CURRENT_TIMESTAMP() AS last_updated_dt
FROM grid AS g
LEFT JOIN ly_sales AS ly
  ON g.product_cd = ly.product_cd
 AND g.region = ly.region
 AND g.ly_week = ly.ly_week
LEFT JOIN `dsl_dataset.promo_calendar` AS p
  ON g.week = p.week
 AND (p.product_cd = g.product_cd OR (p.product_cd IS NULL AND p.category = g.category))
 AND (p.region_canonical IS NULL OR p.region_canonical = 'US-PNW');


-- -----------------------------------------------------------------------------
-- 6. ConsumerAffinity_Consumer (Run 2 — simplified for demo)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.consumer_affinity_consumer` AS
SELECT
  GENERATE_UUID() AS affinity_id,
  CAST(NULL AS STRING) AS session_id,
  ca.product_cd,
  gr.region_canonical,
  ca.week,
  mh.membership_tier AS tier,
  ca.weighted_intent_score AS weighted_intent_raw,
  ca.browse_score,
  CAST(50 + MOD(ABS(FARM_FINGERPRINT(CONCAT(ca.product_cd, ca.region, ca.week, mh.membership_tier))), 200) AS INT64) AS tier_sale_qty,
  CAST(280 AS INT64) AS category_max_sales,
  SAFE_DIVIDE(
    CAST(50 + MOD(ABS(FARM_FINGERPRINT(CONCAT(ca.product_cd, ca.region, ca.week, mh.membership_tier))), 200) AS FLOAT64),
    280
  ) AS buy_score,
  ca.browse_score - SAFE_DIVIDE(
    CAST(50 + MOD(ABS(FARM_FINGERPRINT(CONCAT(ca.product_cd, ca.region, ca.week, mh.membership_tier))), 200) AS FLOAT64),
    280
  ) AS gap_score,
  mh.clv_tier,
  CAST(200 + MOD(ABS(FARM_FINGERPRINT(CONCAT(ca.product_cd, ca.region, ca.week))), 800) AS INT64) AS member_count,
  ca.guest_intent_count,
  ca.member_intent_count,
  SAFE_DIVIDE(ca.guest_intent_count, ca.member_intent_count + ca.guest_intent_count) AS guest_share_pct,
  CAST(NULL AS INT64) AS search_count_ly,
  CAST(NULL AS FLOAT64) AS search_spike_pct,
  ca.top_search_query,
  CAST(0 AS INT64) AS oos_days_count,
  ca.session_unconverted_cart_count AS cart_abandon_total,
  CAST(FLOOR(ca.session_unconverted_cart_count * 0.6) AS INT64) AS cart_abandon_size,
  SAFE_DIVIDE(FLOOR(ca.session_unconverted_cart_count * 0.6), NULLIF(ca.session_unconverted_cart_count, 0)) AS cart_abandon_size_pct,
  CAST(NULL AS DATE) AS last_purchase_dt,
  CAST(180 AS INT64) AS category_cadence_days,
  CAST(20 + MOD(ABS(FARM_FINGERPRINT(CONCAT(ca.product_cd, ca.region, ca.week))), 80) AS INT64) AS replacement_due_count,
  CAST(NULL AS STRING) AS insight_summary,
  CURRENT_TIMESTAMP() AS last_updated_dt
FROM `dsl_dataset.clickstream_agg` AS ca
JOIN `dsl_dataset.geo_region` AS gr
  ON ca.region = gr.enterprise_region
 AND gr.source_system = 'OMS'
CROSS JOIN (
  SELECT membership_tier, clv_tier
  FROM `dsl_dataset.member_hub`
  WHERE membership_tier = 'High Value'
  LIMIT 1
) AS mh
WHERE ca.week BETWEEN '2026-W42' AND '2026-W48';


-- -----------------------------------------------------------------------------
-- 7. DemandForecast_Consumer (Run 2 — Demand Sensing output table)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `dsl_dataset.demand_forecast_consumer` AS
WITH intent_factor AS (
  SELECT
    product_cd,
    region,
    SAFE_DIVIDE(
      AVG(CAST(units_forecast AS FLOAT64)),
      NULLIF(AVG(weighted_intent_score), 0)
    ) AS intent_to_units_factor
  FROM `dsl_dataset.demand_forecast_base` AS b
  JOIN `dsl_dataset.clickstream_agg` AS ca
    USING (product_cd, region)
  GROUP BY product_cd, region
),
affinity AS (
  SELECT
    product_cd,
    region_canonical,
    week,
    MAX(gap_score) AS gap_score,
    SUM(member_count) AS member_count,
    MAX(guest_share_pct) AS guest_share_pct
  FROM `dsl_dataset.consumer_affinity_consumer`
  GROUP BY product_cd, region_canonical, week
)
SELECT
  GENERATE_UUID() AS forecast_id,
  CAST(NULL AS STRING) AS planning_session_id,
  'run_enriched_001' AS run_id,
  b.product_cd,
  b.sku_id,
  gr.region_canonical,
  b.week,
  b.week_start_dt,
  b.season_code,
  b.category,
  b.ly_same_week_sales,
  b.promo_factor,
  b.units_forecast AS units_historical,
  ca.weighted_intent_score,
  COALESCE(f.intent_to_units_factor, 0.019) AS intent_to_units_factor,
  CAST(ROUND(ca.weighted_intent_score * COALESCE(f.intent_to_units_factor, 0.019)) AS INT64) AS intent_units_lift,
  af.gap_score,
  af.member_count,
  CAST(ROUND(COALESCE(af.gap_score, 0) * 0.05 * COALESCE(af.member_count, 0)) AS INT64) AS affinity_units_lift,
  CAST(20 + MOD(ABS(FARM_FINGERPRINT(CONCAT(b.product_cd, b.region, b.week))), 80) AS INT64) AS replacement_due_count,
  1.2 AS avg_repurchase_units,
  CAST(ROUND((20 + MOD(ABS(FARM_FINGERPRINT(CONCAT(b.product_cd, b.region, b.week))), 80)) * 1.2) AS INT64) AS replacement_units_lift,
  0.0 AS ds_score,
  0 AS ds_units_lift,
  CAST(
    b.units_forecast
    + ROUND(ca.weighted_intent_score * COALESCE(f.intent_to_units_factor, 0.019))
    + ROUND(COALESCE(af.gap_score, 0) * 0.05 * COALESCE(af.member_count, 0))
    + ROUND((20 + MOD(ABS(FARM_FINGERPRINT(CONCAT(b.product_cd, b.region, b.week))), 80)) * 1.2)
  AS INT64) AS units_intent_adjusted,
  CAST(
    ROUND(ca.weighted_intent_score * COALESCE(f.intent_to_units_factor, 0.019))
    + ROUND(COALESCE(af.gap_score, 0) * 0.05 * COALESCE(af.member_count, 0))
    + ROUND((20 + MOD(ABS(FARM_FINGERPRINT(CONCAT(b.product_cd, b.region, b.week))), 80)) * 1.2)
  AS INT64) AS delta_units,
  CAST(NULL AS INT64) AS units_override,
  CAST(NULL AS INT64) AS units_final,
  b.actual_units_wtd,
  LEAST(
    1.0,
    SAFE_DIVIDE(ca.weighted_intent_score, 1000)
    * (1 - COALESCE(af.guest_share_pct, 0.5))
  ) AS confidence_score,
  TRUE AS consumer_signals_applied,
  'ml_blended' AS forecast_source,
  CAST(NULL AS STRING) AS approved_by,
  CAST(NULL AS TIMESTAMP) AS approved_at,
  CURRENT_TIMESTAMP() AS last_updated_dt
FROM `dsl_dataset.demand_forecast_base` AS b
JOIN `dsl_dataset.geo_region` AS gr
  ON b.region = gr.enterprise_region
 AND gr.source_system = 'OMS'
LEFT JOIN `dsl_dataset.clickstream_agg` AS ca
  ON b.product_cd = ca.product_cd
 AND b.region = ca.region
 AND b.week = ca.week
LEFT JOIN intent_factor AS f
  ON b.product_cd = f.product_cd
 AND b.region = f.region
LEFT JOIN affinity AS af
  ON b.product_cd = af.product_cd
 AND gr.region_canonical = af.region_canonical
 AND b.week = af.week;


-- -----------------------------------------------------------------------------
-- 8. Verification
-- -----------------------------------------------------------------------------

SELECT 'retail_calendar' AS table_name, COUNT(*) AS row_count FROM `dsl_dataset.retail_calendar`
UNION ALL SELECT 'geo_region', COUNT(*) FROM `dsl_dataset.geo_region`
UNION ALL SELECT 'promo_calendar', COUNT(*) FROM `dsl_dataset.promo_calendar`
UNION ALL SELECT 'dsl_memberprofile', COUNT(*) FROM `dsl_dataset.dsl_memberprofile`
UNION ALL SELECT 'dsl_order', COUNT(*) FROM `dsl_dataset.dsl_order`
UNION ALL SELECT 'member_hub', COUNT(*) FROM `dsl_dataset.member_hub`
UNION ALL SELECT 'clickstream_base', COUNT(*) FROM `dsl_dataset.clickstream_base`
UNION ALL SELECT 'clickstream_agg', COUNT(*) FROM `dsl_dataset.clickstream_agg`
UNION ALL SELECT 'demand_forecast_base', COUNT(*) FROM `dsl_dataset.demand_forecast_base`
UNION ALL SELECT 'consumer_affinity_consumer', COUNT(*) FROM `dsl_dataset.consumer_affinity_consumer`
UNION ALL SELECT 'demand_forecast_consumer', COUNT(*) FROM `dsl_dataset.demand_forecast_consumer`;
