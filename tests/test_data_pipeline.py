import pandas as pd

from src.data_utils import normalize_timestamp_to_utc, prepare_for_upsert


def test_prepare_for_upsert_removes_duplicates_and_keeps_last_value():
    df = pd.DataFrame(
        {
            "date_heure": [
                "2024-01-01T00:00:00+01:00",
                "2024-01-01T00:00:00+01:00",
                "2024-01-01T01:00:00+01:00",
            ],
            "region": ["FR-1", "FR-1", "FR-2"],
            "filiere": ["eolien_mw", "eolien_mw", "solaire_mw"],
            "consommation": [10, 12, 8],
        }
    )

    result = prepare_for_upsert(df)

    assert len(result) == 2
    assert result["consommation"].tolist() == [12, 8]
    assert result["region"].tolist() == ["FR-1", "FR-2"]
    assert str(result["date_heure"].dt.tz) == "UTC"


def test_normalize_timestamp_to_utc_converts_naive_and_offset_values():
    df = pd.DataFrame(
        {
            "date_heure": ["2024-05-01 10:00:00", "2024-05-01T09:00:00+01:00"],
            "region": ["FR-1", "FR-1"],
            "filiere": ["eolien_mw", "eolien_mw"],
            "consommation": [1.0, 2.5],
        }
    )

    result = normalize_timestamp_to_utc(df)

    assert result["date_heure"].dt.tz is not None
    assert str(result["date_heure"].dt.tz) == "UTC"
    assert result["date_heure"].tolist()[0].isoformat() == "2024-05-01T10:00:00+00:00"
    assert result["date_heure"].tolist()[1].isoformat() == "2024-05-01T08:00:00+00:00"


def test_prepare_for_upsert_handles_empty_input():
    result = prepare_for_upsert(pd.DataFrame(columns=["date_heure", "region", "filiere", "consommation"]))

    assert result.empty
    assert list(result.columns) == ["date_heure", "region", "filiere", "consommation"]
