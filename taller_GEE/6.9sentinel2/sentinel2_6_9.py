import ee
import datetime
import json
import os
import folium
import requests
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# =========================
# 1. Inicializar GEE
# =========================
ee.Initialize(project='bamboo-storm-477002-v4')

# =========================
# 2. Carpeta de salida
# =========================
carpeta_salida = "/home/rstudio/work"
os.makedirs(carpeta_salida, exist_ok=True)

# =========================
# 3. Área de estudio
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])
region_interes = punto_estudio.buffer(3000)

# =========================
# 4. Colección Sentinel-2
# =========================
coleccion_s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(punto_estudio)
    .filterDate('2023-01-01', '2023-12-31')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
)

imagen_s2 = coleccion_s2.first()

# =========================
# 5. Información básica
# =========================
id_exacto = imagen_s2.get('system:id').getInfo()
fecha_ms = imagen_s2.get('system:time_start').getInfo()
fecha = datetime.datetime.fromtimestamp(fecha_ms / 1000.0, datetime.UTC).strftime('%Y-%m-%d')
nubosidad = imagen_s2.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()

print("=== SENTINEL-2 SANTA LIBRADA ===")
print("ID exacto:", id_exacto)
print("Fecha:", fecha)
print("Nubosidad:", nubosidad)

# =========================
# 6. Guardar metadatos
# =========================
metadatos = imagen_s2.toDictionary().getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_sentinel2_santa_librada.json")

with open(ruta_meta, "w", encoding="utf-8") as f:
    json.dump(metadatos, f, indent=2, ensure_ascii=False)

print("Metadatos guardados en:", ruta_meta)

# =========================
# 7. Guardar serializado
# =========================
imagen_limpia = ee.Image(id_exacto)
serializado = imagen_limpia.serialize()

ruta_serializado = os.path.join(carpeta_salida, "sentinel2_santa_librada_serializado.json")

with open(ruta_serializado, "w", encoding="utf-8") as f:
    json.dump(serializado, f)

print("Serializado guardado en:", ruta_serializado)

# =========================
# 8. Mapa HTML interactivo
# =========================
vis_params = {
    'bands': ['B4', 'B3', 'B2'],
    'min': 0,
    'max': 3000
}

map_id_dict = ee.Image(imagen_s2).getMapId(vis_params)

m = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name=f'Sentinel-2 RGB - {fecha}'
).add_to(m)

folium.LayerControl().add_to(m)

ruta_html = os.path.join(carpeta_salida, "map_sentinel2_santa_librada.html")
m.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 9. Miniatura PNG estática
# =========================
url_img = imagen_s2.getThumbURL({
    'bands': ['B4', 'B3', 'B2'],
    'min': 0,
    'max': 3000,
    'dimensions': 800,
    'region': region_interes
})

print("URL miniatura:", url_img)

respuesta = requests.get(url_img)
respuesta.raise_for_status()

imagen_png = Image.open(BytesIO(respuesta.content))

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png)
ax.set_title(f"Sentinel-2 RGB - Santa Librada ({fecha})")
ax.axis('off')

ruta_png = os.path.join(carpeta_salida, "sentinel2_santa_librada_rgb.png")
plt.tight_layout()
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)

print("\nSección 6.9 completada correctamente.")