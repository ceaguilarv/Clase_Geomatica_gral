import ee
import geemap
import geopandas as gpd
from pathlib import Path

ee.Initialize(project="bamboo-storm-477002-v4")

base_dir = Path("/home/rstudio/work/Clase_Geomatica_gral/Clase_Geomatica_gral/Taller6_MDE")
data_dir = base_dir / "data"
raster_dir = base_dir / "data_heavy" / "raster"
raster_dir.mkdir(parents=True, exist_ok=True)

# =========================================================
# 1. LEER EL POLÍGONO REAL DE USME DESDE GPKG
# =========================================================
gpkg_path = data_dir / "area_estudio_usme.gpkg"

gdf = gpd.read_file(gpkg_path, layer="area_estudio_usme")

# Asegurar WGS84 para convertir a EE
if gdf.crs is None:
    raise ValueError("La capa no tiene CRS definido.")

gdf_wgs84 = gdf.to_crs("EPSG:4326")

# Convertir a objeto EE
aoi = geemap.geopandas_to_ee(gdf_wgs84)

# =========================================================
# 2. SRTM Y DERIVADOS
# =========================================================
srtm = ee.Image("USGS/SRTMGL1_003").clip(aoi)
pendiente = ee.Terrain.slope(srtm).clip(aoi)
aspecto = ee.Terrain.aspect(srtm).clip(aoi)
sombreado = ee.Terrain.hillshade(srtm).clip(aoi)

# =========================================================
# 3. EXPORTAR CON LA GEOMETRÍA REAL
# =========================================================
region = aoi.geometry()

geemap.ee_export_image(
    srtm,
    filename=str(raster_dir / "srtm_usme.tif"),
    scale=30,
    region=region,
    file_per_band=False
)

geemap.ee_export_image(
    pendiente,
    filename=str(raster_dir / "srtm_pendiente_usme.tif"),
    scale=30,
    region=region,
    file_per_band=False
)

geemap.ee_export_image(
    aspecto,
    filename=str(raster_dir / "srtm_aspecto_usme.tif"),
    scale=30,
    region=region,
    file_per_band=False
)

geemap.ee_export_image(
    sombreado,
    filename=str(raster_dir / "srtm_hillshade_usme.tif"),
    scale=30,
    region=region,
    file_per_band=False
)

print("Exportación completada con el polígono real de Usme:")
print(raster_dir / "srtm_usme.tif")
print(raster_dir / "srtm_pendiente_usme.tif")
print(raster_dir / "srtm_aspecto_usme.tif")
print(raster_dir / "srtm_hillshade_usme.tif")