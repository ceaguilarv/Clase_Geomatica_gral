# ============================================================
# PROYECTO GEOMÁTICA GENERAL - USME
# Clasificación preliminar 2024 con Landsat 8/9 + Random Forest
# Autor: Carlos Aguilar / Luis Gálvez
# ============================================================

import ee
import geemap


# ============================================================
# 1. INICIALIZAR EARTH ENGINE
# ============================================================

ee.Initialize(project='bamboo-storm-477002-v4')

print("Earth Engine inicializado correctamente.")


# ============================================================
# 2. RUTAS DE ASSETS
# ============================================================

ASSET_ROOT = 'projects/bamboo-storm-477002-v4/assets/usme_geomatica_general'

roi = ee.FeatureCollection(f'{ASSET_ROOT}/area_estudio')


# ============================================================
# 3. FUNCIÓN PARA ASIGNAR CLASE
# ============================================================

def set_class(class_value):
    return lambda f: f.set('class', class_value)


# ============================================================
# 4. CARGAR POLÍGONOS DE ENTRENAMIENTO
# ============================================================
# Leyenda:
# 1 = Vegetación / cobertura agro-natural
# 2 = Urbano / construido
# 3 = Minería de arcilla / actividad ladrillera
# 4 = Suelo desnudo no minero
# 5 = Agua

Vegetacion_poly = ee.FeatureCollection(
    f'{ASSET_ROOT}/vegetacion_poly'
).map(set_class(1))

Urbano_poly = ee.FeatureCollection(
    f'{ASSET_ROOT}/Urbano_poly'
).map(set_class(2))

Mineria_arcilla_poly = ee.FeatureCollection(
    f'{ASSET_ROOT}/mineria_arcilla_poly'
).map(set_class(3))

Suelo_desnudo_poly = ee.FeatureCollection(
    f'{ASSET_ROOT}/suelo_desnudo_poly'
).map(set_class(4))

Agua_poly = ee.FeatureCollection(
    f'{ASSET_ROOT}/agua_poly'
).map(set_class(5))


training_polygons = (
    Vegetacion_poly
    .merge(Urbano_poly)
    .merge(Mineria_arcilla_poly)
    .merge(Suelo_desnudo_poly)
    .merge(Agua_poly)
)


# ============================================================
# 5. CARGAR PUNTOS PUROS DE VALIDACIÓN
# ============================================================

Vegetacion_pts = ee.FeatureCollection(
    f'{ASSET_ROOT}/Vegetacion_pts'
).map(set_class(1))

Urbano_pts = ee.FeatureCollection(
    f'{ASSET_ROOT}/Urbano_pts'
).map(set_class(2))

Mineria_arcilla_pts = ee.FeatureCollection(
    f'{ASSET_ROOT}/mineria_arcilla_pts'
).map(set_class(3))

Suelo_desnudo_pts = ee.FeatureCollection(
    f'{ASSET_ROOT}/Suelo_desnudo_pts'
).map(set_class(4))

Agua_pts = ee.FeatureCollection(
    f'{ASSET_ROOT}/Agua_pts'
).map(set_class(5))


validation_points = (
    Vegetacion_pts
    .merge(Urbano_pts)
    .merge(Mineria_arcilla_pts)
    .merge(Suelo_desnudo_pts)
    .merge(Agua_pts)
)


# ============================================================
# 6. VERIFICAR CARGA DE ASSETS
# ============================================================

print("\n--- VERIFICACIÓN DE ASSETS ---")
print("ROI:", roi.size().getInfo())

print("\n--- POLÍGONOS DE ENTRENAMIENTO ---")
print("Vegetación:", Vegetacion_poly.size().getInfo())
print("Urbano:", Urbano_poly.size().getInfo())
print("Minería arcilla:", Mineria_arcilla_poly.size().getInfo())
print("Suelo desnudo:", Suelo_desnudo_poly.size().getInfo())
print("Agua:", Agua_poly.size().getInfo())
print("Total polígonos:", training_polygons.size().getInfo())

print("\n--- PUNTOS DE VALIDACIÓN ---")
print("Vegetación:", Vegetacion_pts.size().getInfo())
print("Urbano:", Urbano_pts.size().getInfo())
print("Minería arcilla:", Mineria_arcilla_pts.size().getInfo())
print("Suelo desnudo:", Suelo_desnudo_pts.size().getInfo())
print("Agua:", Agua_pts.size().getInfo())
print("Total puntos:", validation_points.size().getInfo())


