import ee
import folium
import datetime

ee.Initialize(project='bamboo-storm-477002-v4')

lon_centro, lat_centro = -74.110149, 4.521001
punto_estudio = ee.Geometry.Point([lon_centro, lat_centro])

l9 = (
    ee.ImageCollection("LANDSAT/LC09/C02/T1_TOA")
    .filterBounds(punto_estudio)
    .filterDate('2023-01-01', '2023-12-31')
    .sort('CLOUD_COVER')
    .first()
)

vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0.0, 'max': 0.3}
map_id_dict = ee.Image(l9).getMapId(vis_params)

fecha_ms = l9.get('system:time_start').getInfo()
fecha_capa = datetime.datetime.fromtimestamp(fecha_ms / 1000.0, datetime.UTC).strftime('%Y-%m-%d')
id_desplegada = l9.get('system:id').getInfo()
nubes_desplegada = l9.get('CLOUD_COVER').getInfo()

print("Capa desplegada:", fecha_capa)
print("ID:", id_desplegada)
print("Nubosidad:", nubes_desplegada)

m = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)

folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name=f'Landsat 9 RGB - {fecha_capa}'
).add_to(m)

folium.LayerControl().add_to(m)

m.save('/home/rstudio/work/map_landsat9_santa_librada.html')
print("Mapa guardado en /home/rstudio/work/map_landsat9_santa_librada.html")