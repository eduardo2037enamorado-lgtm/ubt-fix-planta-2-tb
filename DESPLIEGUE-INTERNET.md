# Usar UBT Fix con datos moviles (sin WiFi en planta)

Sin WiFi en planta, la app debe estar en **internet** para que los tecnicos la abran con **datos moviles (4G/5G)**.

## Opcion recomendada: Render (gratis)

### 1. Subir el proyecto a GitHub
1. Crea una cuenta en https://github.com
2. Crea un repositorio nuevo (ejemplo: `ubt-fix-planta-2-tb`)
3. Sube la carpeta del proyecto

### 2. Publicar en Render
1. Entra a https://render.com y crea cuenta
2. Clic en **New +** → **Web Service**
3. Conecta tu repositorio de GitHub
4. Render detecta la configuracion automaticamente (`render.yaml`)
5. Clic en **Deploy**

En unos minutos tendras una URL como:
**https://ubt-fix-planta-2-tb.onrender.com**

### 3. Generar etiquetas QR con la URL de internet
1. Abre en el navegador: `https://TU-URL.onrender.com/codigos`
2. Verifica que la direccion sea la de internet (no localhost)
3. Clic en **Descargar PDF**
4. Imprime y pega las etiquetas en cada UBT

### 4. Uso del tecnico (solo datos moviles)
1. Escanear QR de la maquina con la camara del celular
2. Se abre la app por internet
3. Ingresar codigo: **1010**
4. Registrar la reparacion

## Datos importantes

| Dato | Valor |
|------|-------|
| Codigo de acceso | 1010 |
| Tecnico | Seleccionar de la lista |
| Conexion | Datos moviles del celular |

## Nota sobre plan gratis de Render
- La app puede tardar unos segundos al abrir si no se uso recientemente
- Los datos se guardan en la nube mientras el servicio este activo

## Si prefieres no usar la nube
Necesitas una PC en planta con **internet por cable** y un tunel como **ngrok** o **Cloudflare Tunnel** para exponer la app a internet. Es mas tecnico; la nube es mas simple sin WiFi.

## Cambiar codigo de acceso en la nube
En Render → tu servicio → **Environment** → cambia `ACCESS_CODE`
