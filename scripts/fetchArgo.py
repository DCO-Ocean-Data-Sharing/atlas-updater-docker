# FETCHARGO - collects the last 10 days of Argo float locations for the UN Ocean
# Decade's Digital Atlas. The original source is the Erddap server at Ifremer.
#
# :author: Adam Leadbetter (@adamml)
# :date: 2026-08-18
# :version: 1.0.0

import urllib.request

argoURL: str = ("https://erddap.ifremer.fr/erddap/tabledap/" +
                "ArgoFloats.geoJson?" +
                "platform_number," +
                "project_name," +
                "platform_type," +
                "latitude," +
                "longitude&" +
                "time%3E%3Dnow-10days&" +
                "time%3Cnow")

try:
    with urllib.request.urlopen(argoURL, timeout=30) as resp:
        with open('/maps/argo_floats.geojson', 'wb') as f:
            f.write(resp.read())
except urllib.error.URLError as e:
    print(f"Network error encountered: {e.reason}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: Unable to fetch data from Mercator API")
except PermissionError:
    print(f"Permission denied: Cannot write to output file to disk {e}")
except TypeError as e:
    print(f"Data error: The parsed JSON dictionary contains non-serializable objects: {e}")
except OSError as e:
    print(f"Disk or System error while writing output file: {e}")
