import ee
import folium
import json
import os
import requests
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
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

# Región enfocada en Santa Librada
region_interes = punto_estudio.buffer(5000)

# =========================
# 4. Cargar colección Sentinel-2
# =========================
coleccion_s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(region_interes)
    .filterDate('2023-01-01', '2023-12-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
    .select(['B8', 'B4', 'B3', 'B2'])
)

cantidad = coleccion_s2.size().getInfo()
print("Número de imágenes usadas en el composite:", cantidad)

# =========================
# 5. Crear composite SIN clip
# =========================
composite_s2 = coleccion_s2.median()

# NDVI calculado sobre el composite
ndvi = composite_s2.normalizedDifference(['B8', 'B4']).rename('NDVI')

# =========================
# 6. Guardar metadatos básicos
# =========================
info_basica = {
    "coleccion": "COPERNICUS/S2_SR_HARMONIZED",
    "imagenes_usadas": cantidad,
    "metodo_composite": "median",
    "region_centro": {
        "latitud": lat_centro,
        "longitud": lon_centro
    },
    "fecha_inicio": "2023-01-01",
    "fecha_fin": "2023-12-31",
    "filtro_nubosidad": "< 15%"
}

ruta_meta = os.path.join(carpeta_salida, "metadatos_ndvi_composite_santa_librada.json")
with open(ruta_meta, "w", encoding="utf-8") as archivo:
    json.dump(info_basica, archivo, indent=4, ensure_ascii=False)

# =========================
# 7. Guardar serializado del NDVI
# =========================
texto_json_serializado = ndvi.serialize()
ruta_ser = os.path.join(carpeta_salida, "ndvi_composite_santa_librada_serializado.json")
with open(ruta_ser, "w", encoding="utf-8") as archivo:
    json.dump(texto_json_serializado, archivo)

print("Metadatos guardados en:", ruta_meta)
print("Serializado guardado en:", ruta_ser)

# =========================
# 8. Visualización HTML
# =========================
vis_ndvi = {
    'min': -0.1,
    'max': 0.8,
    'palette': ['blue', 'white', 'green']
}

map_id_dict = ee.Image(ndvi).getMapId(vis_ndvi)

Map_ndvi = folium.Map(
    location=[lat_centro, lon_centro],
    zoom_start=14,
    tiles='OpenStreetMap'
)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='NDVI Composite Santa Librada'
).add_to(Map_ndvi)

coords = region_interes.bounds().coordinates().get(0).getInfo()
xmin = min([c[0] for c in coords])
xmax = max([c[0] for c in coords])
ymin = min([c[1] for c in coords])
ymax = max([c[1] for c in coords])

Map_ndvi.fit_bounds([[ymin, xmin], [ymax, xmax]])
folium.LayerControl().add_to(Map_ndvi)

ruta_html = os.path.join(carpeta_salida, "map_ndvi_composite_santa_librada.html")
Map_ndvi.save(ruta_html)
print("Mapa HTML guardado en:", ruta_html)

# =========================
# 9. PNG estático
# =========================
url_img = ndvi.getThumbURL({
    'min': -0.1,
    'max': 0.8,
    'palette': ['blue', 'white', 'green'],
    'dimensions': 800,
    'region': region_interes
})

respuesta = requests.get(url_img)
respuesta.raise_for_status()
imagen_png = Image.open(BytesIO(respuesta.content))

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

# Grilla ~1 km
paso_1km = 0.009
x_ticks = [lon_centro + (i * paso_1km) for i in range(-6, 7)]
y_ticks = [lat_centro + (i * paso_1km) for i in range(-6, 7)]

x_ticks = [x for x in x_ticks if xmin <= x <= xmax]
y_ticks = [y for y in y_ticks if ymin <= y <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.3f}°" for x in x_ticks], rotation=45)
ax.set_yticklabels([f"{y:.3f}°" for y in y_ticks])

ax.grid(color='black', linestyle='--', linewidth=0.5, alpha=0.3)
ax.set_title('NDVI Composite Sentinel-2 - Santa Librada (2023)', fontsize=14)
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')

cmap_custom = LinearSegmentedColormap.from_list("ndvi", ['blue', 'white', 'green'])
norm = Normalize(vmin=-0.1, vmax=0.8)
fig.colorbar(
    ScalarMappable(norm=norm, cmap=cmap_custom),
    ax=ax,
    shrink=0.7
).set_label('Valor NDVI')

plt.tight_layout()
ruta_png = os.path.join(carpeta_salida, "ndvi_composite_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("PNG guardado en:", ruta_png)
print("\nSección 6.19 completada correctamente.")