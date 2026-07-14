# Retail Business Ontology & Data Strategy
### Forward Deploy Consulting · Architect Phase · May 2026 · Confidential

---

## Purpose

This document defines the **Retail Business Ontology** — the canonical set of entities, attributes, and relationships that must exist in a retailer's data layer for AI and agentic systems to function reliably.

It is the output of the **Architect phase** (Weeks 4–6) of the 4A engagement methodology. Everything in Phase 2 (the agentic layer) reasons over the entities defined here. If the ontology is wrong or incomplete, every agent built on top of it fails.

The ontology also serves as the diagnostic instrument. Every choke point identified in the friction analysis maps to a broken or missing relationship in this model. Fix the relationship → fix the choke point.

---

## How to Read This Document

```
Entity          → A real-world thing the business tracks and makes decisions about
Attribute       → A property of an entity that should have a single canonical value
Relationship    → A connection between two entities that enables a decision or signal flow
Source System   → Where the entity currently lives (the system of record)
Golden Record   → The canonical version of an entity, post-deduplication and resolution
Data Product    → A curated, governed output built from one or more entities for a consumer team
```

---

## Part 1 — Core Entities

### 1.1 Dimension Entities

Dimension entities are the "nouns" of the retail business. They don't change transaction to transaction — they define the universe within which transactions happen.

---

#### ENTITY: Customer

The individual human who purchases from the retailer. The most complex entity to resolve because they appear under multiple IDs across systems.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `master_id` | UUID | **Golden record key.** Resolved from all system IDs. Does not exist in most retailers today — must be built. | Identity Graph (to be built) |
| `pos_id` | string | POS-assigned ID at store level | POS / Store System |
| `ecom_id` | string | .com account ID | Shopify / Salesforce Commerce |
| `loyalty_id` | string | Loyalty program member number | Loyalty / CRM |
| `crm_id` | string | CRM contact ID | Salesforce / HubSpot / Klaviyo |
| `email` | string (hashed) | Primary deterministic match key | All systems |
| `phone` | string (hashed) | Secondary deterministic match key | Loyalty, .com |
| `first_seen_date` | date | Earliest transaction or event | Transaction log |
| `member_status` | enum | `member` / `guest` / `lapsed` | Loyalty |
| `clv_score` | float | Predicted lifetime value | Data Science model |
| `clv_tier` | enum | `platinum` / `gold` / `silver` / `guest` | Data Science model |
| `churn_risk_score` | float | 0–1 probability of lapsing | Data Science model |
| `preferred_channel` | enum | `store` / `ecom` / `omni` | Derived from transaction history |
| `primary_geography` | FK → Location | Home store cluster or shipping region | Loyalty / .com |
| `size_profile` | JSON | Size curve by category (e.g. tops: M, bottoms: 32x30) | Derived from purchase history |

**Golden Record Rule:** `master_id` is assigned by the Identity Graph service using deterministic matching (email → phone) then probabilistic fallback (device fingerprint, behaviour). This ID is the join key for every downstream model. It must be owned by a neutral Data Product function — not Marketing, not Planning.

**Choke points resolved:** CP1 (Identity Fragmentation), CP10 (Guest Blind Spot)

---

#### ENTITY: Product

A sellable item in the retailer's assortment. Exists at multiple levels of granularity — understanding which level is required for which decision is critical.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `style_id` | string | **Style-level key.** A design concept (e.g. "Men's Merino Crew"). Used in Line Plan, PLM. | PLM |
| `sku_id` | string | **SKU-level key.** Style + Color. The buying unit. | PLM / ERP |
| `upc` | string | **UPC-level key.** SKU + Size. The unit that is scanned. Must be unique and stable. | PLM → Item Master |
| `style_name` | string | Human-readable style name | PLM |
| `category` | string | e.g. Outerwear, Footwear, Tops | PLM / Merchandising |
| `sub_category` | string | e.g. Parkas, Sneakers, Crew Necks | PLM / Merchandising |
| `gender` | enum | Men / Women / Kids / Unisex | PLM |
| `colorway` | string | Color description | PLM |
| `size` | string | Size label (varies by category) | PLM |
| `season_code` | FK → Season | Which season this product was created for | PLM |
| `vendor_id` | FK → Vendor | Primary vendor | PLM / ERP |
| `target_fob_cost` | decimal | Planning's target FOB cost | Line Plan / PLM |
| `actual_fob_cost` | decimal | Negotiated and confirmed FOB cost | PLM / ERP |
| `landed_cost` | decimal | FOB + Freight + Duties + Agent Fees + DC Handling | **Calculated — currently in spreadsheets (CP-C3)** |
| `retail_price` | decimal | Initial retail price | Pricing Engine |
| `current_price` | decimal | Current selling price (post-markdowns) | POS / .com |
| `cost_margin_pct` | decimal | (Retail − Landed Cost) / Retail | Derived |
| `tariff_rate` | decimal | Applicable import duty rate | **Manual / not system-driven (CP-C4)** |
| `status` | enum | `planned` / `active` / `clearance` / `discontinued` | PLM |
| `sell_through_rate` | decimal | % of inventory sold at full price | Derived from Transaction |
| `return_rate` | decimal | % of units returned | Derived from Transaction |
| `avg_review_score` | decimal | Customer review rating | .com / Review platform |

