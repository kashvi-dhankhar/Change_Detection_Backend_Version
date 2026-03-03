import threading
from queue import Queue
from typing import Optional, List
import ee

from pipeline.gee_fetch import fetch_sentinel2
from pipeline.aoi_loader import load_aoi
from pipeline.indices import add_indices
from pipeline.change_rules import (
    vegetation_loss,
    vegetation_gain,
    water_expansion,
    water_shrinkage,
    urban_expansion,
    calculate_area,
    mask_to_vectors
)

# --------------------------------------------------
# GLOBAL STATE
# --------------------------------------------------
STATUS_QUEUE = Queue()
RESULT_DATA: Optional[dict] = None
TASK_RUNNING = False


# --------------------------------------------------
# STATUS HELPER
# --------------------------------------------------
def push_status(msg: str):
    print(msg)
    STATUS_QUEUE.put(msg)


# --------------------------------------------------
# FEATURE HELPER
# --------------------------------------------------
def extract_features(fc_geojson: dict, change_type: str, area_m2: float) -> List[dict]:
    features = []
    for f in fc_geojson.get("features", []):
        f["properties"] = {
            "change_type": change_type,
            "area_m2": area_m2
        }
        features.append(f)
    return features


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------
def run_change_detection(kml_path: str, from_date: str, to_date: str):
    global TASK_RUNNING, RESULT_DATA

    try:
        push_status("🛰️ Initializing Earth Engine...")
        ee.Initialize(project="ai-satellite-change-detection")

        push_status("📍 Loading AOI from uploaded KML...")
        aoi = load_aoi(kml_path)

        mid_date = ee.Date(from_date).advance(
            ee.Date(to_date).difference(ee.Date(from_date), "day").divide(2),
            "day"
        )

        push_status("🌍 Fetching Sentinel-2 (T1)...")
        img_t1 = add_indices(
            fetch_sentinel2(aoi, from_date, mid_date.format("YYYY-MM-dd").getInfo())
        )

        push_status("🌍 Fetching Sentinel-2 (T2)...")
        img_t2 = add_indices(
            fetch_sentinel2(aoi, mid_date.format("YYYY-MM-dd").getInfo(), to_date)
        )

        ndvi_diff = img_t2.select("NDVI").subtract(img_t1.select("NDVI"))
        ndwi_diff = img_t2.select("NDWI").subtract(img_t1.select("NDWI"))
        ndbi_diff = img_t2.select("NDBI").subtract(img_t1.select("NDBI"))

        all_features: List[dict] = []

        # ---------------- VEGETATION LOSS ----------------
        push_status("🌱 Detecting vegetation loss...")
        mask = vegetation_loss(ndvi_diff).selfMask()
        fc = mask_to_vectors(mask, aoi).getInfo()
        area = calculate_area(mask, aoi).get("change", 0)
        all_features += extract_features(fc, "vegetation_loss", area)

        # ---------------- VEGETATION GAIN ----------------
        push_status("🌿 Detecting vegetation gain...")
        mask = vegetation_gain(ndvi_diff).selfMask()
        fc = mask_to_vectors(mask, aoi).getInfo()
        area = calculate_area(mask, aoi).get("change", 0)
        all_features += extract_features(fc, "vegetation_gain", area)

        # ---------------- WATER EXPANSION ----------------
        push_status("💧 Detecting water expansion...")
        mask = water_expansion(ndwi_diff).selfMask()
        fc = mask_to_vectors(mask, aoi).getInfo()
        area = calculate_area(mask, aoi).get("change", 0)
        all_features += extract_features(fc, "water_expansion", area)

        # ---------------- WATER SHRINKAGE ----------------
        push_status("💦 Detecting water shrinkage...")
        mask = water_shrinkage(ndwi_diff).selfMask()
        fc = mask_to_vectors(mask, aoi).getInfo()
        area = calculate_area(mask, aoi).get("change", 0)
        all_features += extract_features(fc, "water_shrinkage", area)

        # ---------------- URBAN EXPANSION ----------------
        push_status("🏙️ Detecting urban expansion...")
        mask = urban_expansion(ndbi_diff, ndvi_diff).selfMask()
        fc = mask_to_vectors(mask, aoi).getInfo()
        area = calculate_area(mask, aoi).get("change", 0)
        all_features += extract_features(fc, "urban_expansion", area)

        # ---------------- FINAL GEOJSON ----------------
        RESULT_DATA = {
            "type": "FeatureCollection",
            "features": all_features if all_features else []
        }

        push_status("✅ Completed")

    except Exception as e:
        push_status(f"❌ Error: {str(e)}")

    finally:
        TASK_RUNNING = False


# --------------------------------------------------
# TASK STARTER
# --------------------------------------------------
def start_task(kml_path: str, from_date: str, to_date: str):
    global TASK_RUNNING

    if TASK_RUNNING:
        raise RuntimeError("Task already running")

    TASK_RUNNING = True
    threading.Thread(
        target=run_change_detection,
        args=(kml_path, from_date, to_date),
        daemon=True
    ).start()


# --------------------------------------------------
# SSE STREAM
# --------------------------------------------------
def get_status_stream():
    while True:
        msg = STATUS_QUEUE.get()
        yield f"data: {msg}\n\n"
        if "completed" in msg.lower() or "error" in msg.lower():
            break


# --------------------------------------------------
# RESULT FETCH
# --------------------------------------------------
def get_result():
    return RESULT_DATA
