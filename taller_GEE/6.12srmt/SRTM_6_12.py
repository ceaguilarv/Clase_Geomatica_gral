import ee
import folium
import datetime
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
# 3. Punto y región de interés
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])
region_interes = punto_estudio.buffer(3000)

# =========================
# 4. Carga y procesamiento
# =========================
srtm = ee.Image("USGS/SRTMGL1_003")
hillshade = ee.Terrain.hillshade(srtm)

# =========================
# 5. Exportar JSON
# =========================
id_exacto = srtm.get('system:id').getInfo()
print(f"\nID de la imagen SRTM seleccionada: {id_exacto}")

metadatos_json = srtm.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_srtm_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

srtm_limpia = ee.Image(id_exacto)
texto_json_serializado = srtm_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "srtm_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 6. Parámetros de visualización
# =========================
vis_params = {'min': 0, 'max': 255}
map_id_dict = ee.Image(hillshade).getMapId(vis_params)

# =========================
# 7. Mapa HTML interactivo
# =========================
Map_srtm = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='Relieve SRTM'
).add_to(Map_srtm)

folium.LayerControl().add_to(Map_srtm)

ruta_html = os.path.join(carpeta_salida, "map_srtm_santa_librada.html")
Map_srtm.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 8. PNG estático con grilla ~1 km
# =========================
url_img = hillshade.getThumbURL({
    'min': 0,
    'max': 255,
    'dimensions': 800,
    'region': region_interes
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

coords = region_interes.bounds().coordinates().get(0).getInfo()
xmin, ymin = coords[0][0], coords[0][1]
xmax, ymax = coords[2][0], coords[2][1]

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, cmap='gray', extent=[xmin, xmax, ymin, ymax])

# 1 km ≈ 0.009 grados
paso_1km = 0.009
x_ticks = [lon_centro + (i * paso_1km) for i in range(-4, 5)]
y_ticks = [lat_centro + (i * paso_1km) for i in range(-4, 5)]

x_ticks = [x for x in x_ticks if xmin <= x <= xmax]
y_ticks = [y for y in y_ticks if ymin <= y <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.3f}°" for x in x_ticks])
ax.set_yticklabels([f"{y:.3f}°" for y in y_ticks])

ax.grid(color='white', linestyle='--', linewidth=0.8, alpha=0.5)
ax.set_title('Relieve SRTM - Santa Librada (Píxel ~30 m, Grilla ~1 km)', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "srtm_santa_librada_hillshade.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.12 completada correctamente.")