**Golden Record Rule:** The Item Master owns the UPC. PLM creates the style and SKU. IT assigns UPC. Merchandising adds attributes. Finance adds cost. **No single owner today (CP-D1)** — the fix is to designate a Data Product owner who validates records before they fan out to WMS, POS, .com, and ERP.

**Choke points resolved:** CP-I2 (Item Master failure), CP-D1 (UPC governance), CP-C3 (landed cost), CP-C4 (tariff)

---

#### ENTITY: Location

Any physical or logical node where inventory sits, is received, or is sold.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `location_id` | UUID | **Golden record key.** Canonical location key. | To be standardised |
| `location_type` | enum | `store` / `dc` / `vendor_hub` / `virtual` | WMS / ERP |
| `location_name` | string | Human name | WMS |
| `store_number` | string | Store-specific ID | POS |
| `dc_code` | string | DC-specific ID | WMS |
| `region_canonical` | string | **Canonical region.** Single agreed definition. | **Does not exist today (CP-D2)** |
| `region_planning` | string | How Planning refers to this location's region | Planning system |
| `region_finance` | string | How Finance refers to this location's region | ERP / Finance |
| `region_wms` | string | How WMS refers to this location's region | WMS |
| `region_ecom` | string | How .com refers to this location's region | .com / OMS |
| `geography_lat` | decimal | Latitude (for CLV-by-geography allocation) | Store master |
| `geography_lon` | decimal | Longitude | Store master |
| `dc_capacity_units` | integer | Max units processable per day | WMS |
| `dc_current_load` | integer | Units currently queued | WMS — **not surfaced to Allocation today (CP-I6)** |
| `high_clv_cluster` | boolean | Whether this location serves a high-CLV customer cluster | Derived from Customer × Transaction |

**Golden Record Rule:** One canonical region definition per location, owned by Finance (since Finance is the system of record for geography in most retailers). All other systems maintain their local label but map to `region_canonical` via a lookup table. Region changes go through a change control process — all mapping tables updated before any reports run.

**Choke points resolved:** CP-D2 (Region mismatch), CP-I6 (DC blind spot)

---

#### ENTITY: Vendor

A manufacturer or supplier from whom the retailer buys product.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `vendor_id` | UUID | Golden record key | PLM / ERP |
| `vendor_name` | string | Legal name | ERP |
| `country_of_origin` | string | Manufacturing country | PLM / ERP |
| `agent_id` | FK → Agent | Sourcing agent, if used | PLM |
| `lead_time_days` | integer | Standard production lead time | PLM — often out of date |
| `default_port` | string | Primary shipping port | Logistics system |
| `preferred_freight_mode` | enum | `ocean` / `air` / `rail` | Logistics |
| `tariff_schedule` | JSON | HTS codes and applicable duty rates | **Manual today — updated reactively (CP-C4)** |
| `on_time_delivery_rate` | decimal | % of POs delivered on time | ERP — rarely tracked |
| `quality_reject_rate` | decimal | % of units rejected at DC receiving | WMS — rarely surfaced |

---

#### ENTITY: Season

A planning period. The unit around which Line Plan, buying, and assortment decisions are made.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `season_code` | string | e.g. `SP26`, `FA26` | PLM / Planning |
| `season_name` | string | e.g. Spring 2026 | PLM |
| `line_plan_open_date` | date | When Line Plan opens for this season | Planning |
| `plm_freeze_date` | date | When PLM attributes must be locked | PLM |
| `po_issue_date` | date | When POs must be issued to vendors | ERP |
| `first_receipt_date` | date | When first product is expected at DC | WMS |
| `floor_set_date` | date | When product hits stores | Operations |
| `markdown_start_date` | date | When clearance pricing begins | Pricing |
| `fiscal_quarter` | string | Corresponding FY quarter | Finance |

