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
# 3. Definición del área (Cundinamarca completa, como en la guía)
# =========================
departamentos = ee.FeatureCollection("FAO/GAUL/2015/level1")
cundinamarca = departamentos.filter(ee.Filter.eq('ADM1_NAME', 'Cundinamarca'))
region_interes = cundinamarca.geometry().bounds()

# =========================
# 4. Colección CHIRPS (mayo 2023)
# =========================
coleccion_chirps = (
    ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    .filterBounds(cundinamarca)
    .filterDate('2023-05-01', '2023-05-31')
)

# =========================
# 5. Diagnóstico: top 3
# =========================
ids = coleccion_chirps.aggregate_array('system:id').getInfo()
fechas = coleccion_chirps.aggregate_array('system:time_start').getInfo()

print("--- TOP 3 IMÁGENES CHIRPS (MAYO 2023) ---")
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
chirps = ee.Image(coleccion_chirps.first()).clip(cundinamarca)

id_exacto = chirps.get('system:id').getInfo()
fecha_ms = chirps.get('system:time_start').getInfo()
fecha = datetime.datetime.fromtimestamp(
    fecha_ms / 1000.0, datetime.UTC
).strftime('%Y-%m-%d')

print(f"\nID de la imagen CHIRPS seleccionada: {id_exacto}")
print(f"Fecha: {fecha}")

# =========================
# 7. Guardar metadatos
# =========================
metadatos_json = chirps.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_chirps_cundinamarca.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 8. Guardar serializado
# =========================
chirps_limpia = ee.Image(id_exacto).clip(cundinamarca)
texto_json_serializado = chirps_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "chirps_cundinamarca_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 9. Parámetros de visualización de la guía
# =========================
vis_params = {
    'bands': ['precipitation'],
    'min': 0,
    'max': 50,
    'palette': ['white', 'blue']
}

map_id_dict = ee.Image(chirps).getMapId(vis_params)

# =========================
# 10. Mapa HTML interactivo
# =========================
Map_clima = folium.Map(location=[4.638, -74.084], zoom_start=8)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name=f'Precipitación - {fecha}'
).add_to(Map_clima)

folium.LayerControl().add_to(Map_clima)

ruta_html = os.path.join(carpeta_salida, "map_chirps_cundinamarca.html")
Map_clima.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 11. PNG estático con grilla ~25 km
# =========================
stats = chirps.reduceRegion(
    reducer=ee.Reducer.minMax(),
    geometry=cundinamarca.geometry(),
    scale=5566,
    maxPixels=1e9
).getInfo()

val_min = stats.get('precipitation_min', 0)
val_max = stats.get('precipitation_max', 50)

if val_min == val_max:
    val_max = val_min + 1.0

url_img = chirps.getThumbURL({
    'bands': ['precipitation'],
    'min': val_min,
    'max': val_max,
    'palette': ['white', 'blue'],
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

# 25 km ≈ 0.25 grados
paso_25km = 0.25
lon_grid, lat_grid = (xmin + xmax) / 2, (ymin + ymax) / 2

x_ticks = [lon_grid + (i * paso_25km) for i in range(-5, 6)
           if xmin <= lon_grid + (i * paso_25km) <= xmax]
y_ticks = [lat_grid + (i * paso_25km) for i in range(-5, 6)
           if ymin <= lat_grid + (i * paso_25km) <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.2f}°" for x in x_ticks])
ax.set_yticklabels([f"{y:.2f}°" for y in y_ticks])

ax.grid(color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax.set_title('Precipitación CHIRPS - Cundinamarca (Píxel ~5.5 km, Grilla ~25 km)', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_facecolor('#e0e0e0')

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "chirps_cundinamarca_precipitacion.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.13 completada correctamente.")