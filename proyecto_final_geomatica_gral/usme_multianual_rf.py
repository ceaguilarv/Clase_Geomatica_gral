# ============================================================
# PROYECTO FINAL GEOMÁTICA GENERAL - USME
# Análisis multitemporal de la expansión minera asociada
# a extracción de arcilla y actividad ladrillera
#
# Google Earth Engine + Python
# Clasificación supervisada Random Forest
# Periodo: 1990, 1995, 2000, 2010, 2015, 2020, 2024
# ============================================================

import ee
import geemap


# ============================================================
# 1. INICIALIZAR EARTH ENGINE
# ============================================================

ee.Initialize(project='bamboo-storm-477002-v4')

print("Earth Engine inicializado correctamente.")


# ============================================================
# 2. CONFIGURACIÓN GENERAL
# ============================================================

ASSET_ROOT = 'projects/bamboo-storm-477002-v4/assets/usme_geomatica_general'

ANIOS = [1990, 1995, 2000, 2010, 2015, 2020, 2024]

# Se balancea con base en la clase minoritaria observada en 2024.
# No se inventan muestras adicionales.
N_POR_CLASE = 144

BANDAS = [
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

LEYENDA = {
    1: 'Vegetacion_agro_natural',
    2: 'Urbano_construido',
    3: 'Mineria_arcilla_ladrillera',
    4: 'Suelo_desnudo_no_minero',
    5: 'Agua'
}


# ============================================================
# 3. CARGAR ASSETS
# ============================================================

roi = ee.FeatureCollection(f'{ASSET_ROOT}/area_estudio')


def set_class(class_value):
    return lambda f: ee.Feature(f).set('class', class_value)


# ------------------------------------------------------------
# Polígonos de entrenamiento
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Puntos puros de validación
# ------------------------------------------------------------

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
# 4. VERIFICACIÓN INICIAL DE ASSETS
# ============================================================

print("\n--- VERIFICACIÓN DE ASSETS ---")
print("ROI:", roi.size().getInfo())

print("\nPolígonos de entrenamiento:")
print("Vegetación:", Vegetacion_poly.size().getInfo())
print("Urbano:", Urbano_poly.size().getInfo())
print("Minería arcilla:", Mineria_arcilla_poly.size().getInfo())
print("Suelo desnudo:", Suelo_desnudo_poly.size().getInfo())
print("Agua:", Agua_poly.size().getInfo())
print("Total polígonos:", training_polygons.size().getInfo())

print("\nPuntos de validación:")
print("Vegetación:", Vegetacion_pts.size().getInfo())
print("Urbano:", Urbano_pts.size().getInfo())
print("Minería arcilla:", Mineria_arcilla_pts.size().getInfo())
print("Suelo desnudo:", Suelo_desnudo_pts.size().getInfo())
print("Agua:", Agua_pts.size().getInfo())
print("Total puntos:", validation_points.size().getInfo())


# ============================================================
# 5. FUNCIONES LANDSAT
# ============================================================

def mask_landsat_l2(image):
    """
    Máscara para Landsat Collection 2 Level 2.
    Enmascara nubes, cirros, sombra de nube, nieve y saturación radiométrica.
    """

    image = ee.Image(image)

    qa_pixel = image.select('QA_PIXEL')
    qa_radsat = image.select('QA_RADSAT')

    mask = (
        qa_pixel.bitwiseAnd(1 << 1).eq(0)  # dilated cloud
        .And(qa_pixel.bitwiseAnd(1 << 2).eq(0))  # cirrus
        .And(qa_pixel.bitwiseAnd(1 << 3).eq(0))  # cloud
        .And(qa_pixel.bitwiseAnd(1 << 4).eq(0))  # cloud shadow
        .And(qa_pixel.bitwiseAnd(1 << 5).eq(0))  # snow
        .And(qa_radsat.eq(0))  # saturated pixels
    )

    return image.updateMask(mask).copyProperties(
        image,
        ['system:time_start']
    )


def prep_landsat_57(image):
    """
    Preprocesamiento para Landsat 5 TM y Landsat 7 ETM+.
    Renombra bandas a nombres comunes.
    """

    image = ee.Image(image)
    image = mask_landsat_l2(image)

    optical = (
        image.select([
            'SR_B1',
            'SR_B2',
            'SR_B3',
            'SR_B4',
            'SR_B5',
            'SR_B7'
        ])
        .multiply(0.0000275)
        .add(-0.2)
        .rename([
            'Blue',
            'Green',
            'Red',
            'NIR',
            'SWIR1',
            'SWIR2'
        ])
    )

    return optical.copyProperties(
        image,
        ['system:time_start']
    )


def prep_landsat_89(image):
    """
    Preprocesamiento para Landsat 8 OLI y Landsat 9 OLI-2.
    Renombra bandas a nombres comunes.
    """

    image = ee.Image(image)
    image = mask_landsat_l2(image)

    optical = (
        image.select([
            'SR_B2',
            'SR_B3',
            'SR_B4',
            'SR_B5',
            'SR_B6',
            'SR_B7'
        ])
        .multiply(0.0000275)
        .add(-0.2)
        .rename([
            'Blue',
            'Green',
            'Red',
            'NIR',
            'SWIR1',
            'SWIR2'
        ])
    )

    return optical.copyProperties(
        image,
        ['system:time_start']
    )


def agregar_indices(image):
    """
    Agrega NDVI, NDBI y BSI.
    """

    image = ee.Image(image)

    ndvi = image.normalizedDifference(
        ['NIR', 'Red']
    ).rename('NDVI')

    ndbi = image.normalizedDifference(
        ['SWIR1', 'NIR']
    ).rename('NDBI')

    bsi = image.expression(
        '((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))',
        {
            'SWIR1': image.select('SWIR1'),
            'RED': image.select('Red'),
            'NIR': image.select('NIR'),
            'BLUE': image.select('Blue')
        }
    ).rename('BSI')

    return image.addBands(ndvi).addBands(ndbi).addBands(bsi)


def coleccion_landsat_por_anio(anio):
    """
    Selecciona y preprocesa la colección Landsat correspondiente para cada año.
    Se mantiene Landsat como fuente principal para toda la serie.
    """

    fecha_inicio = f'{anio}-01-01'
    fecha_fin = f'{anio}-12-31'

    def procesar_l57(img):
        img = ee.Image(img)

        qa_pixel = img.select('QA_PIXEL')
        qa_radsat = img.select('QA_RADSAT')

        mask = (
            qa_pixel.bitwiseAnd(1 << 1).eq(0)
            .And(qa_pixel.bitwiseAnd(1 << 2).eq(0))
            .And(qa_pixel.bitwiseAnd(1 << 3).eq(0))
            .And(qa_pixel.bitwiseAnd(1 << 4).eq(0))
            .And(qa_pixel.bitwiseAnd(1 << 5).eq(0))
            .And(qa_radsat.eq(0))
        )

        optical = (
            img.select([
                'SR_B1',
                'SR_B2',
                'SR_B3',
                'SR_B4',
                'SR_B5',
                'SR_B7'
            ])
            .multiply(0.0000275)
            .add(-0.2)
            .rename([
                'Blue',
                'Green',
                'Red',
                'NIR',
                'SWIR1',
                'SWIR2'
            ])
        )

        return (
            optical
            .updateMask(mask)
            .copyProperties(img, ['system:time_start'])
        )

    def procesar_l89(img):
        img = ee.Image(img)

        qa_pixel = img.select('QA_PIXEL')
        qa_radsat = img.select('QA_RADSAT')

        mask = (
            qa_pixel.bitwiseAnd(1 << 1).eq(0)
            .And(qa_pixel.bitwiseAnd(1 << 2).eq(0))
            .And(qa_pixel.bitwiseAnd(1 << 3).eq(0))
            .And(qa_pixel.bitwiseAnd(1 << 4).eq(0))
            .And(qa_pixel.bitwiseAnd(1 << 5).eq(0))
            .And(qa_radsat.eq(0))
        )

        optical = (
            img.select([
                'SR_B2',
                'SR_B3',
                'SR_B4',
                'SR_B5',
                'SR_B6',
                'SR_B7'
            ])
            .multiply(0.0000275)
            .add(-0.2)
            .rename([
                'Blue',
                'Green',
                'Red',
                'NIR',
                'SWIR1',
                'SWIR2'
            ])
        )

        return (
            optical
            .updateMask(mask)
            .copyProperties(img, ['system:time_start'])
        )

    if anio <= 2011:
        coleccion = (
            ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
            .filterBounds(roi)
            .filterDate(fecha_inicio, fecha_fin)
            .map(procesar_l57)
        )

    elif 2012 <= anio <= 2013:
        coleccion = (
            ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
            .filterBounds(roi)
            .filterDate(fecha_inicio, fecha_fin)
            .map(procesar_l57)
        )

    elif 2014 <= anio <= 2020:
        coleccion = (
            ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterBounds(roi)
            .filterDate(fecha_inicio, fecha_fin)
            .map(procesar_l89)
        )

    else:
        landsat8 = (
            ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterBounds(roi)
            .filterDate(fecha_inicio, fecha_fin)
            .map(procesar_l89)
        )

        landsat9 = (
            ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
            .filterBounds(roi)
            .filterDate(fecha_inicio, fecha_fin)
            .map(procesar_l89)
        )

        coleccion = landsat8.merge(landsat9)

    return coleccion


def crear_mosaico_anual(anio):
    """
    Crea mosaico anual mediano, recorta al área de estudio y agrega índices.
    """

    coleccion = coleccion_landsat_por_anio(anio)

    n_img = coleccion.size().getInfo()
    print(f"\nAño {anio} - imágenes Landsat disponibles: {n_img}")

    if n_img == 0:
        raise ValueError(f"No hay imágenes Landsat disponibles para el año {anio}")

    mosaico = (
        coleccion
        .median()
        .clip(roi)
    )

    imagen = agregar_indices(mosaico).select(BANDAS)

    return imagen


# ============================================================
# 6. FUNCIÓN PARA BALANCEAR MUESTRAS
# ============================================================

def balancear_muestras(training_raw, anio):
    """
    Balancea las muestras de entrenamiento por clase usando máximo N_POR_CLASE.
    """

    print(f"\nAño {anio} - muestras sin balancear:")
    print(training_raw.aggregate_histogram('class').getInfo())

    training_raw = training_raw.randomColumn('random', seed=42)

    muestras_balanceadas = []

    for clase in [1, 2, 3, 4, 5]:
        muestras_clase = (
            training_raw
            .filter(ee.Filter.eq('class', clase))
            .limit(N_POR_CLASE, 'random')
        )
        muestras_balanceadas.append(muestras_clase)

    training = (
        muestras_balanceadas[0]
        .merge(muestras_balanceadas[1])
        .merge(muestras_balanceadas[2])
        .merge(muestras_balanceadas[3])
        .merge(muestras_balanceadas[4])
    )

    print(f"\nAño {anio} - muestras balanceadas:")
    print(training.aggregate_histogram('class').getInfo())

    return training


# ============================================================
# 7. FUNCIÓN PRINCIPAL DE CLASIFICACIÓN POR AÑO
# ============================================================

def clasificar_anio(anio):
    """
    Ejecuta el flujo completo para un año:
    mosaico, entrenamiento, balanceo, Random Forest,
    clasificación, validación, áreas y exportación.
    """

    print("\n" + "=" * 70)
    print(f"PROCESANDO AÑO {anio}")
    print("=" * 70)

    imagen = crear_mosaico_anual(anio)

    # ------------------------------------------------------------
    # Extraer muestras desde polígonos
    # ------------------------------------------------------------

    training_raw = imagen.sampleRegions(
        collection=training_polygons,
        properties=['class'],
        scale=30,
        geometries=False,
        tileScale=4
    )

    total_raw = training_raw.size().getInfo()
    print(f"\nAño {anio} - total píxeles entrenamiento sin balancear: {total_raw}")

    if total_raw == 0:
        raise ValueError(f"No se obtuvieron muestras de entrenamiento para {anio}")

    training = balancear_muestras(training_raw, anio)

    total_training = training.size().getInfo()
    print(f"\nAño {anio} - total píxeles entrenamiento balanceado: {total_training}")

    if total_training == 0:
        raise ValueError(f"No se obtuvieron muestras balanceadas para {anio}")

    # ------------------------------------------------------------
    # Entrenar Random Forest
    # ------------------------------------------------------------

    classifier_rf = ee.Classifier.smileRandomForest(
        numberOfTrees=200,
        variablesPerSplit=None,
        minLeafPopulation=1,
        bagFraction=0.7,
        seed=42
    ).train(
        features=training,
        classProperty='class',
        inputProperties=BANDAS
    )

    print(f"\nAño {anio} - Random Forest entrenado.")

    # ------------------------------------------------------------
    # Clasificar imagen
    # ------------------------------------------------------------

    clasificacion = imagen.classify(classifier_rf).rename('classification')

    print(f"Año {anio} - clasificación generada.")

    # ------------------------------------------------------------
    # Validación con puntos puros
    # ------------------------------------------------------------

    validation_sample = imagen.sampleRegions(
        collection=validation_points,
        properties=['class'],
        scale=30,
        geometries=True,
        tileScale=4
    )

    total_val = validation_sample.size().getInfo()
    print(f"\nAño {anio} - puntos válidos usados en validación: {total_val}")

    validated = validation_sample.classify(classifier_rf)

    confusion_matrix = validated.errorMatrix(
        'class',
        'classification',
        order=ee.List([1, 2, 3, 4, 5])
    )

    accuracy = confusion_matrix.accuracy()
    kappa = confusion_matrix.kappa()
    producers = confusion_matrix.producersAccuracy()
    consumers = confusion_matrix.consumersAccuracy()

    print(f"\nAño {anio} - matriz de confusión:")
    print(confusion_matrix.getInfo())

    print(f"\nAño {anio} - Accuracy:")
    print(accuracy.getInfo())

    print(f"\nAño {anio} - Kappa:")
    print(kappa.getInfo())

    print(f"\nAño {anio} - Precisión del productor:")
    print(producers.getInfo())

    print(f"\nAño {anio} - Precisión del usuario:")
    print(consumers.getInfo())

    # ------------------------------------------------------------
    # Área por clase
    # ------------------------------------------------------------

    area_image = ee.Image.pixelArea().divide(10000).addBands(clasificacion)

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

    areas_info = areas.getInfo()

    print(f"\nAño {anio} - área por clase en hectáreas:")
    print(areas_info)

    # ------------------------------------------------------------
    # Importancia de variables
    # ------------------------------------------------------------

    importance = ee.Dictionary(
        classifier_rf.explain().get('importance')
    )

    print(f"\nAño {anio} - importancia de variables:")
    print(importance.getInfo())

    # ------------------------------------------------------------
    # Exportar clasificación raster
    # ------------------------------------------------------------

    export_task = ee.batch.Export.image.toDrive(
        image=clasificacion.toByte(),
        description=f'RF_Usme_{anio}_Landsat',
        folder='GEE_USME_GEOMATICA',
        fileNamePrefix=f'RF_Usme_{anio}_Landsat',
        region=roi.geometry(),
        scale=30,
        maxPixels=1e13
    )

    export_task.start()

    print(f"\nAño {anio} - exportación raster iniciada.")

    # ------------------------------------------------------------
    # Preparar resumen tabular
    # ------------------------------------------------------------

    accuracy_value = accuracy.getInfo()
    kappa_value = kappa.getInfo()

    area_dict = {
        'anio': anio,
        'accuracy': accuracy_value,
        'kappa': kappa_value,
        'puntos_validacion_usados': total_val,
        'muestras_entrenamiento_balanceadas': total_training
    }

    grupos = areas_info.get('groups', [])

    for grupo in grupos:
        clase = int(grupo['class'])
        area = float(grupo['sum'])
        nombre = LEYENDA.get(clase, f'clase_{clase}')
        area_dict[f'area_ha_{nombre}'] = area

    return ee.Feature(None, area_dict)


# ============================================================
# 8. EJECUTAR PROCESO MULTIANUAL
# ============================================================

features_resumen = []

for anio in ANIOS:
    feature = clasificar_anio(anio)
    features_resumen.append(feature)


resumen_fc = ee.FeatureCollection(features_resumen)


# ============================================================
# 9. EXPORTAR TABLA RESUMEN A GOOGLE DRIVE
# ============================================================

tabla_task = ee.batch.Export.table.toDrive(
    collection=resumen_fc,
    description='Resumen_areas_metricas_RF_Usme_multianual',
    folder='GEE_USME_GEOMATICA',
    fileNamePrefix='Resumen_areas_metricas_RF_Usme_multianual',
    fileFormat='CSV'
)

tabla_task.start()


# ============================================================
# 10. FINALIZACIÓN
# ============================================================

print("\n" + "=" * 70)
print("PROCESO MULTIANUAL FINALIZADO")
print("Exportaciones iniciadas en Google Drive.")
print("Carpeta de salida: GEE_USME_GEOMATICA")
print("=" * 70)

print("\nLeyenda usada:")
print("1 = Vegetación / cobertura agro-natural")
print("2 = Urbano / construido")
print("3 = Minería de arcilla / actividad ladrillera")
print("4 = Suelo desnudo no minero")
print("5 = Agua")