# ============================================================
# 7. FUNCIÓN PARA PREPROCESAR LANDSAT 8/9 COLLECTION 2 L2
# ============================================================

def mask_landsat_l2(image):
    """
    Enmascara nubes, sombra de nube, nieve y píxeles saturados.
    Aplica factores de escala para reflectancia de superficie.
    """

    qa_pixel = image.select('QA_PIXEL')
    qa_radsat = image.select('QA_RADSAT')

    # Bits QA_PIXEL para Landsat Collection 2 L2
    # bit 1 = dilated cloud
    # bit 2 = cirrus
    # bit 3 = cloud
    # bit 4 = cloud shadow
    # bit 5 = snow

    mask = (
        qa_pixel.bitwiseAnd(1 << 1).eq(0)
        .And(qa_pixel.bitwiseAnd(1 << 2).eq(0))
        .And(qa_pixel.bitwiseAnd(1 << 3).eq(0))
        .And(qa_pixel.bitwiseAnd(1 << 4).eq(0))
        .And(qa_pixel.bitwiseAnd(1 << 5).eq(0))
        .And(qa_radsat.eq(0))
    )

    # Escalado reflectancia Landsat C2 L2
    optical = (
        image.select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'])
        .multiply(0.0000275)
        .add(-0.2)
        .rename(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
    )

    return (
        image.addBands(optical, overwrite=True)
        .updateMask(mask)
        .copyProperties(image, ['system:time_start'])
    )


# ============================================================
# 8. CREAR MOSAICO LANDSAT 2024
# ============================================================

fecha_inicio = '2024-01-01'
fecha_fin = '2024-12-31'

landsat8 = (
    ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(roi)
    .filterDate(fecha_inicio, fecha_fin)
    .map(mask_landsat_l2)
)

landsat9 = (
    ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
    .filterBounds(roi)
    .filterDate(fecha_inicio, fecha_fin)
    .map(mask_landsat_l2)
)

landsat_2024 = landsat8.merge(landsat9)

print("\nCantidad imágenes Landsat 8/9 2024:", landsat_2024.size().getInfo())


mosaico_2024 = (
    landsat_2024
    .median()
    .clip(roi)
)


# ============================================================
# 9. CALCULAR ÍNDICES ESPECTRALES
# ============================================================

ndvi = mosaico_2024.normalizedDifference(
    ['NIR', 'Red']
).rename('NDVI')

ndbi = mosaico_2024.normalizedDifference(
    ['SWIR1', 'NIR']
).rename('NDBI')

bsi = mosaico_2024.expression(
    '((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))',
    {
        'SWIR1': mosaico_2024.select('SWIR1'),
        'RED': mosaico_2024.select('Red'),
        'NIR': mosaico_2024.select('NIR'),
        'BLUE': mosaico_2024.select('Blue')
    }
).rename('BSI')


imagen_2024 = (
    mosaico_2024
    .select(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
    .addBands(ndvi)
    .addBands(ndbi)
    .addBands(bsi)
)


bandas = [
    'Blue',
    'Green',
    'Red',
    'NIR',
    'SWIR1',
    'SWIR2',
    'NDVI',
    'NDBI',
    'BSI'
]

print("\nBandas usadas:", imagen_2024.bandNames().getInfo())


# ============================================================
# 10. EXTRAER MUESTRAS DE ENTRENAMIENTO DESDE POLÍGONOS
# ============================================================

training = imagen_2024.sampleRegions(
    collection=training_polygons,
    properties=['class'],
    scale=30,
    geometries=False,
    tileScale=4
)

print("\nTotal píxeles de entrenamiento:", training.size().getInfo())
print("Muestras por clase:")
print(training.aggregate_histogram('class').getInfo())


# ============================================================
# 11. ENTRENAR RANDOM FOREST
# ============================================================

classifier_rf = ee.Classifier.smileRandomForest(
    numberOfTrees=200,
    variablesPerSplit=None,
    minLeafPopulation=1,
    bagFraction=0.7,
    seed=42
).train(
    features=training,
    classProperty='class',
    inputProperties=bandas
)

print("\nRandom Forest entrenado correctamente.")


# ============================================================
# 12. CLASIFICAR IMAGEN 2024
# ============================================================

clasificacion_2024 = imagen_2024.classify(classifier_rf).rename('classification')

print("Clasificación 2024 generada.")


# ============================================================
# 13. VALIDACIÓN CON PUNTOS PUROS
# ============================================================

validation_sample = imagen_2024.sampleRegions(
    collection=validation_points,
    properties=['class'],
    scale=30,
    geometries=True,
    tileScale=4
)

validated = validation_sample.classify(classifier_rf)

confusion_matrix = validated.errorMatrix(
    'class',
    'classification'
)

print("\n--- VALIDACIÓN CON PUNTOS PUROS ---")
print("Matriz de confusión:")
print(confusion_matrix.getInfo())

print("\nExactitud global:")
print(confusion_matrix.accuracy().getInfo())

print("\nKappa:")
print(confusion_matrix.kappa().getInfo())

print("\nPrecisión del productor por clase:")
print(confusion_matrix.producersAccuracy().getInfo())

print("\nPrecisión del usuario por clase:")
print(confusion_matrix.consumersAccuracy().getInfo())


# ============================================================
# 14. IMPORTANCIA DE VARIABLES
# ============================================================

importance = ee.Dictionary(classifier_rf.explain().get('importance'))

print("\n--- IMPORTANCIA DE VARIABLES ---")
print(importance.getInfo())


# ============================================================
# 15. CALCULAR ÁREA POR CLASE
# ============================================================

area_image = ee.Image.pixelArea().divide(10000).addBands(clasificacion_2024)

areas = area_image.reduceRegion(
    reducer=ee.Reducer.sum().group(
        groupField=1,
        groupName='class'
    ),
    geometry=roi.geometry(),
    scale=30,
    maxPixels=1e13,
    tileScale=4
)

print("\n--- ÁREA POR CLASE EN HECTÁREAS ---")
print(areas.getInfo())


# ============================================================
# 16. VISUALIZACIÓN EN GEEMAP
# ============================================================

Map = geemap.Map()

Map.centerObject(roi, 11)

# RGB Landsat
Map.addLayer(
    imagen_2024,
    {
        'bands': ['Red', 'Green', 'Blue'],
        'min': 0.02,
        'max': 0.3
    },
    'Landsat RGB 2024'
)

# Falso color
Map.addLayer(
    imagen_2024,
    {
        'bands': ['NIR', 'Red', 'Green'],
        'min': 0.02,
        'max': 0.4
    },
    'Falso color 2024'
)

# Clasificación
Map.addLayer(
    clasificacion_2024,
    {
        'min': 1,
        'max': 5,
        'palette': [
            '00aa00',  # 1 Vegetación
            'ff0000',  # 2 Urbano
            '808080',  # 3 Minería arcilla
            'ffff00',  # 4 Suelo desnudo
            '0000ff'   # 5 Agua
        ]
    },
    'Clasificación RF 2024'
)

# Área de estudio
Map.addLayer(
    roi,
    {},
    'Área de estudio'
)

# Polígonos
Map.addLayer(Vegetacion_poly, {'color': '00aa00'}, 'Poly Vegetación')
Map.addLayer(Urbano_poly, {'color': 'ff0000'}, 'Poly Urbano')
Map.addLayer(Mineria_arcilla_poly, {'color': '808080'}, 'Poly Minería arcilla')
Map.addLayer(Suelo_desnudo_poly, {'color': 'ffff00'}, 'Poly Suelo desnudo')
Map.addLayer(Agua_poly, {'color': '0000ff'}, 'Poly Agua')

# Puntos de validación
Map.addLayer(Vegetacion_pts, {'color': '00ff00'}, 'Pts Vegetación')
Map.addLayer(Urbano_pts, {'color': 'ff5555'}, 'Pts Urbano')
Map.addLayer(Mineria_arcilla_pts, {'color': '555555'}, 'Pts Minería arcilla')
Map.addLayer(Suelo_desnudo_pts, {'color': 'ffaa00'}, 'Pts Suelo desnudo')
Map.addLayer(Agua_pts, {'color': '5555ff'}, 'Pts Agua')

Map.addLayerControl()

Map


# ============================================================
# 17. EXPORTAR CLASIFICACIÓN A GOOGLE DRIVE
# ============================================================

export_task = ee.batch.Export.image.toDrive(
    image=clasificacion_2024.toByte(),
    description='RF_Usme_2024_Landsat',
    folder='GEE_USME_GEOMATICA',
    fileNamePrefix='RF_Usme_2024_Landsat',
    region=roi.geometry(),
    scale=30,
    maxPixels=1e13
)

export_task.start()

print("\nTarea de exportación iniciada.")
print("Revisa la pestaña Tasks en GEE o tu Google Drive en la carpeta GEE_USME_GEOMATICA.")