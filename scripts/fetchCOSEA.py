import json
import math
import os
import tempfile
import time
import urllib.parse
import urllib.request

# COSEA citizen-science observations hosted by SPOTTERON
API_URL = "https://www.spotteron.com/api/v2.4/spots"
TOPIC_ID = 63
OUTPUT_FILE = "/maps/cosea_observations.geojson"


def fetch_page(page):
    params = {
        "filter[topic_id]": TOPIC_ID,
        "page": page,
    }

    url = API_URL + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OceanDecadeAtlasUpdater/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)

    if not isinstance(result.get("data"), list):
        raise ValueError(f"Invalid COSEA API response on page {page}")

    return result


def fetch_all_observations():
    first_page = fetch_page(1)
    metadata = first_page.get("meta", {})

    page_count = int(metadata["page_count"])
    expected_total = int(metadata["total"])

    if page_count < 1 or expected_total < 1:
        raise ValueError("COSEA API returned no observations")

    observations = list(first_page["data"])

    print(
        f"COSEA: downloading {expected_total} observations "
        f"across {page_count} pages"
    )

    for page in range(2, page_count + 1):
        time.sleep(0.2)
        result = fetch_page(page)
        observations.extend(result["data"])

        print(f"COSEA: downloaded page {page}/{page_count}")

    if len(observations) != expected_total:
        raise ValueError(
            f"Incomplete COSEA download: received {len(observations)} "
            f"of {expected_total} observations"
        )

    return observations


def convert_to_geojson(observations):
    features = []
    seen_ids = set()

    for observation in observations:
        attributes = observation.get("attributes", {})
        observation_id = observation.get("id")

        if observation_id is None or observation_id in seen_ids:
            raise ValueError("Duplicate or missing COSEA observation ID")

        seen_ids.add(observation_id)

        # Exclude non-public or inactive observations.
        if attributes.get("privacy_type") != 0:
            continue

        if attributes.get("state") != 1:
            continue

        latitude = attributes.get("latitude")
        longitude = attributes.get("longitude")

        if latitude is None or longitude is None:
            continue

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(latitude) or not math.isfinite(longitude):
            continue

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [longitude, latitude],
            },
            "properties": {
                "observation_id": observation_id,
                "project": "COSEA",
                "observation_date": attributes.get("spotted_at"),
                "category_id": attributes.get("category"),
            },
        })

    if not features:
        raise ValueError("No valid public COSEA observations found")

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def update_cosea():
    observations = fetch_all_observations()
    geojson = convert_to_geojson(observations)

    output_directory = os.path.dirname(OUTPUT_FILE)
    os.makedirs(output_directory, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_directory,
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(geojson, temporary_file, ensure_ascii=False)

        os.replace(temporary_path, OUTPUT_FILE)

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

    print(
        f"COSEA updated successfully: "
        f"{len(geojson['features'])} observations saved"
    )


if __name__ == "__main__":
    update_cosea()
