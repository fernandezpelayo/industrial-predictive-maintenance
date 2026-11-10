
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "maquinas_criticas.csv"

load_dotenv(BASE_DIR / ".env")


# ============================================================
# CONEXIÓN A MYSQL
# ============================================================

def database_url():
    required = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")

    missing = [
        key for key in required
        if not os.getenv(key)
    ]

    if missing:
        raise ValueError(
            f"Faltan variables de entorno: {', '.join(missing)}"
        )

    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
    )


def load_data():
    engine = create_engine(database_url())

    try:
        df = pd.read_sql(
            "SELECT * FROM monitoreo_maquinas",
            con=engine
        )
    finally:
        engine.dispose()

    if df.empty:
        raise ValueError("La tabla monitoreo_maquinas está vacía.")

    required_columns = {
        "UDI",
        "Product_ID",
        "Desgaste",
        "Torque",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Faltan columnas en la tabla: {sorted(missing_columns)}"
        )

    for column in ["Desgaste", "Torque"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    if df[["Desgaste", "Torque"]].isna().any().any():
        raise ValueError(
            "Hay valores nulos o no numéricos en Desgaste o Torque."
        )

    print(f"Registros cargados: {len(df)}")

    return df


# ============================================================
# SELECCIÓN DE MÁQUINAS PARA REVISIÓN
# ============================================================

def seleccionar_registros(df):
    critico = df.loc[
        (df["Desgaste"] > 180)
        | (df["Torque"] > 60)
    ].copy()

    critico["Motivo_Revision"] = " "

    condicion_desgaste = critico["Desgaste"] > 180
    condicion_torque = critico["Torque"] > 60

    critico.loc[
        condicion_desgaste & ~condicion_torque,
        "Motivo_Revision"
    ] = "Desgaste alto"

    critico.loc[
        condicion_torque & ~condicion_desgaste,
        "Motivo_Revision"
    ] = "Torque alto"

    critico.loc[
        condicion_desgaste & condicion_torque,
        "Motivo_Revision"
    ] = "Desgaste alto; Torque alto"

    return critico


# ============================================================
# GENERACIÓN DEL REPORTE
# ============================================================

def generar_reporte(df, critico):
    total_registros = len(df)
    total_criticos = len(critico)

    porcentaje = (
        total_criticos / total_registros * 100
        if total_registros > 0
        else 0
    )

    print("\n=== REPORTE DE REVISIÓN GENERADO ===")
    print(f"Registros analizados: {total_registros}")
    print(f"Registros seleccionados: {total_criticos}")
    print(f"Porcentaje seleccionado: {porcentaje:.2f}%")

    print("\nCriterios:")
    print("- Desgaste > 180 minutos")
    print("- Torque > 60 Nm")

    print("\nMotivos:")

    if total_criticos > 0:
        print(
            critico["Motivo_Revision"]
            .value_counts()
            .to_string()
        )
    else:
        print("No se han encontrado registros.")

    # Redondear las columnas decimales para mejorar la presentación del archivo exportado.
    critico_export = critico.copy()

    columnas_decimales = critico_export.select_dtypes(
        include=["float"]
    ).columns

    critico_export[columnas_decimales] = (
        critico_export[columnas_decimales].round(2)
    )

    critico_export.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
        float_format="%.2f",
    )

    print(f"\nArchivo guardado en: {OUTPUT_PATH}")


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    print("Cargando datos desde MySQL...")

    df = load_data()

    critico = seleccionar_registros(df)

    generar_reporte(df, critico)


if __name__ == "__main__":
    main()
