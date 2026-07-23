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

## Almacenamiento permanente

En Render, el disco del servidor web es **temporal**: si solo usas SQLite, las reparaciones se pierden al reiniciar.

La app ahora usa **PostgreSQL** cuando existe la variable `DATABASE_URL`. El archivo `render.yaml` crea una base de datos en Render y la conecta automaticamente.

### Opcion A: Base de datos en Render (incluida en render.yaml)
1. En Render, abre tu servicio y verifica que exista la base `ubt-fix-db`
2. Si desplegaste antes sin base de datos, agrega una **PostgreSQL** en Render y copia su **Internal Database URL** a la variable `DATABASE_URL` del servicio web
3. Vuelve a desplegar

La base gratuita de Render dura 30 dias. Para guardar datos sin limite de tiempo, usa la opcion B o paga el plan de base de datos (~$6/mes).

### Opcion B: Neon (gratis y permanente, recomendado)
1. Crea cuenta en https://neon.tech
2. Crea un proyecto y copia la **Connection string**
3. En Render → tu servicio → **Environment** → agrega:
   - `DATABASE_URL` = la connection string de Neon
4. Guarda y espera el redespliegue

Las reparaciones quedan guardadas aunque el servidor web se reinicie.

## Nota sobre plan gratis de Render
- La app puede tardar unos segundos al abrir si no se uso recientemente
- Las reparaciones se guardan en PostgreSQL de forma permanente (no en el disco del servidor)

## Si prefieres no usar la nube
Necesitas una PC en planta con **internet por cable** y un tunel como **ngrok** o **Cloudflare Tunnel** para exponer la app a internet. Es mas tecnico; la nube es mas simple sin WiFi.

## Cambiar codigo de acceso en la nube
En Render → tu servicio → **Environment** → cambia `ACCESS_CODE`
