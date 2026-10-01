from fastapi import FastAPI, Response, Query, HTTPException
import httpx
import math
import io
import asyncio
from PIL import Image

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

app = FastAPI()

COPERNICUS_BASE = "https://wmts.marine.copernicus.eu/teroWmts"
DEFAULT_SERVICE = "GLOBAL_MULTIYEAR_BGC_001_033/cmems_mod_glo_bgc_my_0.083deg-lmtl_P1D-i_202511"

EXTENT_MAX = 20037508.3427892
WORLD_SIZE = EXTENT_MAX * 2
TILE_PIXELS = 256

def get_bbox_intersecting_tiles_fixed(bbox_str: str, width: int):
    coords = [float(c) for c in bbox_str.replace("%2C", ",").split(",")]
    min_x, min_y, max_x, max_y = coords

    bbox_width = max_x - min_x
    if bbox_width <= 0:
        return 1, 0, 0, 0, 0, min_x, min_y, max_x, max_y
        
    resolution = bbox_width / width
    zoom_calc = math.log2(WORLD_SIZE / (resolution * TILE_PIXELS))
    zoom = max(1, min(12, math.ceil(zoom_calc)))

    matrix_size = 2 ** zoom
    tile_geo_size = WORLD_SIZE / matrix_size

    col_min = max(0, min(matrix_size - 1, int(math.floor((min_x + EXTENT_MAX) / tile_geo_size))))
    col_max = max(0, min(matrix_size - 1, int(math.floor((max_x + EXTENT_MAX) / tile_geo_size))))
    
    row_min = max(0, min(matrix_size - 1, int(math.floor((EXTENT_MAX - max_y) / tile_geo_size))))
    row_max = max(0, min(matrix_size - 1, int(math.floor((EXTENT_MAX - min_y) / tile_geo_size))))

    return zoom, col_min, col_max, row_min, row_max, tile_geo_size, min_x, min_y, max_x, max_y

async def fetch_single_tile(client, url, headers):
    try:
        res = await client.get(url, headers=headers, timeout=10.0)
        if res.status_code == 200:
            return Image.open(io.BytesIO(res.content))
    except Exception:
        pass
    return Image.new("RGBA", (TILE_PIXELS, TILE_PIXELS), (0, 0, 0, 0))

