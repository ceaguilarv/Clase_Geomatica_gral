import ee
import json

ee.Initialize(project='bamboo-storm-477002-v4')

# 1. Punto de estudio: Santa Librada, Usme
lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])
area_estudio = punto_estudio.buffer(1500)

# 2. Función para obtener la mejor imagen Sentinel-2 de un año
def obtener_imagen_s2(anio):
    inicio = f'{anio}-01-01'
    fin = f'{anio}-12-31'
    
    coleccion = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area_estudio)
        .filterDate(inicio, fin)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
        .sort('CLOUDY_PIXEL_PERCENTAGE')
    )
    
    imagen = ee.Image(coleccion.first())
    return imagen

# 3. Elegir dos años de comparación
img_2020 = obtener_imagen_s2(2020)
img_2024 = obtener_imagen_s2(2024)

# 4. Calcular NDVI para cada fecha
ndvi_2020 = img_2020.normalizedDifference(['B8', 'B4']).rename('NDVI_2020')
ndvi_2024 = img_2024.normalizedDifference(['B8', 'B4']).rename('NDVI_2024')

# 5. Diferencia de NDVI
delta_ndvi = ndvi_2024.subtract(ndvi_2020).rename('Delta_NDVI')

# 6. Imprimir información de las imágenes elegidas
id_2020 = img_2020.get('system:id').getInfo()
fecha_2020 = ee.Date(img_2020.get('system:time_start')).format('YYYY-MM-dd').getInfo()
nubes_2020 = img_2020.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()

id_2024 = img_2024.get('system:id').getInfo()
fecha_2024 = ee.Date(img_2024.get('system:time_start')).format('YYYY-MM-dd').getInfo()
nubes_2024 = img_2024.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()

print("=== Imagen inicial ===")
print("ID:", id_2020)
print("Fecha:", fecha_2020)
print("Nubosidad:", nubes_2020)

print("\n=== Imagen final ===")
print("ID:", id_2024)
print("Fecha:", fecha_2024)
print("Nubosidad:", nubes_2024)

# 7. Guardar serializado de la diferencia NDVI
serializado_delta = ee.serializer.encode(delta_ndvi)
with open("/home/rstudio/work/delta_ndvi_santa_librada_2020_2024.json", "w", encoding="utf-8") as f:
    json.dump(serializado_delta, f, indent=2, ensure_ascii=False)

print("\nArchivo generado: /home/rstudio/work/delta_ndvi_santa_librada_2020_2024.json")