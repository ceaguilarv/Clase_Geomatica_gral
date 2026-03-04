# Taller 4 – Conversión de Formatos e Interoperabilidad

Autor: Carlos Esteban Aguilar Vargas  
Curso: Geomática General  

## Descripción

Este repositorio documenta el desarrollo del Taller 4, enfocado en:

- Conversión de formatos espaciales
- Gestión de sistemas de coordenadas
- Procesos ETL espaciales
- Carga filtrada en PostgreSQL/PostGIS
- Visualización en Google Earth
- Verificación gráfica desde base de datos espacial

## Software utilizado

- QGIS
- PostgreSQL/PostGIS
- Google Earth
- Quarto

## Contenido del repositorio

- `informe.qmd` → Documento fuente en Quarto  
- `informe.html` → Versión renderizada en HTML  
- `informe.pdf` → Versión renderizada en PDF  
- `captura_postgis.png` → Evidencia tabular de carga en PostGIS  
- `previsualizacion_postgis.png` → Visualización gráfica desde PostGIS  
- `visualizacion_google_earth.png` → Visualización del KML en Google Earth  
- `mfebelvis_kml.kml` → Archivo generado en el Ejercicio 1
- `mpios_kml.kml` → Archivo generado a partir de los filtros

## Flujo aplicado

El proceso siguió la lógica profesional:

Extract → Transform → Load (ETL)

1. Extract: Carga de shapefile y archivo KML.  
2. Transform: Filtro por atributo y filtro espacial mediante buffer de 40 km.  
3. Load: Exportación y almacenamiento en PostgreSQL/PostGIS.

## Resultado

Se verificó:

- Correcta transformación a coordenadas geográficas (EPSG:4326).
- Aplicación eficiente de reglas de negocio.
- Integridad geométrica en base de datos espacial.
- Visualización correcta tanto en Google Earth como en QGIS.
