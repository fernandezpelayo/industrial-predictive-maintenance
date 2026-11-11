# Proyecto de Monitoreo y Mantenimiento Predictivo Industrial

Este proyecto implementa un pipeline completo de datos (ETL → SQL → Machine Learning → Dashboard) aplicado a sensores industriales.  
El objetivo es identificar patrones de fallo, priorizar mantenimiento y ofrecer una visualización ejecutiva en Power BI.

---

## Índice

## Índice

1. [Tecnologías utilizadas](#tecnologías-utilizadas)
2. [Hallazgos principales](#hallazgos-principales)
3. [Definición del Índice de Esfuerzo Mecánico](#definición-del-índice-de-esfuerzo-mecánico)
4. [Modelo de Clasificación de Fallos](#modelo-de-clasificación-de-fallos)
   - [Metodología](#metodología)
   - [Resultados](#resultados)
   - [Interpretación](#interpretación)
5. [Limitaciones del Dataset](#limitaciones-del-dataset)
6. [Enfoque del Dashboard](#enfoque-del-dashboard)
7. [Arquitectura del Pipeline](#arquitectura-del-pipeline)
8. [Visualizaciones](#visualizaciones)
   - [Python](#python)
   - [Power BI](#power-bi)
9. [Estructura del Proyecto](#estructura-del-proyecto)
10. [Instalación y ejecución](#instalación-y-ejecución)
11. [Conclusiones](#conclusiones)
12. [Impacto](#impacto)
13. [Licencia](#licencia)
---

## Tecnologías utilizadas

- **Python**: limpieza, transformación y modelado (Pandas, Scikit‑Learn)
- **MySQL**: almacenamiento estructurado de datos
- **SQLAlchemy**: conexión Python ↔ SQL
- **Power BI**: dashboard interactivo y KPIs de negocio
- **Matplotlib / Seaborn**: análisis visual técnico
- **python-dotenv**: gestión segura de credenciales mediante variables de entorno

---

## Hallazgos principales

### 1. Relación entre esfuerzo mecánico y fallos
Los registros con valores más elevados del Índice de Esfuerzo Mecánico presentan una mayor tasa de fallos (8,92 %) que el resto de los registros (1,55 %).

### 2. Relación entre variables
Existe una correlación muy alta entre Torque y el Índice de Esfuerzo Mecánico, algo esperable porque este último se calcula multiplicando Torque por Velocidad.

### 3. Fallos por tipo de máquina
Las máquinas tipo L registran el mayor número de fallos y también la mayor tasa de fallo (3,92 %), seguidas de las tipo M (2,77 %) y H (2,09 %).

### 4. Variables más importantes del modelo
Torque, Velocidad y Desgaste son las tres variables que más influyen en los resultados del modelo.

### 5. Tasa de fallo global
De los 10.000 registros analizados, 339 corresponden a fallos, lo que representa un 3,39 % del total.

---

## Definición del Índice de Esfuerzo Mecánico

El dataset no incluye información energética real.  
Por ello se define un índice:

Índice de Esfuerzo Mecánico = Torque × Velocidad


No representa energía física, pero sí refleja carga operativa y es útil para detectar sobreesfuerzo.

---

## Modelo de Clasificación de Fallos

Se utiliza un modelo Random Forest para analizar los datos y clasificar los registros según presenten o no un fallo.

### Metodología
- Variables utilizadas: Temp_Aire, Temp_Proceso, Velocidad, Torque y Desgaste.
- División de los datos: 80 % para entrenamiento y 20 % para prueba.
- Algoritmo utilizado: `RandomForestClassifier`.
- Evaluación mediante métricas de clasificación.

### Resultados
El conjunto de datos presenta un desequilibrio entre registros con y sin fallos (3,39 % de fallos).

Por este motivo, no basta con fijarse en el porcentaje de aciertos general (98 %). También es importante comprobar cuántos fallos consigue detectar el modelo.

| Métrica | Resultado |
|---|---:|
| Precisión | 0,73 |
| Recall | 0,71 |
| F1-score | 0,72 |

### Interpretación
- El modelo consigue detectar aproximadamente 7 de cada 10 fallos del conjunto de prueba.
- También identifica algunos registros como fallos cuando realmente no lo son.
- Torque, Velocidad y Desgaste son las variables que más influyen en sus resultados.
- El modelo permite analizar los fallos a partir de los datos disponibles, pero no anticipa cuándo se producirá una avería.
---

## Limitaciones del Dataset

- `Fallo` y `Tipo_Fallo` no siempre están alineados  
- No hay datos temporales reales  
- No hay variables eléctricas (corriente, potencia)  
- Dataset desbalanceado (pocos fallos)

---

## Enfoque del Dashboard

El dashboard responde a:

1. ¿Qué tipos de fallo son más frecuentes?  
2. ¿Qué máquinas presentan mayor incidencia?  
3. ¿Qué variables tienen mayor importancia en el análisis de los fallos? 
4. ¿En qué condiciones operativas aumentan los fallos?  
5. ¿Qué porcentaje de registros presenta desgaste elevado?

---

## Arquitectura del Pipeline

CSV → Python (ETL) → MySQL → Modelado → Power BI → Dashboard Ejecutivo

---

## Visualizaciones

### Python
- Análisis de fallos  
- Matriz de correlación  
- Matriz de confusión  
- Importancia de variables

### Power BI
Dashboard interactivo conectado a MySQL.

---

## Estructura del Proyecto

- `data/` → dataset original  
- `outputs/` → máquinas críticas  
- `reports/` → gráficas y métricas  
- `scripts/` → ETL, análisis y modelo  
- `sql/` → consultas SQL  
- `dashboard/` → archivo `.pbix` 
- `README.md`  
- `requirements.txt`  
- `.env.example`  
- `.gitignore`  

---

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/usuario/proyecto-industrial.git
cd proyecto-industrial
```

### 2. Crear un entorno virtual

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar las variables de entorno

Copiar el archivo `.env.example` y crear uno nuevo llamado `.env`, completando los datos de conexión a MySQL.

### 6. Cargar los datos en MySQL

```bash
python scripts/database_upload.py
```

### 7. Ejecutar el análisis y el modelo

```bash
python scripts/analisis_visual.py
python scripts/modelo_predictivo.py
```

### 8. Generar el reporte de máquinas críticas

```bash
python scripts/generar_reporte.py
```

### 9. Abrir el dashboard

Abrir `dashboard/Mantenimiento_Predictivo_Industrial.pbix` con Power BI Desktop.

---

## Conclusiones

- Los registros con mayor Índice de Esfuerzo Mecánico presentan una mayor proporción de fallos.
- Las máquinas tipo L presentan la mayor tasa de fallo dentro del conjunto analizado.
- Torque, Velocidad y Desgaste son las variables más importantes para el modelo Random Forest.
- El modelo consigue identificar aproximadamente el 71 % de los fallos del conjunto de prueba.

## Impacto

Este proyecto permite:

- Analizar los datos de funcionamiento de las máquinas.
- Identificar patrones relacionados con los fallos.
- Detectar registros que presentan condiciones operativas que merecen atención.
- Consultar los principales resultados mediante un dashboard interactivo.

El proyecto reúne distintas herramientas de análisis de datos en un mismo proceso, desde la limpieza y almacenamiento de la información hasta el análisis y la visualización de resultados.

---

## Licencia

El código de este proyecto se distribuye bajo la licencia MIT. Esta licencia no se extiende a los datos ni a los recursos de terceros utilizados en el análisis, que mantienen sus respectivas condiciones de uso.