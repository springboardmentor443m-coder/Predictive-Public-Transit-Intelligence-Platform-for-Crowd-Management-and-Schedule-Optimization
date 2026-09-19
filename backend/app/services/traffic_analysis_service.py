import pandas as pd
import psycopg2


def get_traffic_analysis():
    conn = psycopg2.connect(dbname="metroflow_db")

    query = """
        SELECT
            line AS line,
            COUNT(*) AS records,
            SUM(entries) AS total_entries,
            SUM(exits) AS total_exits
        FROM nyc_subway_traffic
        GROUP BY line
        ORDER BY total_entries DESC;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["traffic_level"] = pd.qcut(
        df["total_entries"],
        q=3,
        labels=["low", "normal", "high"],
        duplicates="drop"
    )

    return df.to_dict(orient="records")
