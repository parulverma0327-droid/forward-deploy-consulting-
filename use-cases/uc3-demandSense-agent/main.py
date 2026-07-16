from flask import Flask, jsonify
from google.cloud import bigquery
from datetime import datetime
import os

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def demand_sensing_agent():
    client = bigquery.Client()
    try:
        sql = """
            SELECT 
                f.forecast_id, f.product_cd, f.sku_id, f.region, f.week, f.week_start_dt,
                f.season_code, f.category, f.units_forecast,
                COALESCE(c.search_count, 0) as search_count,
                COALESCE(c.pdp_view_count, 0) as pdp_view_count,
                COALESCE(c.wishlist_add_count, 0) as wishlist_add_count,
                COALESCE(c.cart_add_count, 0) as cart_add_count,
                COALESCE(c.weighted_intent_score, 0) as weighted_intent_score
            FROM `demandsensinglayer.dsl_dataset.dsl_demandforecast_base` f
            LEFT JOIN `demandsensinglayer.dsl_dataset.dsl_clickstreamagg` c
                ON f.product_cd = c.product_cd AND f.week = c.week
        """
        df = client.query(sql).to_dataframe()

        if df.empty:
            return jsonify({"status": "warning", "message": "No data"})

        df['weighted_intent_score'] = df.apply(
            lambda row: row['weighted_intent_score'] if row['weighted_intent_score'] > 0 else
                        (row['search_count'] * 0.2 + row['pdp_view_count'] * 0.4 +
                         row['wishlist_add_count'] * 0.8 + row['cart_add_count'] * 1.0), axis=1)

        df['units_intent_lift'] = (df['weighted_intent_score'] * 0.019).round().astype(int)
        df['units_intent_adjusted'] = df['units_forecast'] + df['units_intent_lift']
        df['confidence_score'] = 1.0
        df['consumer_signals_applied'] = True
        df['run_type'] = 'Run2'
        df['etl_timestamp'] = datetime.utcnow()
        df['load_date'] = datetime.utcnow().date()

        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(
            df,
            "demandsensinglayer.dsl_dataset.demand_forecast_recommendation",
            job_config=job_config
        )
        job.result()

        return jsonify({
            "status": "success",
            "message": "Demand Sensing Run 2 completed successfully",
            "rows_processed": len(df)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
