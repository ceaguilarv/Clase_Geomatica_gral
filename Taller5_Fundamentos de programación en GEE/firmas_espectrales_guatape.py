import ee
import pandas as pd
import matplotlib.pyplot as plt
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
images_dir = base_dir / "images"
data_dir.mkdir(exist_ok=True)
images_dir.mkdir(exist_ok=True)

# =========================================================
# 3. PUNTOS DE MUESTREO DEL ENUNCIADO
# =========================================================
punto_agua = ee.Geometry.Point([-75.158, 6.265])     # Represa de Guatapé
punto_bosque = ee.Geometry.Point([-75.140, 6.275])   # Bosque cercano

# =========================================================
# 4. IMAGEN SENTINEL-2
# =========================================================
img_s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(punto_agua)
    .filterDate("2023-01-01", "2023-12-31")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
    .sort("CLOUDY_PIXEL_PERCENTAGE")
    .first()
)

bandas_estudio = ["B2", "B3", "B4", "B8", "B11", "B12"]
img_espectral = img_s2.select(bandas_estudio)

# =========================================================
# 5. EXTRACCIÓN DE VALORES
# =========================================================
valores_agua = img_espectral.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=punto_agua,
    scale=10
).getInfo()

valores_bosque = img_espectral.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=punto_bosque,
    scale=10
).getInfo()

# =========================================================
# 6. TABLA DE FIRMAS ESPECTRALES
# =========================================================
df_firmas = pd.DataFrame({
    "Banda": bandas_estudio,
    "Agua": [valores_agua.get(b) for b in bandas_estudio],
    "Bosque": [valores_bosque.get(b) for b in bandas_estudio]
})

csv_path = data_dir / "02_firmas_espectrales_guatape.csv"
df_firmas.to_csv(csv_path, index=False)

# =========================================================
# 7. GRÁFICO
# =========================================================
fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(df_firmas["Banda"], df_firmas["Agua"], marker="s", label="Agua (Represa)", linewidth=2)
ax.plot(df_firmas["Banda"], df_firmas["Bosque"], marker="o", label="Bosque", linewidth=2)

ax.set_title("Firmas Espectrales - Guatapé (Sentinel-2)", fontsize=14)
ax.set_xlabel("Bandas Espectrales", fontsize=12)
ax.set_ylabel("Reflectancia de Superficie (Escalada)", fontsize=12)
ax.legend()
ax.grid(True, linestyle="--", alpha=0.6)

plt.tight_layout()

png_path = images_dir / "02_firmas_espectrales_guatape.png"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.close()

# =========================================================
# 8. CONTROL
# =========================================================
print("Paso 4 listo")
print("Imagen usada:", img_s2.get("system:id").getInfo())
print("CSV generado:", csv_path)
print("PNG generado:", png_path)
print(df_firmas)
