# ============================================================
# TABLAS Y GRÁFICOS - PROYECTO GEOMÁTICA GENERAL USME
# Resultados multianuales Random Forest
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# 1. CARPETA DE SALIDA
# ============================================================

output_dir = Path("/home/rstudio/work/proyecto_final_geomatica_gral/resultados")
output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. DATOS MULTIANUALES
# ============================================================

datos = [
    {
        "anio": 1990,
        "accuracy": 0.6235955056179775,
        "kappa": 0.5193648490710514,
        "vegetacion_ha": 4283.593108020508,
        "urbano_ha": 1974.5233644838186,
        "mineria_ha": 432.8272133399886,
        "suelo_desnudo_ha": 6569.535001494279,
        "agua_ha": 115.28899210552142,
    },
    {
        "anio": 1995,
        "accuracy": 0.7098445595854922,
        "kappa": 0.6288334077406504,
        "vegetacion_ha": 9881.49970339573,
        "urbano_ha": 1221.8278145140598,
        "mineria_ha": 507.32689575209344,
        "suelo_desnudo_ha": 9417.616095112295,
        "agua_ha": 460.6408002002441,
    },
    {
        "anio": 2000,
        "accuracy": 0.6918918918918919,
        "kappa": 0.6034819884184403,
        "vegetacion_ha": 5788.743756460275,
        "urbano_ha": 1126.1482463868451,
        "mineria_ha": 450.21155039823054,
        "suelo_desnudo_ha": 7165.377683150365,
        "agua_ha": 104.0445433220598,
    },
    {
        "anio": 2010,
        "accuracy": 0.7909604519774012,
        "kappa": 0.7255123852634227,
        "vegetacion_ha": 9390.184258732283,
        "urbano_ha": 747.1570508664346,
        "mineria_ha": 573.7026604348588,
        "suelo_desnudo_ha": 10140.40697099668,
        "agua_ha": 137.35035392702582,
    },
    {
        "anio": 2015,
        "accuracy": 0.8186528497409327,
        "kappa": 0.7640998777719574,
        "vegetacion_ha": 9204.177681601057,
        "urbano_ha": 889.663409113857,
        "mineria_ha": 640.3682719001328,
        "suelo_desnudo_ha": 9950.797374105929,
        "agua_ha": 143.8264686625402,
    },
    {
        "anio": 2020,
        "accuracy": 0.844559585492228,
        "kappa": 0.7979833222846376,
        "vegetacion_ha": 9838.894642912208,
        "urbano_ha": 1005.2776565554757,
        "mineria_ha": 518.6215380673378,
        "suelo_desnudo_ha": 9741.39794115491,
        "agua_ha": 154.42188623791253,
    },
    {
        "anio": 2024,
        "accuracy": 0.8393782383419689,
        "kappa": 0.7900554424871921,
        "vegetacion_ha": 9681.95617453243,
        "urbano_ha": 1181.8217439332386,
        "mineria_ha": 301.4958082461145,
        "suelo_desnudo_ha": 10184.246706963251,
        "agua_ha": 139.3908796876915,
    },
]

df = pd.DataFrame(datos)


# ============================================================
# 3. DATOS AUXILIARES BUILDINGS 2024
# ============================================================

buildings_2024 = pd.DataFrame([
    {
        "indicador": "Urbano total clasificado",
        "area_ha": 1181.82,
        "porcentaje": 100.00,
    },
    {
        "indicador": "Urbano con buildings",
        "area_ha": 994.45,
        "porcentaje": 84.15,
    },
    {
        "indicador": "Urbano sin buildings",
        "area_ha": 187.37,
        "porcentaje": 15.85,
    },
    {
        "indicador": "Minería total clasificada",
        "area_ha": 301.50,
        "porcentaje": 100.00,
    },
    {
        "indicador": "Minería con buildings",
        "area_ha": 185.71,
        "porcentaje": 61.60,
    },
    {
        "indicador": "Minería sin buildings",
        "area_ha": 115.78,
        "porcentaje": 38.40,
    },
    {
        "indicador": "Suelo desnudo total clasificado",
        "area_ha": 10184.25,
        "porcentaje": 100.00,
    },
    {
        "indicador": "Suelo desnudo con buildings",
        "area_ha": 703.77,
        "porcentaje": None,
    },
])


# ============================================================
# 4. EXPORTAR TABLAS CSV
# ============================================================

df.to_csv(output_dir / "tabla_areas_metricas_usme.csv", index=False)
buildings_2024.to_csv(output_dir / "tabla_buildings_2024.csv", index=False)

print("Tablas exportadas:")
print(output_dir / "tabla_areas_metricas_usme.csv")
print(output_dir / "tabla_buildings_2024.csv")


# ============================================================
# 5. GRÁFICO ÁREA MINERA
# ============================================================

plt.figure(figsize=(8, 5))
plt.plot(df["anio"], df["mineria_ha"], marker="o")
plt.title("Área clasificada como minería de arcilla / actividad ladrillera")
plt.xlabel("Año")
plt.ylabel("Área (ha)")
plt.grid(True)
plt.tight_layout()
plt.savefig(output_dir / "grafico_area_minera.png", dpi=300)
plt.close()


# ============================================================
# 6. GRÁFICO URBANO, MINERÍA Y SUELO DESNUDO
# ============================================================

plt.figure(figsize=(8, 5))
plt.plot(df["anio"], df["urbano_ha"], marker="o", label="Urbano/construido")
plt.plot(df["anio"], df["mineria_ha"], marker="o", label="Minería de arcilla")
plt.plot(df["anio"], df["suelo_desnudo_ha"], marker="o", label="Suelo desnudo")
plt.title("Comparación multitemporal de clases críticas")
plt.xlabel("Año")
plt.ylabel("Área (ha)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(output_dir / "grafico_clases_criticas.png", dpi=300)
plt.close()


# ============================================================
# 7. GRÁFICO ACCURACY Y KAPPA
# ============================================================

plt.figure(figsize=(8, 5))
plt.plot(df["anio"], df["accuracy"], marker="o", label="Accuracy")
plt.plot(df["anio"], df["kappa"], marker="o", label="Kappa")
plt.title("Métricas de validación por año")
plt.xlabel("Año")
plt.ylabel("Valor")
plt.ylim(0, 1)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(output_dir / "grafico_accuracy_kappa.png", dpi=300)
plt.close()


# ============================================================
# 8. GRÁFICO BUILDINGS 2024
# ============================================================

buildings_plot = buildings_2024[
    buildings_2024["indicador"].isin([
        "Urbano con buildings",
        "Urbano sin buildings",
        "Minería con buildings",
        "Minería sin buildings"
    ])
].copy()

plt.figure(figsize=(9, 5))
plt.bar(buildings_plot["indicador"], buildings_plot["area_ha"])
plt.title("Cruce auxiliar entre clasificación 2024 y edificaciones")
plt.xlabel("Indicador")
plt.ylabel("Área (ha)")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(output_dir / "grafico_buildings_2024.png", dpi=300)
plt.close()


# ============================================================
# 9. RESUMEN EN CONSOLA
# ============================================================

print("\nTabla principal:")
print(df)

print("\nTabla buildings 2024:")
print(buildings_2024)

print("\nGráficos exportados en:")
print(output_dir)