---

### 1.2 Transactional Entities

Transactional entities record events — they are time-stamped, immutable, and linked to dimension entities.

---

#### ENTITY: Transaction

Any customer-initiated event that involves product and money. Includes sales and returns.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `transaction_id` | UUID | Immutable event key | POS / OMS |
| `transaction_type` | enum | `sale` / `return` / `exchange` | POS / OMS |
| `transaction_timestamp` | timestamp | **When the event actually occurred.** | POS — arrives in Planning as **EOD batch (CP-I4)** |
| `master_id` | FK → Customer | Resolved customer. **Null for guests today (CP10).** | Identity Graph |
| `upc` | FK → Product | Item scanned or ordered | POS / OMS |
| `location_id` | FK → Location | Store or DC or .com | POS / WMS / OMS |
| `channel` | enum | `store` / `ecom` / `app` | POS / OMS |
| `units` | integer | Quantity | POS / OMS |
| `gross_revenue` | decimal | Units × full retail price | POS / OMS |
| `net_revenue` | decimal | After discounts / returns | POS / OMS |
| `promo_applied` | FK → Offer | Promotion used, if any | OMS / CRM |
| `return_reason_code` | FK → ReturnReason | **Structured code. Missing for most transactions today (CP4).** | Returns portal / OMS |
| `is_member_transaction` | boolean | Whether master_id was resolved | Derived |
| `attribution_method` | enum | `deterministic` / `probabilistic` / `unresolved` | Identity Graph |

**Choke points resolved:** CP-I4 (POS batch lag → fix: real-time event stream to Kafka), CP4 (Returns siloed), CP10 (Guest blind spot)

---

#### ENTITY: IntentSignal

A non-transactional customer behaviour on .com or app that signals future demand. **This entity does not exist in most retailers' connected data layers today — it lives only in Adobe Analytics / GA4 / Salesforce Commerce.**

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `signal_id` | UUID | Event key | .com analytics platform |
| `signal_timestamp` | timestamp | When the event occurred | .com |
| `master_id` | FK → Customer | Resolved customer (may be probabilistic) | Identity Graph |
| `signal_type` | enum | `search` / `pdp_view` / `wishlist_add` / `cart_add` / `cart_abandon` / `category_browse` | .com analytics |
| `upc` / `style_id` | FK → Product | Product browsed/searched (may be null for category-level search) | .com analytics |
| `search_query` | string | Raw search term (e.g. "heavyweight parka") | .com analytics |
| `location_id` | FK → Location | Derived from shipping address / IP / loyalty home store | Derived |
| `intent_weight` | float | Scored: cart_add=1.0, wishlist=0.8, pdp_view=0.4, search=0.2 | Derived |
| `session_id` | string | Browser session | .com analytics |

**Golden Record Rule:** This entity must be extracted from .com analytics via an event streaming pipeline (Kafka/Kinesis) into the central data lake. It must be aggregated into a **Forward Demand Signal** per (style_id, location_id, week) for consumption by the Demand Sensing Agent.

**Choke points resolved:** CP2 (Browse intent never leaves .com), CP-I7 (No forward demand signal into Planning)

---

#### ENTITY: PurchaseOrder

A formal commitment from the retailer to a vendor to produce and deliver product.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `po_id` | string | PO number | ERP / SAP |
| `season_code` | FK → Season | Season this PO serves | ERP |
| `vendor_id` | FK → Vendor | Vendor | ERP |
| `sku_id` | FK → Product | SKU ordered | ERP / PLM |
| `units_ordered` | integer | Committed quantity | ERP |
| `units_received` | integer | Actual received at DC | WMS |
| `target_fob_cost` | decimal | Cost at PO issuance | ERP |
| `actual_fob_cost` | decimal | Invoiced cost | ERP / Finance |
| `landed_cost_estimated` | decimal | **Calculated field — currently in spreadsheets (CP-C3)** | Spreadsheet |
| `landed_cost_actual` | decimal | Actual landed cost at DC receipt | Finance |
| `po_issue_date` | date | When PO was issued | ERP |
| `expected_ship_date` | date | Vendor's committed ship date | ERP |
| `actual_receipt_date` | date | Date product received at DC | WMS |
| `po_status` | enum | `draft` / `issued` / `in_production` / `shipped` / `received` / `closed` | ERP |
| `variance_pct` | decimal | (actual_landed_cost − landed_cost_estimated) / landed_cost_estimated | Derived |

---

#### ENTITY: Inventory

