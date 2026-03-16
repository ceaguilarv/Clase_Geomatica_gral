import ee
import folium
import json
import os
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
# 4. Colección DSWx Sentinel-1
# =========================
coleccion_dswx = (
    ee.ImageCollection("OPERA/DSWX/L3_V1/S1")
    .filterBounds(punto_estudio)
)

# =========================
# 5. Selección definitiva
# =========================
dswx = ee.Image(coleccion_dswx.first())

id_exacto = dswx.get('system:id').getInfo()
print(f"\nID de la imagen DSWx seleccionada: {id_exacto}")

# =========================
# 6. Guardar metadatos
# =========================
metadatos_json = dswx.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_dswx_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 7. Guardar serializado
# =========================
dswx_limpia = ee.Image(id_exacto)
texto_json_serializado = dswx_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "dswx_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 8. Parámetros de visualización
# =========================
vis_params = {
    'bands': ['WTR_Water_classification'],
    'min': 0,
    'max': 4,
    'palette': ['white', 'blue', 'cyan', 'gray', 'black']
}
map_id_dict = ee.Image(dswx).getMapId(vis_params)

# =========================
# 9. Mapa HTML interactivo
# =========================
Map_dswx = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='DSWx Agua'
).add_to(Map_dswx)

folium.LayerControl().add_to(Map_dswx)

ruta_html = os.path.join(carpeta_salida, "map_dswx_santa_librada.html")
Map_dswx.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 10. PNG estático
# =========================
url_img = dswx.getThumbURL({
    'bands': ['WTR_Water_classification'],
    'min': 0,
    'max': 4,
    'palette': ['white', 'blue', 'cyan', 'gray', 'black'],
    'dimensions': 800,
    'region': region_interes
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

coords = region_interes.bounds().coordinates().get(0).getInfo()
xmin, ymin = coords[0][0], coords[0][1]
xmax, ymax = coords[2][0], coords[2][1]

fig, ax = plt.subplots(figsize=(10, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

# Grilla ~1 km
paso_1km = 0.009
x_ticks = [lon_centro + (i * paso_1km) for i in range(-4, 5)]
y_ticks = [lat_centro + (i * paso_1km) for i in range(-4, 5)]
x_ticks = [x for x in x_ticks if xmin <= x <= xmax]
y_ticks = [y for y in y_ticks if ymin <= y <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.3f}°" for x in x_ticks])
ax.set_yticklabels([f"{y:.3f}°" for y in y_ticks])

ax.grid(color='gray', linestyle='--', linewidth=1, alpha=0.7)
ax.set_title('Clasificación de Agua DSWx - Santa Librada (Píxel ~30 m, Grilla ~1 km)', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')

# Leyenda
leyenda = [
    mpatches.Patch(color='white', label='0: No data / fondo'),
    mpatches.Patch(color='blue', label='1: Agua'),
    mpatches.Patch(color='cyan', label='2: Agua parcial / transición'),
    mpatches.Patch(color='gray', label='3: Incierto / otra clase'),
    mpatches.Patch(color='black', label='4: No agua / clase final')
]
ax.legend(handles=leyenda, loc='lower right', fontsize=8, frameon=True)

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "dswx_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.16 completada correctamente.")