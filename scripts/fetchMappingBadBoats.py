import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Mapping Bad Boats: The Floating Stories Lab / ReTISS
# UN Ocean Decade endorsed Action
SERVICE_URL = (
    "https://services-eu1.arcgis.com/APM8FyQ4IgTmRlob/arcgis/rest/services/"
    "survey123_523fa2f55e7b42ee8752f33033616991_results/"
    "FeatureServer/0/query"
)

OUTPUT_FILE = "/maps/mapping_bad_boats.geojson"
PAGE_SIZE = 500

# Keep only the attributes needed for the Digital Atlas.
FIELDS = [
    "objectid",
    "country",
    "date_of_observation",
    "vessel_type",
    "vessel_classification",
    "primary_habitat_nearby",
]


def fetch_page(offset):
    params = {
        "where": "1=1",
        "outFields": ",".join(FIELDS),
        "returnGeometry": "true",
        "outSR": "4326",
        "resultOffset": offset,
        "resultRecordCount": PAGE_SIZE,
        "orderByFields": "objectid ASC",
        "f": "geojson",
    }

    url = SERVICE_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)

    if data.get("type") != "FeatureCollection":
        raise ValueError("ArcGIS did not return a valid GeoJSON FeatureCollection.")

    return data.get("features", [])


def format_date(timestamp):
    if timestamp is None:
        return None

    return datetime.fromtimestamp(
        int(timestamp) / 1000,
        tz=timezone.utc
    ).strftime("%Y-%m-%d")


def update_mapping_bad_boats():
    all_features = []
    offset = 0

    while True:
        features = fetch_page(offset)
        all_features.extend(features)

        if len(features) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    if not all_features:
        raise ValueError("No Mapping Bad Boats observations were returned.")

    cleaned_features = []

    for feature in all_features:
        geometry = feature.get("geometry")

        if not geometry or geometry.get("type") != "Point":
            continue

        properties = feature.get("properties", {})

        cleaned_features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "objectid": properties.get("objectid"),
                "country": properties.get("country"),
                "observation_date": format_date(
                    properties.get("date_of_observation")
                ),
                "vessel_type": properties.get("vessel_type"),
                "vessel_classification": properties.get("vessel_classification"),
                "primary_habitat_nearby": properties.get("primary_habitat_nearby"),
            },
        })

    if not cleaned_features:
        raise ValueError("No valid point observations were returned.")

    geojson = {
        "type": "FeatureCollection",
        "features": cleaned_features,
    }

    # Write safely so a failed update does not overwrite existing data.
    output_directory = os.path.dirname(OUTPUT_FILE)
    os.makedirs(output_directory, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_directory,
            suffix=".tmp",
            delete=False
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(geojson, temporary_file, ensure_ascii=False)

        os.replace(temporary_path, OUTPUT_FILE)

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

    print(
        f"Mapping Bad Boats updated successfully: "
        f"{len(cleaned_features)} observations saved."
    )


if __name__ == "__main__":
    try:
        update_mapping_bad_boats()
    except Exception as error:
        print(f"Mapping Bad Boats update failed: {error}")
        raise
