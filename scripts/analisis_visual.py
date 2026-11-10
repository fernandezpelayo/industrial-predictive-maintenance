
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")


# ============================================================
# 2. CONEXIÓN A MYSQL
# ============================================================

def database_url():
    """Construye la URL de conexión a MySQL."""

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
        database=os.getenv("DB_NAME"),
    )


def load_data():
    """Carga los datos de la tabla de mantenimiento."""

    engine = create_engine(database_url())

    try:
        with engine.connect() as conn:
            df = pd.read_sql(
                "SELECT * FROM monitoreo_maquinas",
                con=conn,
            )
    finally:
        engine.dispose()

    required_columns = [
        "Tipo",
        "Fallo",
        "Tipo_Fallo",
        "Temp_Aire",
        "Temp_Proceso",
        "Velocidad",
        "Torque",
        "Desgaste",
        "Indice_Esfuerzo_Mecanico",
    ]

    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Faltan columnas en la tabla MySQL: {sorted(missing_columns)}"
        )

    if not df["Fallo"].isin([0, 1]).all():
        raise ValueError("La columna Fallo debe contener exclusivamente 0 y 1.")

    return df


# ============================================================
# 3. CONFIGURACIÓN DE VISUALIZACIONES
# ============================================================

sns.set_theme(style="whitegrid")

traduccion_fallos = {
    "Power Failure": "Fallo de Potencia",
    "Tool Wear Failure": "Desgaste de Herramienta",
    "Overstrain Failure": "Sobreesfuerzo",
    "Random Failures": "Fallos Aleatorios",
    "Heat Dissipation Failure": "Disipación de Calor",
    "No Failure": "Etiqueta inconsistente (Sin fallo)",
}


# ============================================================
# 4. GRÁFICA: FRECUENCIA DE FALLOS
# ============================================================

def generar_grafica_fallos(df):

    # Se consideran los registros identificados como Fallo = 1.
    df_fallos = df.loc[df["Fallo"] == 1].copy()

    # Traducir las categorías sin perder etiquetas desconocidas.
    df_fallos["Tipo_Fallo"] = (
        df_fallos["Tipo_Fallo"]
        .map(traduccion_fallos)
        .fillna(df_fallos["Tipo_Fallo"])
    )

    # Ordenar las categorías por frecuencia total.
    orden = (
        df_fallos["Tipo_Fallo"]
        .value_counts()
        .index
    )

    plt.figure(figsize=(12, 7))

    ax = sns.countplot(
        data=df_fallos,
        x="Tipo_Fallo",
        hue="Tipo",
        order=orden,
    )

    # Añadir los valores encima de las barras.
    for container in ax.containers:
        ax.bar_label(
            container,
            fmt="%.0f",
            padding=3,
            fontsize=9,
        )

    plt.title(
        "Frecuencia de fallos por causa y tipo de máquina",
        fontsize=14,
        pad=15,
    )
    plt.xlabel("Tipo de fallo")
    plt.ylabel("Número de registros")
    plt.xticks(rotation=25, ha="right")
    plt.legend(title="Tipo de máquina")
    plt.tight_layout()

    output_path = REPORTS_DIR / "fallos.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()

    print(f"Gráfica de fallos guardada en: {output_path}")


# ============================================================
# 5. GRÁFICA: MATRIZ DE CORRELACIÓN
# ============================================================

def generar_matriz_correlacion(df):

    cols_analisis = [
        "Temp_Aire",
        "Temp_Proceso",
        "Velocidad",
        "Torque",
        "Desgaste",
        "Indice_Esfuerzo_Mecanico",
        "Fallo",
    ]

    correlacion = df[cols_analisis].corr()

    plt.figure(figsize=(12, 9))

    sns.heatmap(
        correlacion,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5,
        vmin=-1,
        vmax=1,
        square=True,
    )

    plt.title(
        "Matriz de correlación: variables operativas y fallos",
        fontsize=14,
        pad=15,
    )
    plt.tight_layout()

    output_path = REPORTS_DIR / "correlacion.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()

    print(f"Matriz de correlación guardada en: {output_path}")


# ============================================================
# 6. EJECUCIÓN PRINCIPAL
# ============================================================

def main():

    print("Cargando datos desde MySQL...")

    df = load_data()

    print(f"Registros cargados: {len(df)}")
    print(f"Fallos registrados: {df['Fallo'].sum()}")

    generar_grafica_fallos(df)
    generar_matriz_correlacion(df)

    print("\nAnálisis visual completado correctamente.")


if __name__ == "__main__":
    main()
    