A snapshot of stock position for a product at a location at a point in time.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `snapshot_id` | UUID | Snapshot key | WMS / Inventory Hub |
| `upc` | FK → Product | Item | WMS |
| `location_id` | FK → Location | Where stock is | WMS |
| `snapshot_timestamp` | timestamp | When this count was taken | WMS — **often not synced to .com in real-time (CP-I3)** |
| `units_on_hand` | integer | Physical units at location | WMS |
| `units_on_order` | integer | Units on open POs not yet received | ERP |
| `units_in_transit` | integer | Units shipped from DC, not yet at store | WMS |
| `units_committed` | integer | Reserved for open customer orders | OMS |
| `units_available` | integer | on_hand − committed | Derived |
| `weeks_of_supply` | decimal | units_on_hand / avg_weekly_sales | Derived |
| `days_since_last_receipt` | integer | Aging metric | Derived |
| `is_stale` | boolean | True if snapshot is >1 hour old | Derived — **threshold to be defined in SLAs** |

**Choke points resolved:** CP-I3 (WMS not syncing to .com), CP-I6 (DC capacity blind spot)

---

#### ENTITY: Allocation

A planned transfer of inventory from a DC to a store or from a vendor to a DC.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `allocation_id` | UUID | Transfer order key | Allocation engine / WMS |
| `upc` | FK → Product | Item | Allocation |
| `from_location_id` | FK → Location | Origin | WMS |
| `to_location_id` | FK → Location | Destination | WMS |
| `units_allocated` | integer | Units to be moved | Allocation |
| `allocation_date` | date | When allocation was generated | Allocation |
| `expected_receipt_date` | date | When destination expects to receive | WMS |
| `allocation_status` | enum | `planned` / `in_wms` / `picked` / `shipped` / `received` | WMS |
| `allocation_trigger` | enum | `replenishment` / `initial_push` / `rebalance` / `markdown_pull` | Derived |
| `dc_load_at_creation` | integer | **DC queue at time of allocation — not captured today (CP-I6)** | WMS |

**Choke points resolved:** CP-I5 (Manual file handoff → automated system trigger), CP-I6 (DC blind spot)

---

#### ENTITY: ReturnReason

A structured classification of why a product was returned. **Currently exists only as free-text or is absent entirely in most retailers.**

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `return_reason_id` | UUID | Key | Returns portal / OMS |
| `transaction_id` | FK → Transaction | The return transaction | OMS |
| `upc` | FK → Product | Item returned | OMS |
| `master_id` | FK → Customer | Who returned it | Identity Graph |
| `reason_code` | enum | `sizing` / `quality` / `changed_mind` / `wrong_item` / `description_mismatch` / `gift` / `other` | Returns portal |
| `reason_detail` | string | Customer free-text | Returns portal |
| `reason_inferred` | string | NLP-classified reason from free-text | **To be derived by agent** |
| `size_feedback` | enum | `runs_small` / `runs_large` / `true_to_size` / `null` | Extracted from reason |
| `quality_issue_type` | string | e.g. "seam split", "color bleed" | Extracted from reason |

**Choke points resolved:** CP4 (Returns data siloed), CP9 (Post-purchase signal not in PLM)

---

#### ENTITY: Offer

A promotion, discount, or personalized offer extended to a customer.

| Attribute | Type | Description | Source System Today |
|---|---|---|---|
| `offer_id` | UUID | Offer key | CRM / Marketing platform |
| `offer_type` | enum | `pct_discount` / `dollar_off` / `bogo` / `loyalty_points` / `free_shipping` | CRM |
| `offer_trigger` | enum | `broadcast` / `segment` / `individual` / `markdown_pull` | CRM |
| `target_segment` | FK → Customer (segment) | Audience definition | CRM |
| `product_scope` | FK → Product (style/category) | What products the offer applies to | CRM |
| `discount_pct` | decimal | Discount depth | CRM |
| `send_date` | date | When offer was sent | CRM |
| `expiry_date` | date | When offer expires | CRM |
| `redemption_rate` | decimal | % of recipients who redeemed | CRM / OMS |
| `incremental_revenue` | decimal | Lift over control group | Data Science — **rarely measured today** |
| `is_margin_positive` | boolean | Whether the offer was margin-accretive | Finance / Data Science |
| `inventory_trigger` | boolean | True if triggered by aging stock (CP-I — Inventory Aging) | Allocation / Inventory Hub |

**Choke points resolved:** CP6 (Offer Irrelevance), CP-I: Inventory Aging → Marketing signal

