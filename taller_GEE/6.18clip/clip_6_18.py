import ee
import folium
import json
import os
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
# 3. Punto de estudio
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])

# Área FINAL de recorte (pequeña)
area_clip = punto_estudio.buffer(1200).bounds()

# Área de BÚSQUEDA (más grande) para evitar problemas de borde de tile
area_busqueda = punto_estudio.buffer(8000)

# =========================
# 4. Cargar Sentinel-2
# =========================
coleccion_s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(area_busqueda)
    .filterDate('2023-01-01', '2023-12-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    .select(['B4', 'B3', 'B2', 'B8'])
)

cantidad = coleccion_s2.size().getInfo()
print("Número de imágenes candidatas:", cantidad)

# Diagnóstico útil: tiles presentes
try:
    mgrs_tiles = coleccion_s2.aggregate_array('MGRS_TILE').distinct().getInfo()
    print("Tiles MGRS encontrados:", mgrs_tiles)
except Exception:
    print("No fue posible leer MGRS_TILE")

# =========================
# 5. Composite + clip
# =========================
composite_s2 = coleccion_s2.median()
s2_clip = composite_s2.clip(area_clip)

# =========================
# 6. Guardar metadatos
# =========================
metadatos_json = {
    "coleccion": "COPERNICUS/S2_SR_HARMONIZED",
    "imagenes_usadas": cantidad,
    "metodo_composite": "median",
    "fecha_inicio": "2023-01-01",
    "fecha_fin": "2023-12-31",
    "filtro_nubosidad": "< 40%",
    "buffer_busqueda_metros": 8000,
    "buffer_clip_metros": 1200,
    "area_centro": {
        "latitud": lat_centro,
        "longitud": lon_centro
    },
    "proceso": "Composite Sentinel-2 + clip local en Santa Librada"
}

ruta_meta = os.path.join(carpeta_salida, "metadatos_s2_clip_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 7. Guardar serializado
# =========================
texto_json_serializado = s2_clip.serialize()
ruta_ser = os.path.join(carpeta_salida, "s2_clip_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 8. Visualización
# =========================
vis_params = {
    'bands': ['B4', 'B3', 'B2'],
    'min': 0,
    'max': 3000
}

map_id_img = ee.Image(s2_clip).getMapId(vis_params)

# Borde del recorte
borde_clip = ee.Image().paint(ee.FeatureCollection([ee.Feature(area_clip)]), 0, 2)
map_id_vector = borde_clip.getMapId({'palette': ['red']})

# =========================
# 9. Mapa HTML
# =========================
Map_filtro = folium.Map(location=[lat_centro, lon_centro], zoom_start=16)

folium.TileLayer(
    tiles=map_id_img['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='Sentinel-2 composite recortado'
).add_to(Map_filtro)

folium.TileLayer(
    tiles=map_id_vector['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='Límite de recorte'
).add_to(Map_filtro)

coords = area_clip.coordinates().get(0).getInfo()
xmin = min([c[0] for c in coords])
xmax = max([c[0] for c in coords])
ymin = min([c[1] for c in coords])
ymax = max([c[1] for c in coords])

Map_filtro.fit_bounds([[ymin, xmin], [ymax, xmax]])
folium.LayerControl().add_to(Map_filtro)

ruta_html = os.path.join(carpeta_salida, "map_filtro_santa_librada.html")
Map_filtro.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 10. PNG estático
# =========================
url_img = s2_clip.getThumbURL({
    'bands': ['B4', 'B3', 'B2'],
    'min': 0,
    'max': 3000,
    'dimensions': 800,
    'region': area_clip
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

# Grilla ~1 km
paso_1km = 0.009
x_ticks = [lon_centro + (i * paso_1km) for i in range(-3, 4)]
y_ticks = [lat_centro + (i * paso_1km) for i in range(-3, 4)]

x_ticks = [x for x in x_ticks if xmin <= x <= xmax]
y_ticks = [y for y in y_ticks if ymin <= y <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.3f}°" for x in x_ticks], rotation=45)
ax.set_yticklabels([f"{y:.3f}°" for y in y_ticks])

ax.grid(color='white', linestyle='--', linewidth=0.8, alpha=0.7)
ax.set_title('Sentinel-2 composite recortado - Santa Librada', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_facecolor('#e0e0e0')

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "s2_clip_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.18 corregida y completada correctamente.")