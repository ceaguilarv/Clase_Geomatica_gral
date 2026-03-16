import ee
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import urllib.request
from PIL import Image
import numpy as np
import os

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
# 3. Definición del área
# =========================
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])

# Área pequeña para medir NDVI local
area_estudio = punto_estudio.buffer(1500)

# Área un poco más amplia para asegurar buena cobertura al buscar imágenes
area_busqueda = punto_estudio.buffer(8000)

# =========================
# 4. Colección Sentinel-2 para serie temporal
# =========================
s2_ts = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(area_busqueda)
    .filterDate('2023-01-01', '2023-12-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
    .select(['B8', 'B4', 'B3', 'B2'])
)

cantidad = s2_ts.size().getInfo()
print("Número de imágenes en la serie temporal:", cantidad)

# =========================
# 5. Añadir NDVI a cada imagen
# =========================
def add_ndvi(img):
    ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return img.addBands(ndvi).copyProperties(img, ['system:time_start'])

s2_ndvi = s2_ts.map(add_ndvi)

# =========================
# 6. Extraer NDVI medio por fecha
# =========================
def extract_ndvi(img):
    mean_dict = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=area_estudio,
        scale=10,
        maxPixels=1e9
    )
    return ee.Feature(None, {
        'NDVI': mean_dict.get('NDVI'),
        'system:time_start': img.get('system:time_start')
    })

ndvi_features = ee.FeatureCollection(
    s2_ndvi.map(extract_ndvi)
).filter(ee.Filter.notNull(['NDVI']))

ndvi_list = ndvi_features.reduceColumns(
    ee.Reducer.toList(2),
    ['system:time_start', 'NDVI']
).get('list').getInfo()

df = pd.DataFrame(ndvi_list, columns=['Time', 'NDVI'])
df['Time'] = pd.to_datetime(df['Time'], unit='ms')
df = df.sort_values('Time')

print(df.head())
print(f"Total de observaciones válidas: {len(df)}")

# =========================
# 7. Guardar CSV
# =========================
ruta_csv = os.path.join(carpeta_salida, "serie_ndvi_santa_librada.csv")
df.to_csv(ruta_csv, index=False)
print("CSV guardado en:", ruta_csv)

# =========================
# 8. Figura principal: curva temporal
# =========================
fig = plt.figure(figsize=(12, 10))
ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2)

ax1.plot(df['Time'], df['NDVI'], marker='o', linewidth=2)
ax1.set_title('Serie temporal NDVI - Santa Librada (2023)')
ax1.set_xlabel('Fecha')
ax1.set_ylabel('NDVI medio')
ax1.grid(True, linestyle='--', alpha=0.6)

# =========================
# 9. Filmstrip de 5 fechas
# =========================
n_thumbs = 5
img_list = s2_ts.sort('system:time_start').toList(n_thumbs)
count = img_list.size().getInfo()

for i in range(min(n_thumbs, count)):
    img = ee.Image(img_list.get(i))
    fecha_ms = img.get('system:time_start').getInfo()
    fecha = datetime.datetime.fromtimestamp(
        fecha_ms / 1000.0, datetime.UTC
    ).strftime('%Y-%m-%d')

    thumb_url = img.getThumbURL({
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000,
        'dimensions': 300,
        'region': area_estudio.bounds(),
        'format': 'png'
    })

    with urllib.request.urlopen(thumb_url) as url_response:
        img_array = np.array(Image.open(url_response))

    ax_thumb = plt.subplot2grid((3, n_thumbs), (2, i))
    ax_thumb.imshow(img_array)
    ax_thumb.set_title(fecha, fontsize=9)
    ax_thumb.axis('off')

plt.tight_layout()

ruta_png = os.path.join(carpeta_salida, "serie_temporal_ndvi_santa_librada.png")
plt.savefig(ruta_png, dpi=200, bbox_inches='tight')
plt.close()

print("Figura guardada en:", ruta_png)
print("\nSección 6.20 completada correctamente.")