---

### 1.3 Signal & Output Entities

These entities are **produced by AI/Data Science** and must flow back into operational decision-making. Today they stay locked in the analytics stack.

---

#### ENTITY: DemandForecast

| Attribute | Type | Description |
|---|---|---|
| `forecast_id` | UUID | Key |
| `sku_id` | FK → Product | SKU being forecast |
| `location_id` | FK → Location | Store or region |
| `week` | date | Forecast week |
| `units_historical` | integer | Baseline from sales history |
| `units_intent_adjusted` | integer | Adjusted using IntentSignal forward demand |
| `units_replacement_adjusted` | integer | Adjusted using replacement cycle model |
| `units_final` | integer | Final forecast consumed by Planning |
| `confidence_score` | float | Model confidence |
| `forecast_source` | enum | `statistical` / `ml_blended` / `agent_override` |

**Choke points resolved:** CP-I7 (No forward demand signal into Planning), CP8 (Data Science output stays in marketing)

---

#### ENTITY: DataScienceOutput

The structured output of Data Science models, formatted for consumption by Planning and Allocation — not just Marketing.

| Attribute | Type | Description |
|---|---|---|
| `output_id` | UUID | Key |
| `master_id` | FK → Customer | Customer this output applies to |
| `output_type` | enum | `clv_score` / `churn_risk` / `replacement_trigger` / `next_best_offer` / `category_affinity` |
| `output_value` | float | Score or probability |
| `output_label` | string | Human-readable (e.g. "high churn risk") |
| `valid_from` | date | When this score is current from |
| `valid_to` | date | When this score expires |
| `routed_to` | enum | `marketing` / `planning` / `allocation` / `all` | **Today always `marketing` (CP8)** |
| `acted_on` | boolean | Whether any system consumed and acted on this output |

---

## Part 2 — Relationships Between Entities

The choke points are, at their core, **missing or broken relationships** between entities. This table maps the critical joins.

| Relationship | From Entity | To Entity | Join Key | Status Today | Choke Point |
|---|---|---|---|---|---|
| Customer resolution | POS/ecom/loyalty records | `Customer.master_id` | email → phone → probabilistic | **Missing** | CP1 |
| Intent → Product | `IntentSignal` | `Product.style_id` | search query NLP / UPC | **Missing pipeline** | CP2, CP-I7 |
| Intent → Location | `IntentSignal` | `Location.location_id` | shipping zip / loyalty home store | **Missing** | CP2 |
| Transaction → Customer | `Transaction` | `Customer.master_id` | Identity Graph join | **Partial — guests unresolved** | CP10 |
| Transaction → ReturnReason | `Transaction` | `ReturnReason` | transaction_id | **Free-text only / missing** | CP4, CP9 |
| Inventory → .com availability | `Inventory.units_available` | .com display layer | UPC → real-time sync | **Batch, not real-time** | CP-I3 |
| POS → Planning (real-time) | `Transaction.timestamp` | Planning forecast input | SKU + location + timestamp | **EOD batch only** | CP-I4 |
| Allocation → DC load check | `Allocation` | `Location.dc_current_load` | location_id | **Not checked** | CP-I6 |
| DataScienceOutput → Planning | `DataScienceOutput` | `DemandForecast` | master_id → segment → SKU affinity | **Does not exist** | CP8 |
| DataScienceOutput → Allocation | `DataScienceOutput.clv_score` | `Allocation.to_location_id` | CLV by geography | **Does not exist** | CP8 |
| ReturnReason → PLM | `ReturnReason` | `Product.style_id` (PLM feedback) | UPC → SKU → style | **Does not exist** | CP9 |
| Location regions | `Location.region_*` | `Location.region_canonical` | lookup table | **No canonical def** | CP-D2 |
| Tariff → PO cost | `Vendor.tariff_schedule` | `PurchaseOrder.landed_cost_estimated` | HTS code + origin country | **Manual / spreadsheet** | CP-C4 |
| Offer → Inventory trigger | `Inventory` (aging stock) | `Offer` (markdown activation) | UPC + location + WOS threshold | **Manual / absent** | CP-I / CP6 |

---

## Part 3 — Source System Map & Golden Record Ownership

