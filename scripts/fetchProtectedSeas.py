# FETCHPROTECTEDSEAS - collects the ProtectedSeas Navigator "All Sites" layer
# for the UN Ocean Decade's Global Digital Atlas.
#
# The ArcGIS Feature Service limits standard feature queries, so this script
# first retrieves all OBJECTIDs and downloads the complete dataset in batches.
# The downloaded GeoJSON is then converted to a spatially indexed GeoPackage
# for more efficient use by MapServer.
#
# :date: 2026-08-28
# :version: 1.1.0

import urllib.request
import urllib.parse
import urllib.error
import json
import os
import sys
import time
import subprocess
import shutil

protectedSeasURL = (
    "https://services9.arcgis.com/lm7wE8a9YA9rKfzy/arcgis/rest/services/"
    "Navigator_AllSites_010925_attributes/FeatureServer/0/query"
)

geojsonFile = "/maps/protectedseas_navigator.geojson"
temporaryGeoJSON = geojsonFile + ".tmp"

geoPackageFile = "/maps/protectedseas_navigator.gpkg"
temporaryGeoPackage = "/tmp/protectedseas_navigator.gpkg"
temporaryGeoPackageCopy = "/maps/protectedseas_navigator.gpkg.tmp"

batchSize = 250


def post_request(parameters, retries=3):
    data = urllib.parse.urlencode(parameters).encode("utf-8")

    request = urllib.request.Request(
        protectedSeasURL,
        data=data,
        headers={
            "User-Agent": "UN-Ocean-Decade-Atlas-Updater/1.0"
        }
    )

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(
                request,
                timeout=120
            ) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt == retries:
                raise

            print(
                f"Request failed on attempt {attempt}. Retrying..."
            )

            time.sleep(5)


try:
    # Get all record IDs
    idResponse = post_request({
        "where": "1=1",
        "returnIdsOnly": "true",
        "f": "json"
    })

    if "error" in idResponse:
        raise RuntimeError(
            f"ArcGIS ID query error: {idResponse['error']}"
        )

    objectIDs = sorted(
        idResponse.get("objectIds", [])
    )

    if not objectIDs:
        raise RuntimeError(
            "ProtectedSeas returned no OBJECTIDs."
        )

    expectedCount = len(objectIDs)

    print(
        f"ProtectedSeas records reported by source: "
        f"{expectedCount}"
    )

    downloadedCount = 0
    firstFeature = True

    # Stream GeoJSON to disk
    with open(
        temporaryGeoJSON,
        "w",
        encoding="utf-8"
    ) as output:

        output.write(
            '{"type":"FeatureCollection","features":['
        )

        for start in range(
            0,
            expectedCount,
            batchSize
        ):

            batchIDs = objectIDs[
                start:start + batchSize
            ]

            batchResponse = post_request({
                "objectIds": ",".join(
                    str(objectID)
                    for objectID in batchIDs
                ),
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson"
            })

            if "error" in batchResponse:
                raise RuntimeError(
                    "ArcGIS batch query error: "
                    f"{batchResponse['error']}"
                )

            features = batchResponse.get(
                "features",
                []
            )

            for feature in features:
                if not firstFeature:
                    output.write(",")

                json.dump(
                    feature,
                    output,
                    ensure_ascii=False
                )

                firstFeature = False
                downloadedCount += 1

            output.flush()

            print(
                f"Downloaded {downloadedCount} of "
                f"{expectedCount} ProtectedSeas records..."
            )

        output.write("]}")

    if downloadedCount != expectedCount:
        raise RuntimeError(
            "ProtectedSeas download incomplete: "
            f"{downloadedCount} of "
            f"{expectedCount} records downloaded."
        )

    os.replace(
        temporaryGeoJSON,
        geojsonFile
    )

    print(
        f"ProtectedSeas download complete: "
        f"{downloadedCount} records."
    )

    if os.path.exists(temporaryGeoPackage):
        os.remove(temporaryGeoPackage)

    print(
        "Creating spatially indexed ProtectedSeas GeoPackage..."
    )

    subprocess.run(
        [
            "ogr2ogr",
            "-f", "GPKG",
            temporaryGeoPackage,
            geojsonFile,
            "-nln", "protectedseas_navigator",
            "-lco", "SPATIAL_INDEX=YES"
        ],
        check=True
    )

    # Verify GeoPackage feature count
    result = subprocess.run(
        [
            "ogrinfo",
            "-ro",
            "-so",
            temporaryGeoPackage,
            "protectedseas_navigator"
        ],
        check=True,
        capture_output=True,
        text=True
    )

    expectedLine = f"Feature Count: {expectedCount}"

    if expectedLine not in result.stdout:
        raise RuntimeError(
            "ProtectedSeas GeoPackage validation failed. "
            f"Expected {expectedCount} features."
        )

    # Copy completed GeoPackage into shared maps directory
    shutil.copyfile(
        temporaryGeoPackage,
        temporaryGeoPackageCopy
    )

    # Atomically replace the working MapServer copy
    os.replace(
        temporaryGeoPackageCopy,
        geoPackageFile
    )

    # GeoJSON is only an intermediate file
    if os.path.exists(geojsonFile):
        os.remove(geojsonFile)

    print(
        "ProtectedSeas update complete: "
        f"{expectedCount} records written to "
        f"{geoPackageFile}"
    )


except urllib.error.HTTPError as e:
    print(
        f"HTTP Error {e.code}: "
        "Unable to fetch ProtectedSeas data"
    )
    sys.exit(1)

except urllib.error.URLError as e:
    print(
        f"Network error encountered: {e.reason}"
    )
    sys.exit(1)

except json.JSONDecodeError as e:
    print(
        f"JSON reading error: {e}"
    )
    sys.exit(1)

except subprocess.CalledProcessError as e:
    print(
        f"GDAL conversion error: {e}"
    )
    sys.exit(1)

except (
    RuntimeError,
    PermissionError,
    OSError,
    TypeError,
    ValueError
) as e:
    print(
        f"ProtectedSeas update failed: {e}"
    )
    sys.exit(1)

finally:
    if os.path.exists(temporaryGeoJSON):
        os.remove(temporaryGeoJSON)

    if os.path.exists(temporaryGeoPackage):
        os.remove(temporaryGeoPackage)

    if os.path.exists(temporaryGeoPackageCopy):
        os.remove(temporaryGeoPackageCopy)