@app.get("/service")
@app.get("/")
async def wms_bridge_endpoint(
    request: str = Query(None, alias="REQUEST"),
    layers: str = Query(None, alias="LAYERS"),
    style: str = Query(None, alias="STYLE"),
    styles: str = Query(None, alias="STYLES"),
    bbox: str = Query(None, alias="BBOX"),
    width: int = Query(256, alias="WIDTH"),
    height: int = Query(256, alias="HEIGHT"),
    time: str = Query("2025-06-30T00:00:00Z", alias="TIME")
):
    if not request:
        return Response(content="Missing REQUEST Parameter", status_code=400)

    active_style = style or styles or ""
    if active_style.lower() == "none":
        active_style = ""

    service_path = DEFAULT_SERVICE
    if layers and "/" in layers:
        service_path = layers.replace("%2F", "/")

    full_layer_parameter = service_path

    if request.lower() == "getlegendgraphic":
        json_legend_url = f"{COPERNICUS_BASE}/?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetLegend&LAYER={full_layer_parameter}&STYLE={active_style}&FORMAT=application/json"
        headers = {"Host": "wmts.marine.copernicus.eu", "User-Agent": "Mozilla/5.0"}
        
        async with httpx.AsyncClient(verify=True) as client:
            try:
                res = await client.get(json_legend_url, headers=headers, timeout=10.0)
                if res.status_code != 200:
                    raise Exception("Upstream legend unavailable")

                payload = res.json()
                continuous_data = payload.get("continuous", {})
                
                variable_name = continuous_data.get("variableName", "Concentration")
                val_min = continuous_data.get("valueMin", 0.0)
                val_max = continuous_data.get("valueMax", 1.0)
                
                cmap_info = continuous_data.get("cmap", {})
                raw_colors = cmap_info.get("colorMap", [])
                
                if not raw_colors:
                    rgb_colors = ["#000033", "#003399", "#3399FF", "#66FFF3"]
                else:
                    rgb_colors = [(r/255.0, g/255.0, b/255.0) for r, g, b in raw_colors]

                cmap = mcolors.LinearSegmentedColormap.from_list("copernicus", rgb_colors, N=256)
                fig, ax = plt.subplots(figsize=(1.8, 4.5))
                fig.subplots_adjust(left=0.05, right=0.30, bottom=0.1, top=0.9)

                gradient = np.linspace(0, 1, 256).reshape(-1, 1)
                ax.imshow(gradient, cmap=cmap, aspect='auto', origin='lower', extent=[0, 1, val_min, val_max])
                ax.set_xticks([])
                
                ax.set_ylabel(variable_name, fontsize=8, fontweight='bold', wrap=True)
                ax.yaxis.set_label_position("right")
                ax.yaxis.tick_right()

                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=True)
                plt.close(fig)
                return Response(content=buf.getvalue(), media_type="image/png")

            except Exception as e:
                img = Image.new('RGBA', (180, 250), color=(255, 255, 255, 0))
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                return Response(content=buf.getvalue(), media_type="image/png")

    if request.lower() == "getmap" and bbox:
        zoom, col_min, col_max, row_min, row_max, tile_size, min_x, min_y, max_x, max_y = get_bbox_intersecting_tiles_fixed(bbox, width)

        cols_count = col_max - col_min + 1
        rows_count = row_max - row_min + 1

        headers = {
            "Host": "wmts.marine.copernicus.eu",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "image/avif,image/webp,image/png,image/*"
        }

        tasks = []
        async with httpx.AsyncClient(verify=True) as client:
            for r in range(row_min, row_max + 1):
                for c in range(col_min, col_max + 1):
                    url = (
                        f"{COPERNICUS_BASE}/?"
                        f"SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&"
                        f"LAYER={full_layer_parameter}&STYLE={active_style}&TIME={time}&"
                        f"TILEMATRIXSET=EPSG:3857&TILEMATRIX={zoom}&"
                        f"TILEROW={r}&TILECOL={c}&FORMAT=image/png"
                    )
                    tasks.append(fetch_single_tile(client, url, headers))
            
            tiles = await asyncio.gather(*tasks)

        canvas_w = cols_count * TILE_PIXELS
        canvas_h = rows_count * TILE_PIXELS
        master_canvas = Image.new("RGBA", (canvas_w, canvas_h))

        idx = 0
        for r_idx in range(rows_count):
            for c_idx in range(cols_count):
                master_canvas.paste(tiles[idx], (c_idx * TILE_PIXELS, r_idx * TILE_PIXELS))
                idx += 1

        grid_left_edge = (col_min * tile_size) - EXTENT_MAX
        grid_top_edge = EXTENT_MAX - (row_min * tile_size)

        crop_left = (min_x - grid_left_edge) / tile_size * TILE_PIXELS
        crop_right = (max_x - grid_left_edge) / tile_size * TILE_PIXELS
        crop_top = (grid_top_edge - max_y) / tile_size * TILE_PIXELS
        crop_bottom = (grid_top_edge - min_y) / tile_size * TILE_PIXELS

        cropped_img = master_canvas.crop((
            int(round(crop_left)), 
            int(round(crop_top)), 
            int(round(crop_right)), 
            int(round(crop_bottom))
        ))
        
        final_img = cropped_img.resize((width, height), Image.Resampling.BILINEAR)

        output_buf = io.BytesIO()
        final_img.save(output_buf, format="PNG")
        
        return Response(content=output_buf.getvalue(), media_type="image/png")

    return Response(content=f"Unsupported Action: {request}", status_code=400)