| Entity | Primary Source System | Secondary Sources | Golden Record Owner | Today's Problem |
|---|---|---|---|---|
| Customer | Loyalty / CRM | POS, .com, OMS | Data Product (neutral) | 3+ IDs per person, never resolved |
| Product (Style/SKU) | PLM | ERP, Planning | PLM team | PLM creates, multiple teams modify, no gate |
| Product (UPC/Item Master) | Item Master | PLM, WMS, POS, .com, ERP | Data Product (neutral) | No single owner, no validation gate |
| Location | WMS | ERP, Planning, .com | Finance | 4 different region definitions |
| Vendor | ERP / PLM | Logistics | Procurement | Tariff schedules not maintained |
| Season | Planning | PLM, Finance | Planning | Calendar diverges between PLM and ERP |
| Transaction | POS / OMS | Finance | Finance | Arrives in Planning as EOD batch |
| IntentSignal | .com analytics (Adobe/GA4) | — | Data Product | Does not reach Planning or Inventory |
| PurchaseOrder | ERP | PLM, Logistics | Finance | Landed cost calculated outside ERP |
| Inventory | WMS | OMS | Supply Chain / Inventory Hub | Not real-time to .com |
| Allocation | Allocation engine | WMS | Supply Chain | Manual file handoff to WMS |
| ReturnReason | Returns portal / OMS | — | Merchandising | Free-text, unstructured, never fed back |
| Offer | CRM / Marketing platform | OMS | Marketing | Not triggered by inventory or CLV |
| DemandForecast | Planning system | Data Science | Planning | Intent and DS signals not incorporated |
| DataScienceOutput | Data Science platform | — | Data Science | Routed only to Marketing |

---

## Part 4 — Data Products

A **Data Product** is a curated, governed, SLA-backed dataset built from one or more entities for a specific consuming team. This is the interface between the raw data layer and the decision-makers.

| Data Product | Consuming Team | Key Entities | Update Frequency | SLA | Unlocks |
|---|---|---|---|---|---|
| **Master Customer Profile** | All teams | Customer + Transaction + IntentSignal + DataScienceOutput | Near real-time (1hr lag max) | match_rate >80%, completeness >90% | CP1, CP10, CP8 |
| **Forward Demand Signal** | Planning, Allocation | IntentSignal + DemandForecast | Daily (rolling 8-week forward) | lag <24hr, coverage >70% of active SKUs | CP2, CP-I7, CP8 |
| **Member Sales View** | Planning | Transaction + Customer | Near real-time (1hr lag max) | attribution >75% of transactions | CP-I4, CP10 |
| **Inventory Position** | .com, OMS, Allocation | Inventory | Real-time (target <15min lag) | freshness SLA: stale flag triggers alert | CP-I3 |
| **CLV by Geography** | Allocation | Customer + Location + DataScienceOutput | Weekly refresh | CLV coverage >80% of active customers | Node 2 (connected loops) |
| **Aging Inventory Signal** | Marketing / CRM | Inventory + Offer | Daily | WOS threshold breach triggers within 24hr | Node 3 (connected loops) |
| **Returns Intelligence** | Merchandising, PLM | ReturnReason + Transaction + Product | Weekly aggregate | structured_reason_rate 100%, delay <7 days | CP4, CP9 |
| **Post-Purchase Feedback** | PLM, Line Plan | ReturnReason + Transaction + Product.sell_through + review scores | End of season + rolling | Delivered to merchant inbox at PLM cycle open | CP9, Node 4 |
| **Landed Cost Calculator** | Planning, Finance | PurchaseOrder + Vendor.tariff_schedule + Logistics rates | On PO creation + real-time on tariff change | variance_alert within 24hr of tariff change | CP-C3, CP-C4 |
| **Promo Effectiveness** | Marketing, Finance | Offer + Transaction + Customer | Post-campaign (T+7 days) | incremental_revenue calc for every offer | CP6 |

---

## Part 5 — Governance Layer

### 5.1 Canonical Definitions

These definitions must be agreed across teams before any model is built. Disagreement on definitions is the most common reason ontology work fails.

| Term | Canonical Definition | Common Variants to Retire |
|---|---|---|
| **Active Member** | A loyalty member who has made ≥1 purchase in the last 12 months | "Loyalty member", "enrolled member", varies by team |
| **A Sale** | A completed transaction where payment was captured and product shipped/handed over | "Order", "booking", "conversion" — these all mean different things |
| **Member Purchase** | A transaction where master_id was resolved (deterministic OR probabilistic) | "Loyalty purchase" — excludes probabilistic matches |
| **Return** | A transaction where a previously sold unit came back and was credited | "Refund", "reversal", "chargeback" — each handled differently |
| **Return Reason** | A structured reason code (not free text) attached to a return transaction | Free-text entry — must be deprecated |
| **Landed Cost** | FOB + Freight + Duties + Agent Fees + DC Handling. Calculated in-system, not in spreadsheet. | "Cost", "COGS" — use landed_cost consistently |
| **Full Price Sale** | A transaction where current_price = retail_price (no markdown applied) | "Regular price", "non-promo" |
| **Sell-Through Rate** | Units sold at full price / Total units received, by style, at end of season | % sold (includes markdown) — must specify |
| **CLV** | Predicted 12-month net revenue from a customer, calculated by Data Science model | "Customer value", "LTV", "member value" |
| **Region** | `region_canonical` — the Finance-owned definition. All other region labels are aliases. | Planning "East", WMS "DC-Northeast", .com "US-1" |

