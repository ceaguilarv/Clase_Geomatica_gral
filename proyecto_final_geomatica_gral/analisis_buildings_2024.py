# ============================================================
# ANÁLISIS AUXILIAR BUILDINGS 2024
# Proyecto Geomática General - Usme
# Compara clasificación RF 2024 con edificaciones 2024
# ============================================================

import ee

ee.Initialize(project='bamboo-storm-477002-v4')

print("Earth Engine inicializado correctamente.")


# ============================================================
# 1. RUTAS
# ============================================================

ASSET_ROOT = 'projects/bamboo-storm-477002-v4/assets/usme_geomatica_general'

roi = ee.FeatureCollection(f'{ASSET_ROOT}/area_estudio')

# Cambia este nombre si tu Asset quedó con otro nombre
buildings = ee.FeatureCollection(f'{ASSET_ROOT}/buildings_2024_usme')


# ============================================================
# 2. CARGAR CLASIFICACIÓN RF 2024
# ============================================================
# Este raster es el que se exportó a Drive.

clasificacion_2024 = ee.Image(
    f'{ASSET_ROOT}/RF_Usme_2024_Landsat'
)

# Leyenda del raster:
# 1 = Vegetación
# 2 = Urbano
# 3 = Minería arcilla / actividad ladrillera
# 4 = Suelo desnudo
# 5 = Agua


# ============================================================
# 3. PREPARAR BUILDINGS
# ============================================================

buildings_usme = buildings.filterBounds(roi)

print("Número de polígonos de edificios en Usme:", buildings_usme.size().getInfo())


# Buffer de edificios.
# Como Landsat trabaja a 30 m, se usa un buffer de 15 m o 30 m.
# 15 m = más conservador
# 30 m = más flexible para coincidir con píxel Landsat

buffer_m = 30

buildings_buffer = buildings_usme.map(
    lambda f: ee.Feature(f).buffer(buffer_m)
)


# Rasterizar buildings:
# 1 = presencia de edificio/buffer
# 0 = ausencia

buildings_raster = (
    ee.Image(0)
    .byte()
    .paint(
        featureCollection=buildings_buffer,
        color=1
    )
    .unmask(0)
    .rename('buildings')
    .clip(roi)
)


# ============================================================
# 4. CREAR MÁSCARAS DE CLASES
# ============================================================

urbano = clasificacion_2024.eq(2).selfMask().rename('urbano')
mineria = clasificacion_2024.eq(3).selfMask().rename('mineria')
suelo_desnudo = clasificacion_2024.eq(4).selfMask().rename('suelo_desnudo')

hay_building = buildings_raster.eq(1).selfMask().rename('hay_building')
sin_building = buildings_raster.eq(0).selfMask().rename('sin_building')


# Coincidencias
urbano_con_building = urbano.And(hay_building).rename('urbano_con_building')
urbano_sin_building = urbano.And(sin_building).rename('urbano_sin_building')

mineria_con_building = mineria.And(hay_building).rename('mineria_con_building')
mineria_sin_building = mineria.And(sin_building).rename('mineria_sin_building')

suelo_desnudo_con_building = suelo_desnudo.And(hay_building).rename('suelo_desnudo_con_building')


# ============================================================
# 5. FUNCIÓN PARA CALCULAR ÁREA
# ============================================================

def calcular_area_ha(mask_image, nombre):
    area = (
        ee.Image.pixelArea()
        .divide(10000)
        .updateMask(mask_image)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi.geometry(),
            scale=30,
            maxPixels=1e13,
            tileScale=4
        )
    )

    valor = area.getInfo().get('area')

    if valor is None:
        valor = 0

    print(f"{nombre}: {valor:.2f} ha")
    return valor


print("\n--- ÁREAS DE COHERENCIA URBANA 2024 ---")

area_urbano_total = calcular_area_ha(urbano, "Urbano total clasificado")
area_urbano_con_building = calcular_area_ha(urbano_con_building, "Urbano con buildings")
area_urbano_sin_building = calcular_area_ha(urbano_sin_building, "Urbano sin buildings")

area_mineria_total = calcular_area_ha(mineria, "Minería total clasificada")
area_mineria_con_building = calcular_area_ha(mineria_con_building, "Minería con buildings")
area_mineria_sin_building = calcular_area_ha(mineria_sin_building, "Minería sin buildings")

area_suelo_desnudo_total = calcular_area_ha(suelo_desnudo, "Suelo desnudo total clasificado")
area_suelo_desnudo_con_building = calcular_area_ha(
    suelo_desnudo_con_building,
    "Suelo desnudo con buildings"
)


# ============================================================
# 6. PORCENTAJES
# ============================================================

print("\n--- PORCENTAJES ---")

if area_urbano_total > 0:
    print(
        "Porcentaje urbano con buildings:",
        round((area_urbano_con_building / area_urbano_total) * 100, 2),
        "%"
    )

    print(
        "Porcentaje urbano sin buildings:",
        round((area_urbano_sin_building / area_urbano_total) * 100, 2),
        "%"
    )

if area_mineria_total > 0:
    print(
        "Porcentaje minería con buildings:",
        round((area_mineria_con_building / area_mineria_total) * 100, 2),
        "%"
    )

    print(
        "Porcentaje minería sin buildings:",
        round((area_mineria_sin_building / area_mineria_total) * 100, 2),
        "%"
    )


# ============================================================
# 7. EXPORTAR CAPAS AUXILIARES A DRIVE
# ============================================================

# Mapa de coherencia:
# 1 = urbano con buildings
# 2 = urbano sin buildings
# 3 = minería con buildings
# 4 = minería sin buildings
# 5 = suelo desnudo con buildings

coherencia = (
    ee.Image(0)
    .where(urbano_con_building, 1)
    .where(urbano_sin_building, 2)
    .where(mineria_con_building, 3)
    .where(mineria_sin_building, 4)
    .where(suelo_desnudo_con_building, 5)
    .rename('coherencia_buildings_2024')
    .clip(roi)
)

task = ee.batch.Export.image.toDrive(
    image=coherencia.toByte(),
    description='Coherencia_Buildings_RF_Usme_2024',
    folder='GEE_USME_GEOMATICA',
    fileNamePrefix='Coherencia_Buildings_RF_Usme_2024',
    region=roi.geometry(),
    scale=30,
    maxPixels=1e13
)

task.start()

print("\nExportación iniciada:")
print("Coherencia_Buildings_RF_Usme_2024")
print("Carpeta Drive: GEE_USME_GEOMATICA")