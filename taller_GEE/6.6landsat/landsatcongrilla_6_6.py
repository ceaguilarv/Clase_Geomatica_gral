import ee
import requests
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

ee.Initialize(project='bamboo-storm-477002-v4')

lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])
region_interes = punto_estudio.buffer(3000)

l9_estatica = (
    ee.ImageCollection("LANDSAT/LC09/C02/T1_TOA")
    .filterBounds(punto_estudio)
    .filterDate('2023-01-01', '2023-12-31')
    .sort('CLOUD_COVER')
    .first()
)

url_img = l9_estatica.getThumbURL({
    'bands': ['B4', 'B3', 'B2'],
    'min': 0.0,
    'max': 0.3,
    'dimensions': 800,
    'region': region_interes
})

print("URL miniatura:", url_img)

respuesta = requests.get(url_img)
print("Status HTTP:", respuesta.status_code)

imagen_png = Image.open(BytesIO(respuesta.content))

coords = region_interes.bounds().coordinates().get(0).getInfo()
xmin, ymin = coords[0][0], coords[0][1]
xmax, ymax = coords[2][0], coords[2][1]

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(imagen_png, extent=[xmin, xmax, ymin, ymax])

paso_1km = 0.009
x_ticks = [lon_centro + (i * paso_1km) for i in range(-4, 5)]
y_ticks = [lat_centro + (i * paso_1km) for i in range(-4, 5)]
x_ticks = [x for x in x_ticks if xmin <= x <= xmax]
y_ticks = [y for y in y_ticks if ymin <= y <= ymax]

ax.set_xticks(x_ticks)
ax.set_yticks(y_ticks)
ax.set_xticklabels([f"{x:.3f}°" for x in x_ticks], rotation=45)
ax.set_yticklabels([f"{y:.3f}°" for y in y_ticks])

ax.grid(color='white', linestyle='--', linewidth=0.8, alpha=0.7)
ax.set_title('Landsat 9 Color Verdadero - Santa Librada')
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')

plt.tight_layout()

salida = "/home/rstudio/work/landsat9_santa_librada_grilla.png"
plt.savefig(salida, dpi=200, bbox_inches='tight')
print("Imagen guardada en:", salida)