### 5.2 Data Quality SLAs

| Pipeline / Entity | Metric | Target | Alert Threshold |
|---|---|---|---|
| Identity Graph | match_rate (transactions resolved to master_id) | >80% | <70% triggers alert |
| Identity Graph | guest_resolution_rate (probabilistic matches) | >50% | <40% triggers alert |
| IntentSignal pipeline | lag (event time → data lake) | <1 hour | >2 hours triggers alert |
| Member Sales attribution | attribution_rate | >75% | <65% triggers alert |
| Inventory position | freshness (time since last WMS sync) | <15 minutes | >1 hour triggers alert |
| ReturnReason | structured_reason_code_rate | 100% | <95% triggers alert |
| Item Master | duplicate_upc_rate | 0% | Any duplicate triggers alert |
| Tariff schedule | days_since_last_update | <30 days | >60 days triggers alert |
| Demand Forecast | forward_coverage (% of active SKUs with a forward signal) | >70% | <50% triggers alert |

### 5.3 Ownership RACI

| Entity / Data Product | Accountable (A) | Responsible (R) | Consulted (C) | Informed (I) |
|---|---|---|---|---|
| Customer master_id / Identity Graph | Data Product Lead | Data Engineering | Marketing, IT | Planning, Finance |
| Item Master / UPC | Data Product Lead | PLM team + IT | Merchandising, Finance, WMS | All downstream systems |
| region_canonical | Finance | Data Engineering | Planning, WMS, IT | All reporting teams |
| IntentSignal pipeline | Data Product Lead | Data Engineering | .com team, Marketing | Planning, Allocation |
| Landed Cost formula | Finance | Data Engineering | Logistics, Procurement | Planning |
| Tariff schedule | Procurement / Finance | Procurement (input), Data Eng (update) | Logistics | Planning |
| DemandForecast | Planning | Planning + Data Science | Allocation, Finance | Merchandising |
| DataScienceOutput routing | Data Science | Data Science + Data Engineering | Marketing, Planning | Allocation |

### 5.4 Change Control Process

Any change to a source system that affects a golden record must follow this process:

```
1. Source system team notifies Data Product Lead ≥2 sprint cycles before change goes live
2. Data Engineering assesses impact on downstream pipelines
3. Mapping tables and transformation logic updated in staging
4. Data quality checks run against staging environment
5. Change promoted to production only after quality gates pass
6. Post-change monitoring for 2 weeks: all SLA metrics watched daily
```

**The Nike example applied:** Nike maintained two region tables and a mapping table between them. This should be the minimum bar — a `region_map` table that translates every system-specific region label to `region_canonical`. When leadership redraws regions, only the `region_map` is updated. All downstream reports automatically correct.

---

## Part 6 — Ontology → Choke Point Resolution Map

