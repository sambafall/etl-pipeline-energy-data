from src.dashboard_data import build_history_query


def test_build_history_query_uses_filters_and_hourly_aggregation():
    query = build_history_query(
        "energy.eco_to_mix",
        region="FR-1",
        start_date="2024-01-01T00:00:00+00:00",
        end_date="2024-01-08T00:00:00+00:00",
        aggregate_hours=True,
    )

    assert "WHERE" in query
    assert "region = 'FR-1'" in query
    assert "date_heure >= '2024-01-01T00:00:00+00:00'" in query
    assert "date_heure < '2024-01-08T00:00:00+00:00'" in query
    assert "date_trunc('hour', date_heure)" in query
    assert "AVG(consommation) AS consommation" in query
