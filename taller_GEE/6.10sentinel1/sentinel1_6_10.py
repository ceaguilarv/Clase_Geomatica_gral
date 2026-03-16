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
# 3. Definición del punto geográfico
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])
region_interes = punto_estudio.buffer(3000)

# =========================
# 4. Explorar opciones y filtrar
# =========================
coleccion_s1 = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(punto_estudio)
    .filterDate('2023-01-01', '2023-12-31')
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
)

# =========================
# 5. Diagnóstico: top 3 imágenes
# =========================
ids = coleccion_s1.aggregate_array('system:id').getInfo()
fechas = coleccion_s1.aggregate_array('system:time_start').getInfo()

print("--- TOP 3 IMÁGENES SENTINEL-1 (2023) ---")
for i in range(min(3, len(ids))):
    fecha_legible = datetime.datetime.fromtimestamp(
        fechas[i] / 1000.0, datetime.UTC
    ).strftime('%Y-%m-%d')
    print(f"Opción {i+1} | Fecha: {fecha_legible}")
    print(f"ID: {ids[i]}\n")
print("----------------------------------------------------------------")

# =========================
# 6. Selección definitiva
# =========================
s1 = ee.Image(coleccion_s1.first())

# =========================
# 7. Exportar JSON
# =========================
id_exacto = s1.get('system:id').getInfo()
print(f"\nID de la imagen Sentinel 1 seleccionada: {id_exacto}")

metadatos_json = s1.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_sentinel1_santa_librada.json")
with open(ruta_meta, 'w', encoding='utf-8') as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

s1_limpia = ee.Image(id_exacto)
texto_json_serializado = s1_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "sentinel1_santa_librada_serializado.json")
with open(ruta_ser, 'w', encoding='utf-8') as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 8. Parámetros de visualización
# =========================
vis_params = {'bands': ['VV'], 'min': -20, 'max': 0}
map_id_dict = ee.Image(s1).getMapId(vis_params)

# =========================
# 9. Mensaje final del mapa
# =========================
fecha_capa_ms = s1.get('system:time_start').getInfo()
fecha_capa = datetime.datetime.fromtimestamp(
    fecha_capa_ms / 1000.0, datetime.UTC
).strftime('%Y-%m-%d')

print("\n✅ MAPA GENERADO CON ÉXITO")
print(f"Capa desplegada : Sentinel 1 VV - {fecha_capa}")
print("----------------------------------------------------------------")

# =========================
# 10. Mapa HTML interactivo
# =========================
Map_s1 = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name=f'Sentinel 1 VV - {fecha_capa}'
).add_to(Map_s1)

folium.LayerControl().add_to(Map_s1)

ruta_html = os.path.join(carpeta_salida, "map_sentinel1_santa_librada.html")
Map_s1.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 11. Mapa estático PNG
# =========================
url_img = s1.getThumbURL({
    'bands': ['VV'],
    'min': -20,
    'max': 0,
    'dimensions': 800,
    'region': region_interes
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()

imagen_png = Image.open(BytesIO(respuesta.content))

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png)
ax.set_title(f"Sentinel 1 VV - Santa Librada ({fecha_capa})")
ax.axis('off')

ruta_png = os.path.join(carpeta_salida, "sentinel1_santa_librada_vv.png")
plt.tight_layout()
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.10 completada correctamente.")