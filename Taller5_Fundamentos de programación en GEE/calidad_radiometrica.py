import ee
import json
from pathlib import Path

ee.Initialize(project="bamboo-storm-477002-v4")

base_dir = Path("/home/rstudio/work/Clase_Geomatica_gral/Clase_Geomatica_gral/Taller5_Fundamentos de programación en GEE")
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)

# Área de estudio: PNN Los Nevados
punto_nevados = ee.Geometry.Point([-75.321, 4.895])
aoi = punto_nevados.buffer(10000)

# Colección temporal completa
coleccion_s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(aoi)
    .filterDate("2023-01-01", "2023-12-31")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
)

# Función de máscara estricta con SCL
def enmascarar_nubes_s2(img):
    scl = img.select("SCL")
    mascara = (
        scl.neq(3)   # sombra de nube
        .And(scl.neq(8))   # nube prob. media
        .And(scl.neq(9))   # nube prob. alta
        .And(scl.neq(10))  # cirrus
    )
    return img.updateMask(mascara)

# Aplicación iterativa sobre toda la colección
coleccion_limpia = coleccion_s2.map(enmascarar_nubes_s2)

# Reducción estadística temporal
imagen_median = coleccion_limpia.median().clip(aoi)

# Exportación de metadatos
metadatos = imagen_median.getInfo()
with open(data_dir / "03_reto_calidad_radiometrica_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadatos, f, indent=2, ensure_ascii=False)

# Exportación del objeto serializado
serializado = imagen_median.serialize()
with open(data_dir / "03_reto_calidad_radiometrica_serialized.json", "w", encoding="utf-8") as f:
    f.write(serializado)

print("Paso 5 listo")
print("Imágenes en la colección:", coleccion_s2.size().getInfo())
print("Archivo metadata: data/03_reto_calidad_radiometrica_metadata.json")
print("Archivo serialized: data/03_reto_calidad_radiometrica_serialized.json")