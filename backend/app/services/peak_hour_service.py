import pandas as pd
import psycopg2


def get_peak_hours():
    conn = psycopg2.connect(dbname="metroflow_db")

    query = """
        SELECT
            EXTRACT(HOUR FROM transit_timestamp)::int AS hour,
            AVG(ridership) AS avg_ridership
        FROM mta_hourly_ridership
        GROUP BY EXTRACT(HOUR FROM transit_timestamp)
        ORDER BY hour;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    peak_threshold = df["avg_ridership"].quantile(0.75)
    low_threshold = df["avg_ridership"].quantile(0.25)

    def classify(value):
        if value >= peak_threshold:
            return "peak"
        elif value <= low_threshold:
            return "low"
        return "normal"

    df["demand_level"] = df["avg_ridership"].apply(classify)

    return df.to_dict(orient="records")
