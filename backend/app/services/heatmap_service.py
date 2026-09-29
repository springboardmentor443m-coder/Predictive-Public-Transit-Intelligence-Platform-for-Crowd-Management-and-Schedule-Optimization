import psycopg2


def get_heatmap_data():
    conn = psycopg2.connect(dbname="metroflow_db")

    query = """
        SELECT
            stop_name,
            latitude,
            longitude,
            SUM(entries) AS entries,
            SUM(exits) AS exits
        FROM nyc_subway_traffic
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        GROUP BY stop_name, latitude, longitude
        ORDER BY entries DESC
        LIMIT 100;
    """

    cursor = conn.cursor()
    cursor.execute(query)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    heatmap = []

    for row in rows:
        stop_name, latitude, longitude, entries, exits = row

        intensity = float(entries or 0) + float(exits or 0)

        heatmap.append({
            "station": stop_name,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "intensity": intensity,
        })

    return {
        "count": len(heatmap),
        "heatmap": heatmap,
    }