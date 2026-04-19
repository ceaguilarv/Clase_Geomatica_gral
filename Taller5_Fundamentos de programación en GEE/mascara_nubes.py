import ee
import json
from pathlib import Path

# =========================================================
# 1. INICIALIZACIÓN
# =========================================================
ee.Initialize(project="bamboo-storm-477002-v4")

# =========================================================
# 2. RUTAS
# =========================================================
base_dir = Path("/home/rstudio/work/Clase_Geomatica_gral/Clase_Geomatica_gral/Taller5_Fundamentos de programación en GEE")
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)

# =========================================================
# 3. ZONA DEL ENUNCIADO
# =========================================================
punto_nevados = ee.Geometry.Point([-75.321, 4.895])

# Buffer pequeño para verificar que sí queden píxeles válidos
zona_control = punto_nevados.buffer(2000)

# Buffer más amplio para exportar el resultado
region_exportacion = punto_nevados.buffer(12000)

# =========================================================
# 4. FUNCIÓN DE MÁSCARA SEGÚN EL TALLER
# =========================================================
def enmascarar_nubes_s2(img):
    scl = img.select("SCL")
    mascara = (
        scl.neq(3)   # sombras de nubes
        .And(scl.neq(8))   # nubes prob. media
        .And(scl.neq(9))   # nubes prob. alta
        .And(scl.neq(10))  # cirrus
    )
    return img.updateMask(mascara)

# =========================================================
# 5. FUNCIÓN DE CONTROL DE VISIBILIDAD
# =========================================================
def agregar_pixeles_validos(img):
    img_limpia = enmascarar_nubes_s2(img)

    conteo = img_limpia.select("B4").reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=zona_control,
        scale=20,
        maxPixels=1e8,
        bestEffort=True
    ).get("B4")

    return img.set("pixeles_validos_centro", conteo)

# =========================================================
# 6. COLECCIÓN BASE DEL ENUNCIADO
# =========================================================
coleccion_base = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(punto_nevados)
    .filterDate("2023-01-01", "2023-12-31")
    .filter(ee.Filter.gt("CLOUDY_PIXEL_PERCENTAGE", 20))
)

# =========================================================
# 7. SELECCIÓN ROBUSTA DE ESCENA
# =========================================================
coleccion_controlada = (
    coleccion_base
    .map(agregar_pixeles_validos)
    .filter(ee.Filter.gt("pixeles_validos_centro", 0))
    .sort("pixeles_validos_centro", False)
)

cantidad = coleccion_controlada.size().getInfo()

if cantidad == 0:
    raise ValueError(
        "No se encontró una imagen de 2023 con nubosidad >20% y píxeles válidos en la zona central después de aplicar la máscara."
    )

img_s2 = ee.Image(coleccion_controlada.first())
img_limpia = enmascarar_nubes_s2(img_s2).clip(region_exportacion)

# =========================================================
# 8. VERIFICACIÓN FINAL
# =========================================================
control_final = img_limpia.select("B4").reduceRegion(
    reducer=ee.Reducer.count(),
    geometry=zona_control,
    scale=20,
    maxPixels=1e8,
    bestEffort=True
).getInfo()

# =========================================================
# 9. EXPORTACIÓN
# =========================================================
metadatos = img_limpia.getInfo()
with open(data_dir / "01_los_nevados_mascara_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadatos, f, indent=2, ensure_ascii=False)

serializado = img_limpia.serialize()
with open(data_dir / "01_los_nevados_mascara_serialized.json", "w", encoding="utf-8") as f:
    f.write(serializado)

# =========================================================
# 10. REPORTE EN CONSOLA
# =========================================================
print("Paso 3 corregido listo")
print("Imágenes candidatas con datos válidos:", cantidad)
print("ID imagen elegida:", img_s2.get("system:id").getInfo())
print("Cloudy Pixel Percentage:", img_s2.get("CLOUDY_PIXEL_PERCENTAGE").getInfo())
print("Pixeles válidos en zona central:", img_s2.get("pixeles_validos_centro").getInfo())
print("Control final reduceRegion:", control_final)
print("Archivo metadata: data/01_los_nevados_mascara_metadata.json")
print("Archivo serialized: data/01_los_nevados_mascara_serialized.json")