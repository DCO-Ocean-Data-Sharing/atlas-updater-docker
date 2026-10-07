import os
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

SITEMAP_URL = "https://dco-ocean-data-sharing.github.io/atlas-updater-docker/sitemap.xml"
SITE_PREFIX = "/atlas-updater-docker/"


def get_sitemap_urls():
    print(f"Reading sitemap from {SITEMAP_URL}")

    with urllib.request.urlopen(SITEMAP_URL) as response:
        sitemap_data = response.read()

    root = ET.fromstring(sitemap_data)

    urls = []

    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            urls.append(element.text.strip())

    return urls


def get_repository_path(url):
    parsed_url = urlparse(url)
    path = parsed_url.path

    if SITE_PREFIX not in path:
        return None

    return path.split(SITE_PREFIX, 1)[1]


def synchronise_file(url, repository_path):
    if repository_path.startswith("maps/"):
        destination = "/" + repository_path

    elif repository_path.startswith("scripts/"):
        destination = "/" + repository_path

    else:
        return

    os.makedirs(os.path.dirname(destination), exist_ok=True)

    urllib.request.urlretrieve(url, destination)

    print(f"Synchronised {repository_path}")


sitemap_urls = get_sitemap_urls()

files_to_sync = []
mapserver_url = None

for url in sitemap_urls:
    repository_path = get_repository_path(url)

    if not repository_path:
        continue

    if repository_path == "maps/mapserver.map":
        mapserver_url = url

    elif repository_path.startswith("maps/") or repository_path.startswith("scripts/"):
        files_to_sync.append((url, repository_path))


# Synchronise supporting files and scripts first
for url, repository_path in files_to_sync:
    synchronise_file(url, repository_path)


# Synchronise the main MapServer configuration last
if mapserver_url:
    synchronise_file(mapserver_url, "maps/mapserver.map")
else:
    raise RuntimeError("maps/mapserver.map was not found in the sitemap.")


print("GitHub sitemap synchronisation completed successfully.")
