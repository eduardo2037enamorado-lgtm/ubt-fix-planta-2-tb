# UBT Fix Planta 2 TB

Aplicación web para registrar reparaciones de las UBT 601 a 612 en Planta 2 TB.

## Requisitos

- Python 3.10 o superior

## Instalación

```powershell
cd C:\Users\Tigre\Projects\reparaciones-ubt
python -m pip install -r requirements.txt
```

## Ejecutar

```powershell
python app.py
```

Abre el navegador en: http://localhost:5000

## Uso con celular (recomendado)

1. Inicia el servidor en la PC: `python app.py`
2. Desde la PC abre **Etiquetas QR** con la IP de red, por ejemplo: `http://192.168.1.38:5000/codigos`
3. Verifica que la dirección del servidor sea la IP correcta (no `localhost`)
4. Imprime y pega un QR en cada máquina (UBT 601 a 612)
5. El técnico escanea el QR con la **cámara del celular**
6. Se abre la app, identifica la UBT y muestra el registro diario de esa máquina
7. El técnico registra la reparación y guarda

También puede usar **Abrir cámara** dentro de la app para escanear sin salir del navegador.

## Funciones

- Código QR único por UBT (601-612) que abre la app al escanear
- Identificación automática de la máquina
- Registro diario por UBT
- Fecha, técnico, descripción y repuestos
- Historial completo en Registro manual
- Resumen por unidad

Los datos se guardan en `reparaciones.db` (SQLite).
