
USE mantenimiento_industrial;

-- ============================================================
-- 1. VERIFICACIÓN INICIAL DE LA BASE DE DATOS
-- ============================================================

-- Comprobar estructura de la tabla.
DESCRIBE monitoreo_maquinas;

-- Comprobar registros y tasa global de fallo.
SELECT
    COUNT(*) AS Total_Registros,
    SUM(Fallo) AS Total_Fallos,
    ROUND(AVG(Fallo) * 100, 2) AS Tasa_Fallo_Pct
FROM monitoreo_maquinas;


-- ============================================================
-- 2. ANÁLISIS DE FALLOS POR TIPO DE MÁQUINA
-- ============================================================

SELECT
    Tipo,
    COUNT(*) AS Registros,
    SUM(Fallo) AS Total_Fallos,
    ROUND(100.0 * SUM(Fallo) / COUNT(*), 2) AS Tasa_Fallo_Pct,
    ROUND(AVG(Temp_Proceso), 2) AS Temp_Media_Proceso
FROM monitoreo_maquinas
GROUP BY Tipo
ORDER BY Tasa_Fallo_Pct DESC;


-- ============================================================
-- 3. ANÁLISIS DEL ESFUERZO MECÁNICO POR TIPO DE MÁQUINA
-- ============================================================

-- El índice Torque × Velocidad es un proxy de esfuerzo mecánico.
-- No representa una medición de energía ni de consumo real.

SELECT
    Tipo,
    COUNT(*) AS Registros,
    ROUND(AVG(Indice_Esfuerzo_Mecanico), 2) AS Esfuerzo_Medio,
    ROUND(MAX(Indice_Esfuerzo_Mecanico), 2) AS Esfuerzo_Maximo,
    ROUND(AVG(Torque), 2) AS Torque_Medio,
    ROUND(AVG(Velocidad), 2) AS Velocidad_Media
FROM monitoreo_maquinas
GROUP BY Tipo
ORDER BY Esfuerzo_Medio DESC;


-- ============================================================
-- 4. RELACIÓN ENTRE ESFUERZO ELEVADO Y TASA DE FALLO
-- ============================================================

-- Esfuerzo_Elevado = 1 identifica registros por encima
-- del percentil 75 del índice de esfuerzo.

SELECT
    Esfuerzo_Elevado,
    COUNT(*) AS Registros,
    SUM(Fallo) AS Total_Fallos,
    ROUND(AVG(Fallo) * 100, 2) AS Tasa_Fallo_Pct,
    ROUND(AVG(Indice_Esfuerzo_Mecanico), 2) AS Esfuerzo_Medio
FROM monitoreo_maquinas
GROUP BY Esfuerzo_Elevado
ORDER BY Esfuerzo_Elevado;


-- ============================================================
-- 5. DISTRIBUCIÓN DE LOS TIPOS DE FALLO
-- ============================================================

-- Se incluyen los registros con Fallo = 1.
-- La categoría No Failure permite identificar inconsistencias
-- entre la variable binaria Fallo y Tipo_Fallo.

SELECT
    Tipo_Fallo,
    COUNT(*) AS Total_Registros,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM monitoreo_maquinas WHERE Fallo = 1),
        2
    ) AS Porcentaje_Fallos
FROM monitoreo_maquinas
WHERE Fallo = 1
GROUP BY Tipo_Fallo
ORDER BY Total_Registros DESC;


-- ============================================================
-- 6. COMPROBACIÓN DE INCONSISTENCIAS EN LAS ETIQUETAS
-- ============================================================

-- Identificar registros en los que Fallo y Tipo_Fallo
-- no coinciden según las etiquetas originales.

SELECT
    Fallo,
    Tipo_Fallo,
    COUNT(*) AS Registros
FROM monitoreo_maquinas
WHERE
    (Fallo = 0 AND Tipo_Fallo <> 'No Failure')
    OR
    (Fallo = 1 AND Tipo_Fallo = 'No Failure')
GROUP BY Fallo, Tipo_Fallo
ORDER BY Fallo, Tipo_Fallo;


-- ============================================================
-- 7. DETALLE DE LOS REGISTROS CON ETIQUETAS INCONSISTENTES
-- ============================================================

SELECT
    UDI,
    Product_ID,
    Tipo,
    Fallo,
    Tipo_Fallo,
    Torque,
    Velocidad,
    Desgaste,
    Indice_Esfuerzo_Mecanico
FROM monitoreo_maquinas
WHERE
    (Fallo = 0 AND Tipo_Fallo <> 'No Failure')
    OR
    (Fallo = 1 AND Tipo_Fallo = 'No Failure')
ORDER BY UDI;
