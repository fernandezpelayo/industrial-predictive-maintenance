
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS Y VARIABLES DE ENTORNO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "mantenimiento.csv"

load_dotenv(BASE_DIR / ".env")


# ============================================================
# 2. CONFIGURACIÓN DE LA CONEXIÓN A MYSQL
# ============================================================

def database_url(database=None):
    """Construye la URL de conexión utilizando las variables de .env."""

    required = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Faltan variables de entorno en .env: {', '.join(missing)}"
        )

    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=database if database is not None else os.getenv("DB_NAME"),
    )


# ============================================================
# 3. CARGA Y VALIDACIÓN DEL CSV ORIGINAL
# ============================================================

if not DATA_PATH.exists():
    raise FileNotFoundError(f"No se encuentra el archivo: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

columnas = {
    "UDI": "UDI",
    "Product ID": "Product_ID",
    "Type": "Tipo",
    "Air temperature [K]": "Temp_Aire",
    "Process temperature [K]": "Temp_Proceso",
    "Rotational speed [rpm]": "Velocidad",
    "Torque [Nm]": "Torque",
    "Tool wear [min]": "Desgaste",
    "Target": "Fallo",
    "Failure Type": "Tipo_Fallo",
}

faltantes = set(columnas) - set(df.columns)

if faltantes:
    raise ValueError(
        f"Faltan columnas requeridas en el CSV: {sorted(faltantes)}"
    )

df_mantenimiento = df.rename(columns=columnas)[
    list(columnas.values())
].copy()

# Comprobar valores nulos.
if df_mantenimiento.isnull().any().any():
    columnas_nulas = df_mantenimiento.columns[
        df_mantenimiento.isnull().any()
    ].tolist()

    raise ValueError(
        f"Se han encontrado valores nulos en: {columnas_nulas}"
    )

# Comprobar que UDI identifica cada registro.
if df_mantenimiento["UDI"].duplicated().any():
    raise ValueError("Se han encontrado identificadores UDI duplicados.")

# Comprobar que la variable objetivo solo contiene 0 y 1.
if not df_mantenimiento["Fallo"].isin([0, 1]).all():
    raise ValueError("La columna Fallo debe contener exclusivamente 0 y 1.")

# Validar las variables numéricas.
columnas_numericas = [
    "UDI",
    "Temp_Aire",
    "Temp_Proceso",
    "Velocidad",
    "Torque",
    "Desgaste",
    "Fallo",
]

for columna in columnas_numericas:
    df_mantenimiento[columna] = pd.to_numeric(
        df_mantenimiento[columna],
        errors="raise",
    )

if not np.isfinite(
    df_mantenimiento[columnas_numericas].to_numpy(dtype=float)
).all():
    raise ValueError("Se han encontrado valores numéricos no válidos.")

df_mantenimiento["Fallo"] = df_mantenimiento["Fallo"].astype("int8")


# ============================================================
# 4. CREACIÓN DE INDICADORES DERIVADOS
# ============================================================

# Proxy de esfuerzo mecánico: Torque × Velocidad.
# No representa consumo energético real.

df_mantenimiento["Indice_Esfuerzo_Mecanico"] = (
    df_mantenimiento["Torque"] * df_mantenimiento["Velocidad"]
)

# Umbral estadístico: percentil 75 del conjunto de datos.
umbral_esfuerzo = df_mantenimiento[
    "Indice_Esfuerzo_Mecanico"
].quantile(0.75)

# Identificación de registros por encima del umbral.
df_mantenimiento["Esfuerzo_Elevado"] = (
    df_mantenimiento["Indice_Esfuerzo_Mecanico"] > umbral_esfuerzo
).astype("int8")


# ============================================================
# 5. VALIDACIÓN DE LA CONFIGURACIÓN DE MYSQL
# ============================================================

db_name = os.getenv("DB_NAME")

if not re.fullmatch(r"[A-Za-z0-9_]+", db_name):
    raise ValueError(
        "DB_NAME solo puede contener letras, números y guion bajo."
    )


# ============================================================
# 6. CONFIRMACIÓN ANTES DE SUSTITUIR LA TABLA
# ============================================================

print("\n=== CARGA DE DATOS EN MYSQL ===")
print(f"Registros preparados: {len(df_mantenimiento)}")
print(f"Base de datos: {db_name}")
print(f"Umbral de esfuerzo (percentil 75): {umbral_esfuerzo:.2f}")

print(
    "\nATENCIÓN: si la tabla monitoreo_maquinas ya existe, "
    "será sustituida completamente."
)

confirmacion = input(
    "\n¿Deseas continuar con la carga? (s/n): "
).strip().lower()

if confirmacion != "s":
    print("Carga cancelada. No se han realizado cambios en MySQL.")
    raise SystemExit


# ============================================================
# 7. CREACIÓN DE LA BASE DE DATOS SI NO EXISTE
# ============================================================

server_engine = create_engine(database_url(database=None))

try:
    with server_engine.begin() as conn:
        conn.execute(
            text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        )
finally:
    server_engine.dispose()


# ============================================================
# 8. CARGA DE DATOS EN MYSQL
# ============================================================

engine = create_engine(database_url())

try:
    df_mantenimiento.to_sql(
        name="monitoreo_maquinas",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )
finally:
    engine.dispose()


# ============================================================
# 9. RESUMEN DE LA CARGA
# ============================================================

print("\n=== CARGA COMPLETADA ===")
print(f"Registros cargados: {len(df_mantenimiento)}")
print(f"Total de fallos: {df_mantenimiento['Fallo'].sum()}")
print(
    f"Tasa de fallo: "
    f"{df_mantenimiento['Fallo'].mean() * 100:.2f}%"
)
print(f"Umbral de esfuerzo: {umbral_esfuerzo:.2f}")
print("Tabla creada: monitoreo_maquinas")
print("Columnas derivadas:")
print("- Indice_Esfuerzo_Mecanico")
print("- Esfuerzo_Elevado")
