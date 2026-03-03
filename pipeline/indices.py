import ee

def add_indices(img: ee.Image) -> ee.Image:
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndwi = img.normalizedDifference(["B3", "B8"]).rename("NDWI")
    ndbi = img.normalizedDifference(["B11", "B8"]).rename("NDBI")
    return img.addBands([ndvi, ndwi, ndbi])
