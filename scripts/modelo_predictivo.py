
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

IMAGES_DIR = BASE_DIR / "reports" / "images"
METRICS_DIR = BASE_DIR / "reports" / "metrics"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

FEATURES = [
    "Temp_Aire",
    "Temp_Proceso",
    "Velocidad",
    "Torque",
    "Desgaste",
]

TARGET = "Fallo"


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

    required_columns = set(FEATURES + [TARGET])
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Faltan columnas en la tabla: {sorted(missing_columns)}"
        )

    # Comprobar que las variables utilizadas son numéricas.
    for column in FEATURES + [TARGET]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Comprobar valores nulos o infinitos.
    df[FEATURES + [TARGET]] = (
        df[FEATURES + [TARGET]]
        .replace([float("inf"), float("-inf")], pd.NA)
    )

    if df[FEATURES + [TARGET]].isna().any().any():
        raise ValueError(
            "Hay valores nulos o no numéricos en las variables del modelo."
        )

    # Comprobar que la variable objetivo solo contiene 0 y 1.
    if not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError(
            "La variable Fallo debe contener únicamente valores 0 y 1."
        )

    if df[TARGET].nunique() < 2:
        raise ValueError(
            "El modelo necesita registros de ambas clases de Fallo."
        )

    df[TARGET] = df[TARGET].astype(int)

    print(f"Registros cargados: {len(df)}")
    print(f"Fallos registrados: {df[TARGET].sum()}")
    print(f"Tasa de fallo: {df[TARGET].mean() * 100:.2f}%")

    return df


# ============================================================
# ENTRENAMIENTO Y EVALUACIÓN DEL MODELO
# ============================================================

def entrenar_modelo(df):
    X = df[FEATURES]
    y = df[TARGET]

    # Separar los datos: 80 % entrenamiento y 20 % prueba.
    # Stratify mantiene la proporción de fallos en ambos grupos.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"\nRegistros de entrenamiento: {len(X_train)}")
    print(f"Registros de prueba: {len(X_test)}")

    # Crear y entrenar el modelo Random Forest.
    modelo = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    modelo.fit(X_train, y_train)

    # Realizar predicciones sobre los datos de prueba.
    y_pred = modelo.predict(X_test)

    return modelo, X_test, y_test, y_pred


# ============================================================
# EVALUACIÓN DE RESULTADOS
# ============================================================

def evaluar_modelo(y_test, y_pred):
    print("\n=== RESULTADOS DEL MODELO ===\n")

    informe = classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=["Sin fallo", "Fallo"],
        output_dict=True,
        zero_division=0
    )

    print(
        classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["Sin fallo", "Fallo"],
            zero_division=0
        )
    )

    # Guardar las métricas en un CSV.
    pd.DataFrame(informe).transpose().to_csv(
        METRICS_DIR / "metricas_modelo.csv",
        index_label="clase",
        sep=";",
        decimal=","
    )

    # Generar matriz de confusión.
    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=[0, 1]
    )

    plt.figure(figsize=(6, 5))

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="YlGnBu",
        cbar=False,
        xticklabels=["Sin fallo", "Fallo"],
        yticklabels=["Sin fallo", "Fallo"]
    )

    plt.title("Matriz de confusión (conjunto de prueba)")
    plt.xlabel("Predicción")
    plt.ylabel("Valor real")
    plt.tight_layout()

    output_path = IMAGES_DIR / "matriz_confusion.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()

    print(f"Matriz de confusión guardada en: {output_path}")


# ============================================================
# IMPORTANCIA DE LAS VARIABLES
# ============================================================

def generar_importancias(modelo):
    df_importancias = pd.DataFrame({
        "variable": FEATURES,
        "importancia": modelo.feature_importances_
    })

    # Traducir los nombres de las variables.
    df_importancias["variable"] = (
        df_importancias["variable"].replace({
            "Temp_Aire": "Temp. aire",
            "Temp_Proceso": "Temp. proceso",
            "Velocidad": "Velocidad",
            "Torque": "Torque",
            "Desgaste": "Desgaste"
        })
    )

    # Ordenar de mayor a menor importancia.
    df_importancias = df_importancias.sort_values(
        by="importancia",
        ascending=False
    )

    df_importancias.to_csv(
        METRICS_DIR / "importancia_variables.csv",
        index=False,
        sep=";",
        decimal=","
    )

    print("\n=== IMPORTANCIA DE LAS VARIABLES ===")

    print(
        df_importancias.to_string(
            index=False,
            formatters={
                "importancia": "{:.4f}".format
            }
        )
    )

    print(
    "\nImportancias guardadas en: "
    "reports/metrics/importancia_variables.csv"
)


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    print("Cargando datos desde MySQL...")

    df = load_data()

    modelo, X_test, y_test, y_pred = entrenar_modelo(df)

    evaluar_modelo(y_test, y_pred)

    generar_importancias(modelo)

    print("\nModelo entrenado y evaluación completada.")


if __name__ == "__main__":
    main()