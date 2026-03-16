import ee
import folium
import json
import os
import requests
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, LinearSegmentedColormap
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
# 4. Colección WorldPop
# =========================
coleccion_wp = (
    ee.ImageCollection("WorldPop/GP/100m/pop")
    .filterBounds(punto_estudio)
    .filter(ee.Filter.eq('country', 'COL'))
)

worldpop = ee.Image(coleccion_wp.first()).clip(region_interes)

id_exacto = worldpop.get('system:id').getInfo()
print(f"\nID de la imagen WorldPop seleccionada: {id_exacto}")

# =========================
# 5. Guardar metadatos
# =========================
metadatos_json = worldpop.getInfo()
ruta_meta = os.path.join(carpeta_salida, "metadatos_worldpop_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(metadatos_json, archivo, indent=4, ensure_ascii=False)

# =========================
# 6. Guardar serializado
# =========================
worldpop_limpia = ee.Image(id_exacto).clip(region_interes)
texto_json_serializado = worldpop_limpia.serialize()
ruta_ser = os.path.join(carpeta_salida, "worldpop_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 7. Parámetros de visualización
# =========================
vis_params = {
    'bands': ['population'],
    'min': 0,
    'max': 100,
    'palette': ['white', 'yellow', 'red']
}
map_id_dict = ee.Image(worldpop).getMapId(vis_params)

# =========================
# 8. Mapa HTML interactivo
# =========================
Map_pop = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='Población WorldPop'
).add_to(Map_pop)

folium.LayerControl().add_to(Map_pop)

ruta_html = os.path.join(carpeta_salida, "map_worldpop_santa_librada.html")
Map_pop.save(ruta_html)

print("Mapa HTML guardado en:", ruta_html)

# =========================
# 9. PNG estático
# =========================
url_img = worldpop.getThumbURL({
    'bands': ['population'],
    'min': 0,
    'max': 100,
    'palette': ['white', 'yellow', 'red'],
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
ax.set_title('Población WorldPop - Santa Librada (100 m, Grilla ~1 km)', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')

# Barra de color
cmap = LinearSegmentedColormap.from_list("worldpop", ['white', 'yellow', 'red'])
norm = Normalize(vmin=0, vmax=100)
sm = ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Población estimada por píxel")

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "worldpop_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.17 completada correctamente.")