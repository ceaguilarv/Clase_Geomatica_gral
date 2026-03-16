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
# 3. Área de estudio
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])

# Para MODIS conviene una región más amplia por su resolución de ~500 m
region_interes = punto_estudio.buffer(10000).bounds()

# =========================
# 4. Colección MODIS
# =========================
coleccion_modis = (
    ee.ImageCollection("MODIS/061/MOD09GA")
    .filterBounds(punto_estudio)
    .filterDate('2023-01-01', '2023-12-31')
)

# =========================
# 5. Diagnóstico: top 3
# =========================
ids = coleccion_modis.aggregate_array('system:id').getInfo()
fechas = coleccion_modis.aggregate_array('system:time_start').getInfo()

print("--- TOP 3 IMÁGENES MODIS (2023) ---")
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
modis = ee.Image(coleccion_modis.first())

id_exacto = modis.get('system:id').getInfo()
fecha_ms = modis.get('system:time_start').getInfo()
fecha = datetime.datetime.fromtimestamp(
    fecha_ms / 1000.0, datetime.UTC
).strftime('%Y-%m-%d')

print(f"\nID de la imagen MODIS seleccionada: {id_exacto}")
print(f"Fecha: {fecha}")

# =========================
# 7. Guardar metadatos
# =========================
metadatos_json = modis.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_modis_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 8. Guardar serializado
# =========================
modis_limpia = ee.Image(id_exacto)
texto_json_serializado = modis_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "modis_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 9. Parámetros de visualización
# =========================
vis_params = {
    'bands': ['sur_refl_b01', 'sur_refl_b04', 'sur_refl_b03'],
    'min': -100,
    'max': 3000
}
map_id_dict = ee.Image(modis).getMapId(vis_params)

# =========================
# 10. Mapa HTML interactivo
# =========================
Map_modis = folium.Map(location=[lat_centro, lon_centro], zoom_start=12)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name=f'MODIS RGB - {fecha}'
).add_to(Map_modis)

folium.LayerControl().add_to(Map_modis)

ruta_html = os.path.join(carpeta_salida, "map_modis_santa_librada.html")
Map_modis.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 11. Miniatura PNG estática
# =========================
url_img = modis.getThumbURL({
    'bands': ['sur_refl_b01', 'sur_refl_b04', 'sur_refl_b03'],
    'min': -100,
    'max': 3000,
    'dimensions': 800,
    'region': region_interes
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

# Coordenadas para georreferenciar la imagen PNG
coords = region_interes.coordinates().get(0).getInfo()
xmin = min([c[0] for c in coords])
xmax = max([c[0] for c in coords])
ymin = min([c[1] for c in coords])
ymax = max([c[1] for c in coords])

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

# Grilla de 10 km aprox: 10 km ≈ 0.09 grados
paso_10km = 0.09
lon_grid, lat_grid = (xmin + xmax) / 2, (ymin + ymax) / 2

x_ticks = [lon_grid + (i * paso_10km) for i in range(-5, 6) if xmin <= lon_grid + (i * paso_10km) <= xmax]
y_ticks = [lat_grid + (i * paso_10km) for i in range(-5, 6) if ymin <= lat_grid + (i * paso_10km) <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.2f}°" for x in x_ticks])
ax.set_yticklabels([f"{y:.2f}°" for y in y_ticks])

ax.grid(color='white', linestyle='--', linewidth=0.8, alpha=0.7)
ax.set_title(f"MODIS Color Verdadero - Santa Librada ({fecha})", fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_facecolor('#e0e0e0')

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "modis_santa_librada_rgb.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.11 completada correctamente.")