| Choke Point | Broken/Missing in Ontology | Fix | Phase |
|---|---|---|---|
| CP1 — Identity Fragmentation | `Customer.master_id` does not exist | Build Identity Graph; assign master_id as universal join key | Phase 1 |
| CP2 — Browse Intent Siloed | `IntentSignal` entity not in connected data layer | Event streaming pipeline .com → data lake; create IntentSignal table | Phase 1 |
| CP4 — Returns Data Siloed | `ReturnReason.reason_code` is free-text or absent | Structured reason code taxonomy + NLP classification; join to PLM feedback | Phase 1 |
| CP6 — Offer Irrelevance | `Offer.inventory_trigger` and `Offer.target_segment` not CLV-based | Wire Inventory aging signal → Offer trigger; use CLV segments in targeting | Phase 2 |
| CP8 — DS Output in Marketing Only | `DataScienceOutput.routed_to` = marketing only | Route DS outputs to Planning and Allocation data products | Phase 2 |
| CP9 — Post-purchase not in PLM | `ReturnReason` → `Product` relationship missing | Build Returns Intelligence data product; deliver to PLM at season open | Phase 2 |
| CP10 — Guest Blind Spot | `Transaction.master_id` = null for guests | Probabilistic resolution in Identity Graph; guest_resolution_rate SLA | Phase 1 |
| CP-I2 — Item Master failure | `Product.upc` has no single owner or validation gate | Assign Data Product owner; build validation gate before fan-out | Phase 1 |
| CP-I3 — WMS not real-time to .com | `Inventory.snapshot_timestamp` staleness | Real-time WMS → Inventory Hub sync; freshness SLA <15min | Phase 1 |
| CP-I4 — POS batch lag | `Transaction.transaction_timestamp` arrives EOD | POS event stream → Kafka → Planning real-time feed | Phase 1 |
| CP-I5 — Manual allocation handoff | `Allocation` → WMS is a file upload | API-based allocation trigger; `allocation_status` tracked in system | Phase 1 |
| CP-I6 — DC capacity blind spot | `Location.dc_current_load` not surfaced to Allocation | WMS exposes dc_current_load via API; Allocation checks before firing | Phase 1 |
| CP-I7 — No forward demand signal | `DemandForecast.units_intent_adjusted` = null | IntentSignal aggregation into Forward Demand Signal data product | Phase 2 |
| CP-C3 — Landed cost in spreadsheets | `PurchaseOrder.landed_cost_estimated` calculated outside ERP | In-system landed cost calculator using Vendor.tariff_schedule + logistics rates | Phase 1 |
| CP-C4 — Tariff not real-time | `Vendor.tariff_schedule` manually updated | Tariff data feed → auto-update; `days_since_last_update` SLA | Phase 1 |
| CP-D1 — UPC governance | No validation gate on `Product.upc` | Governance process + automated duplicate check before fan-out | Phase 1 |
| CP-D2 — Region mismatch | `Location.region_canonical` does not exist | Create canonical region + mapping table; change control process | Phase 1 |

---

## Part 7 — What Gets Built When

### Phase 1 Ontology Work (Weeks 4–6, Architect Phase + early Phase 1)

Priority order based on dependency chains — later work builds on earlier:

1. **`Location.region_canonical` + region_map table** — affects every report and downstream join. Fix first.
2. **`Product.upc` governance gate** — Item Master fan-out is the single largest amplifier of bad data.
3. **`Customer.master_id` (Identity Graph)** — required for every downstream model. Nothing meaningful works without it.
4. **`Transaction` real-time stream** — POS events to Kafka → Planning. Kills CP-I4.
5. **`IntentSignal` pipeline** — .com events to data lake. Enables Forward Demand Signal.
6. **`Inventory` real-time sync** — WMS → Inventory Hub → .com. Kills CP-I3.
7. **`PurchaseOrder.landed_cost_estimated` in-system** — eliminates the spreadsheet. Kills CP-C3.
8. **`ReturnReason` structured codes** — taxonomy + NLP classification on free-text.
9. **`Vendor.tariff_schedule` live feed** — kills CP-C4.
10. **`Allocation` API trigger** — kills CP-I5 and enables CP-I6 check.

### Phase 2 Ontology Work (Weeks 7–12, Agentic Layer)

Once Phase 1 entities are clean and flowing:

1. **`DemandForecast` intent-adjusted** — Demand Sensing Agent consumes IntentSignal + replacement cycle model.
2. **`DataScienceOutput.routed_to`** — route DS outputs to Planning and Allocation, not just Marketing.
3. **`Offer.inventory_trigger`** — wire aging inventory → marketing activation.
4. **Post-Purchase Feedback data product** — ReturnReason + sell-through → PLM workflow at season open.
5. **CLV by Geography data product** — DataScienceOutput × Location → Allocation engine.

---

## Open Items / Next Session

- [ ] Agree canonical definitions with client stakeholders (Part 5.1) — requires cross-functional workshop
- [ ] Confirm which source systems are in scope (NetSuite vs SAP vs other)
- [ ] Confirm Data Product ownership model — does client have a Data Product function or does one need to be created?
- [ ] Size Identity Graph build — deterministic match rate estimate requires sample from POS + loyalty
- [ ] Map ontology entities to client's specific tech stack (replace generic system names with actual vendor names)
- [ ] Prioritise Phase 1 pipeline builds by revenue impact for this specific client
- [ ] Define agent interfaces — what does the Demand Sensing Agent query and what does it produce? (inputs/outputs from this ontology)

---

*Forward Deploy Consulting · Architect Phase · May 2026*
