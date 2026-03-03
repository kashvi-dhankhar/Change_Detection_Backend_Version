# import ee

# # ---------------------------------------------
# # SIMPLE, SAFE THRESHOLDS (DEBUG FRIENDLY)
# # ---------------------------------------------
# NDVI_DROP = -0.1
# NDVI_RISE = 0.1
# NDWI_RISE = 0.1
# NDWI_DROP = -0.1
# NDBI_RISE = 0.1


# def vegetation_loss(ndvi_diff):
#     return ndvi_diff.lt(NDVI_DROP)


# def vegetation_gain(ndvi_diff):
#     return ndvi_diff.gt(NDVI_RISE)


# def water_expansion(ndwi_diff):
#     return ndwi_diff.gt(NDWI_RISE)


# def water_shrinkage(ndwi_diff):
#     return ndwi_diff.lt(NDWI_DROP)


# def urban_expansion(ndbi_diff, ndvi_diff):
#     return ndbi_diff.gt(NDBI_RISE).And(ndvi_diff.lt(0))


# def calculate_area(mask, aoi):
#     pixel_area = mask.multiply(ee.Image.pixelArea())
#     area = pixel_area.reduceRegion(
#         reducer=ee.Reducer.sum(),
#         geometry=aoi,
#         scale=10,
#         maxPixels=1e13
#     )
#     return area.getInfo()



# # ----------------------------------------
# # AREA CALCULATION (m²)
# # ----------------------------------------

# def calculate_area(mask, aoi):
#     pixel_area = ee.Image.pixelArea()
#     area_img = mask.multiply(pixel_area)

#     stats = area_img.reduceRegion(
#         reducer=ee.Reducer.sum(),
#         geometry=aoi,
#         scale=10,
#         maxPixels=1e13
#     )

#     return stats.getInfo()




import ee

# ---------------------------------------------
# THRESHOLDS (SAFE DEFAULTS)
# ---------------------------------------------
NDVI_DROP = -0.1
NDVI_RISE = 0.1
NDWI_RISE = 0.1
NDWI_DROP = -0.1
NDBI_RISE = 0.1

MIN_AREA_M2 = 500  # 🔥 remove tiny noisy polygons


# ---------------------------------------------
# PIXEL-LEVEL CHANGE MASKS
# ---------------------------------------------
def vegetation_loss(ndvi_diff):
    return ndvi_diff.lt(NDVI_DROP)


def vegetation_gain(ndvi_diff):
    return ndvi_diff.gt(NDVI_RISE)


def water_expansion(ndwi_diff):
    return ndwi_diff.gt(NDWI_RISE)


def water_shrinkage(ndwi_diff):
    return ndwi_diff.lt(NDWI_DROP)


def urban_expansion(ndbi_diff, ndvi_diff):
    return ndbi_diff.gt(NDBI_RISE).And(ndvi_diff.lt(0))


# ---------------------------------------------
# AREA CALCULATION (m²)
# ---------------------------------------------
def calculate_area(mask, aoi):
    area_img = mask.selfMask().multiply(ee.Image.pixelArea())

    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi,
        scale=10,
        maxPixels=1e13
    )

    return stats.getInfo()


# ---------------------------------------------
# CLEAN VECTOR OUTPUT (FOR GEOJSON)
# ---------------------------------------------
def mask_to_vectors(mask, aoi):
    return (
        mask.selfMask()
        .rename("change")
        .reduceToVectors(
            geometry=aoi,
            scale=10,
            geometryType="polygon",
            reducer=ee.Reducer.countEvery(),
            maxPixels=1e13
        )
    )

    # return vectors
