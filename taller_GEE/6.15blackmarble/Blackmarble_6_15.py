import ee
import folium
import datetime
import json
import os
import requests
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
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
region_interes = punto_estudio.buffer(10000).bounds()

# =========================
# 4. Colección BlackMarble / VIIRS NTL
# =========================
coleccion_ntl = (
    ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
    .filterBounds(punto_estudio)
    .filterDate('2023-01-01', '2023-12-31')
)

# =========================
# 5. Diagnóstico: top 3
# =========================
ids = coleccion_ntl.aggregate_array('system:id').getInfo()
fechas = coleccion_ntl.aggregate_array('system:time_start').getInfo()

print("--- TOP 3 IMÁGENES BLACKMARBLE (2023) ---")
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
ntl = ee.Image(coleccion_ntl.first())

id_exacto = ntl.get('system:id').getInfo()
fecha_ms = ntl.get('system:time_start').getInfo()
fecha = datetime.datetime.fromtimestamp(
    fecha_ms / 1000.0, datetime.UTC
).strftime('%Y-%m-%d')

print(f"\nID de la imagen BlackMarble seleccionada: {id_exacto}")
print(f"Fecha: {fecha}")

# =========================
# 7. Guardar metadatos
# =========================
metadatos_json = ntl.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_ntl_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 8. Guardar serializado
# =========================
ntl_limpia = ee.Image(id_exacto)
texto_json_serializado = ntl_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "ntl_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 9. Parámetros de visualización de la guía
# =========================
vis_params = {'bands': ['avg_rad'], 'min': 0, 'max': 60}
map_id_dict = ee.Image(ntl).getMapId(vis_params)

# =========================
# 10. Mapa HTML interactivo con base oscura
# =========================
Map_ntl = folium.Map(
    location=[lat_centro, lon_centro],
    zoom_start=14,
    tiles='CartoDB dark_matter'
)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name=f'Luces Nocturnas - {fecha}'
).add_to(Map_ntl)

folium.LayerControl().add_to(Map_ntl)

ruta_html = os.path.join(carpeta_salida, "map_ntl_santa_librada.html")
Map_ntl.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 11. PNG estático con grilla ~10 km
# =========================
url_img = ntl.getThumbURL({
    'bands': ['avg_rad'],
    'min': 0,
    'max': 60,
    'palette': ['black', 'white'],
    'dimensions': 800,
    'region': region_interes
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

coords = region_interes.coordinates().get(0).getInfo()
xmin = min([c[0] for c in coords])
xmax = max([c[0] for c in coords])
ymin = min([c[1] for c in coords])
ymax = max([c[1] for c in coords])

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

# 10 km ≈ 0.09 grados
paso_10km = 0.09
lon_grid, lat_grid = (xmin + xmax) / 2, (ymin + ymax) / 2

x_ticks = [lon_grid + (i * paso_10km) for i in range(-5, 6)
           if xmin <= lon_grid + (i * paso_10km) <= xmax]
y_ticks = [lat_grid + (i * paso_10km) for i in range(-5, 6)
           if ymin <= lat_grid + (i * paso_10km) <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.2f}°" for x in x_ticks])
ax.set_yticklabels([f"{y:.2f}°" for y in y_ticks])

ax.grid(color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax.set_title(f"Luces Nocturnas BlackMarble - Santa Librada ({fecha})", fontsize=14)
ax.set_xlabel("Longitud")
ax.set_ylabel("Latitud")
ax.set_facecolor("#111111")

# barra de color
norm = Normalize(vmin=0, vmax=60)
sm = ScalarMappable(norm=norm, cmap='gray')
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Radiancia promedio (avg_rad)")

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "ntl_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.15 completada correctamente.")