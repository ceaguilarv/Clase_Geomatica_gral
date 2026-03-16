# Sección 6 – Google Earth Engine aplicado a Santa Librada, Usme

Este repositorio/documento reúne el desarrollo completo de la **Sección 6** del taller de **Google Earth Engine (GEE)**, adaptado al sector de **Santa Librada, localidad de Usme (Bogotá, Colombia)**. El trabajo no se limitó a reproducir los ejemplos originales de la guía, sino que los orientó a un caso territorial concreto, con énfasis en observación satelital, análisis geoespacial, visualización cartográfica y documentación reproducible.

## Objetivo general

Desarrollar paso a paso los ejercicios de la Sección 6 del taller de GEE, adaptándolos al área de estudio de Santa Librada, Usme, y documentando no solo los resultados obtenidos sino también los errores encontrados durante la práctica y las correcciones metodológicas implementadas.

## Área de estudio

El punto de referencia principal utilizado en la mayoría de los ejercicios fue:

- **Latitud:** 4.521001  
- **Longitud:** -74.110149

En Earth Engine, el punto se definió así:

```python
punto_estudio = ee.Geometry.Point([-74.110149, 4.521001])
```

A partir de este punto se construyeron diferentes áreas auxiliares según el objetivo de cada ejercicio:

- **área de búsqueda**, para consultar colecciones sin depender del borde de una sola escena;
- **área de recorte**, para ejercicios de `clip()`;
- **área de análisis**, para cálculos estadísticos como NDVI medio o series temporales.

## Estructura del trabajo

La sección desarrollada incluye los siguientes bloques:

- **6.1–6.5**: preparación del entorno, acceso a GEE y lectura de catálogos
- **6.6–6.17**: exploración de catálogos satelitales, raster y vectoriales
- **6.18–6.20**: querying, clipping, NDVI y análisis temporal
- **6.21–6.22**: entregables, criterios de evaluación y glosario de funciones

## Secciones trabajadas

### 6.1 Requerimientos
Se verificó el entorno mínimo de trabajo: Google Earth Engine, proyecto en Google Cloud, contenedor Docker, Quarto, TinyTeX, QGIS con PIXI y plugin de GEE.

### 6.2 Registro y configuración de GEE
Se comprobó el uso operativo del proyecto:

```python
bamboo-storm-477002-v4
```

### 6.3 Entornos de ejecución
Se definió como ruta principal de trabajo:

- Python en contenedor
- Quarto para documentación
- QGIS para integración SIG

### 6.4 Inicialización del entorno
Se corrigieron problemas iniciales de autenticación y se estableció la inicialización correcta de la sesión:

```python
ee.Initialize(project='bamboo-storm-477002-v4')
```

### 6.5 Acceso a catálogos
Se revisaron los principales Asset ID utilizados a lo largo del trabajo, distinguiendo entre `Image`, `ImageCollection` y `FeatureCollection`.

### 6.6 Landsat 8/9
Se trabajó con `LANDSAT/LC09/C02/T1_TOA`, generando metadatos, serializado, HTML y PNG RGB.

### 6.7 GEE desde QGIS
Se validó la integración del plugin de GEE en QGIS, especialmente a través de la pestaña **Search**.

### 6.8 ArcGIS Pro
No se desarrolló, por decisión metodológica.

### 6.9 Sentinel-2
Se trabajó con `COPERNICUS/S2_SR_HARMONIZED` para observación óptica y generación de productos base.

### 6.10 Sentinel-1
Se trabajó con `COPERNICUS/S1_GRD`, usando polarización `VV` y visualización SAR.

### 6.11 MODIS
Se corrigió el uso inicial del producto MODIS. La versión correcta fue:

```python
MODIS/061/MOD09A1
```

### 6.12 SRTM
Se generó un producto de relieve sombreado (`hillshade`) a partir de `USGS/SRTMGL1_003`.

### 6.13 CHIRPS
Se trabajó precipitación a escala de Cundinamarca con `UCSB-CHG/CHIRPS/DAILY`.

### 6.14 Open Buildings
Se trabajó con la colección vectorial:

```python
GOOGLE/Research/open-buildings/v3/polygons
```

### 6.15 BlackMarble
Se trabajó con luces nocturnas usando:

```python
NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG
```

### 6.16 DSWx Sentinel-1
Se trabajó clasificación de agua con:

```python
OPERA/DSWX/L3_V1/S1
```

### 6.17 WorldPop
Se trabajó estimación de población con:

```python
WorldPop/GP/100m/pop
```

### 6.18 Querying y clipping
Se documentó uno de los problemas metodológicos más importantes del trabajo: el uso de una sola escena Sentinel-2 (`.first()`) podía producir recortes vacíos o partidos. La corrección consistió en:

1. usar un **área de búsqueda más amplia**;
2. construir un **composite** con `.median()`;
3. definir un **área de clip pequeña**;
4. aplicar `clip()` solo al final.

Ejemplo conceptual:

```python
area_busqueda = punto_estudio.buffer(8000)
area_clip = punto_estudio.buffer(1200).bounds()
coleccion_s2 = ee.ImageCollection(...).filterBounds(area_busqueda)
composite_s2 = coleccion_s2.median()
s2_clip = composite_s2.clip(area_clip)
```

### 6.19 NDVI
También se corrigió el problema de calcular NDVI sobre una sola escena. La versión estable fue:

```python
coleccion_s2 = ee.ImageCollection(...).filterBounds(region_interes)
composite_s2 = coleccion_s2.median()
ndvi = composite_s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
```

En esta sección se dejó claro que el **NDVI analítico no debía depender de un clip erróneo**, y que la visualización debía enfocarse en Santa Librada sin comprometer el cálculo.

### 6.20 Análisis temporal y galería visual
Se construyó una serie temporal de NDVI medio y una galería visual de imágenes Sentinel-2 para interpretar cambios de cobertura a lo largo de 2023.

## Productos generados

A lo largo de la sección se generaron distintos tipos de salidas:

- **JSON de metadatos**
- **JSON serializados**
- **mapas HTML interactivos**
- **PNG de resultados**
- **CSV de series temporales**

Entre los productos más importantes se encuentran:

- `landsat9_santa_librada_grilla.png`
- `sentinel2_santa_librada_rgb.png`
- `sentinel1_santa_librada_vv.png`
- `modis_santa_librada_rgb.png`
- `srtm_santa_librada_hillshade.png`
- `chirps_cundinamarca_precipitacion.png`
- `buildings_santa_librada.png`
- `ntl_santa_librada.png`
- `dswx_santa_librada.png`
- `worldpop_santa_librada.png`
- `s2_clip_santa_librada.png`
- `ndvi_composite_santa_librada.png`
- `serie_temporal_ndvi_santa_librada.png`

## Errores metodológicos relevantes

Durante la práctica aparecieron errores que se documentaron como parte fundamental del proceso.

### 1. Error de autenticación e inicialización
En la etapa inicial, Earth Engine intentó usar `gcloud` en un entorno donde no estaba disponible.

**Corrección:** usar la inicialización correcta del proyecto y separar claramente el entorno del contenedor del entorno PIXI/QGIS.

### 2. Error de rutas entre Linux y Windows
Al trabajar entre el contenedor y QGIS, algunas rutas apuntaban a sistemas de archivos distintos.

**Corrección:** mantener los scripts principales en el contenedor con rutas Linux y usar rutas Windows solo en QGIS cuando fue necesario.

### 3. Error por uso de una sola escena Sentinel-2
En 6.18 y 6.19, el uso de `.first()` producía imágenes partidas, vacías o con bordes de tile visibles.

**Corrección:** usar `ImageCollection` + `.median()` sobre un área de búsqueda más grande, y solo después recortar o enfocar la visualización.

### 4. Error por producto MODIS inadecuado
Se usó inicialmente un producto diario con demasiada nubosidad.

**Corrección:** cambiar a `MODIS/061/MOD09A1`.

## Criterio metodológico principal

La principal lección del trabajo fue que **no siempre es suficiente tomar la primera escena disponible de una colección**. Cuando el área de estudio se ubica cerca del borde de un tile o presenta coberturas parciales, es más robusto:

- ampliar el área de búsqueda;
- trabajar con varias imágenes;
- construir composiciones (`median`);
- y luego aplicar recortes o visualizaciones localizadas.

Este criterio fue clave para corregir los ejercicios de **querying/clipping** y **NDVI**.

## Estructura recomendada del proyecto

```text
taller_GEE/
├── seccion6.qmd
├── README.md
├── evidencias/
│   ├── evid_6_1_entorno.png
│   ├── evid_6_2_inicializacion_ok.png
│   ├── evid_6_3_entornos_trabajo.png
│   ├── ...
│   └── evid_6_20_serie_temporal.png
├── outputs/
│   ├── *.json
│   ├── *.html
│   ├── *.png
│   └── *.csv
└── scripts/
    ├── landsat_6_6.py
    ├── sentinel2_6_9.py
    ├── sentinel1_6_10.py
    ├── modis_6_11.py
    ├── srtm_6_12.py
    ├── chirps_6_13.py
    ├── buildings_6_14.py
    ├── blackmarble_6_15.py
    ├── dswx_6_16.py
    ├── worldpop_6_17.py
    ├── clip_6_18.py
    ├── ndvi_6_19.py
    └── serie_temporal_6_20.py
```

## Conclusión general

El desarrollo de esta sección permitió transformar una guía general de Google Earth Engine en un ejercicio aplicado al caso de **Santa Librada, Usme**. Más allá del uso de catálogos, mapas y scripts, el proceso destacó la importancia de la validación visual, la lectura crítica de salidas y la documentación de errores y correcciones. Esto fortaleció tanto el valor técnico como el valor metodológico del trabajo final.

## Autoría

Documento preparado por:

- **Carlos Aguilar**
- **Luis Gálvez**
