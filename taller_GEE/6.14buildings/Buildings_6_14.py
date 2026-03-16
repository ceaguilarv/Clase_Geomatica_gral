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
# 3. Punto y región de interés
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])
region_interes = punto_estudio.buffer(3000)

# =========================
# 4. Carga de la colección vectorial
# =========================
buildings = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons") \
    .filterBounds(region_interes)

id_exacto = "GOOGLE/Research/open-buildings/v3/polygons"
print(f"\nID de la colección vectorial seleccionada: {id_exacto}")

# =========================
# 5. Guardar metadatos
# =========================
metadatos_json = buildings.limit(1).getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_buildings_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 6. Guardar serializado
# =========================
texto_json_serializado = buildings.serialize()
ruta_ser = os.path.join(carpeta_salida, "buildings_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 7. Visualización interactiva en Folium
# =========================
vis_params = {'color': 'FF0000'}
map_id_dict = buildings.getMapId(vis_params)

Map_bld = folium.Map(location=[lat_centro, lon_centro], zoom_start=17)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='Edificios Santa Librada'
).add_to(Map_bld)

folium.LayerControl().add_to(Map_bld)

ruta_html = os.path.join(carpeta_salida, "map_buildings_santa_librada.html")
Map_bld.save(ruta_html)

print("\n✅ MAPA VECTORIAL GENERADO CON ÉXITO")
print("Capa desplegada : Edificios Santa Librada")
print("Mapa HTML guardado en:", ruta_html)

# =========================
# 8. Rasterizar para PNG estático
# =========================
imagen_vacia = ee.Image().byte()
edificios_raster = imagen_vacia.paint(buildings, 1, 2)

url_img = edificios_raster.getThumbURL({
    'palette': ['red'],
    'min': 1,
    'max': 1,
    'dimensions': 800,
    'region': region_interes,
    'format': 'png'
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

coords = region_interes.bounds().coordinates().get(0).getInfo()
xmin, ymin = coords[0][0], coords[0][1]
xmax, ymax = coords[2][0], coords[2][1]

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

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

ax.grid(color='gray', linestyle='--', linewidth=1, alpha=0.7)
ax.set_title('Edificios Santa Librada (Vector, Grilla ~1 km)', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.set_facecolor('#f0f0f0')

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "buildings_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.14 completada correctamente.")