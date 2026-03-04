# Taller 4 – Conversión de Formatos e Interoperabilidad

Autor: Carlos Esteban Aguilar Vargas  
Curso: Geomática General  

## Descripción

Este repositorio documenta el desarrollo del Taller 4, enfocado en:

- Conversión de formatos espaciales
- Gestión de sistemas de coordenadas
- Procesos ETL espaciales
- Carga filtrada en PostgreSQL/PostGIS

## Software utilizado

- QGIS
- PostgreSQL/PostGIS
- Quarto

## Contenido del repositorio

- `informe.qmd` → Documento fuente en Quarto  
- `informe.html` → Versión renderizada en HTML  
- `informe.pdf` → Versión renderizada en PDF  
- `captura_postgis.png` → Evidencia de carga en PostGIS  
- `mfebelvis_kml` → Archivo generado en el Ejercicio 1  

## Flujo aplicado

El proceso siguió la lógica profesional:

Extract → Transform → Load (ETL)

Primero se cargaron los datos originales, luego se aplicaron filtros alfanuméricos y espaciales, y finalmente se almacenaron en PostgreSQL/PostGIS.