import json
from datetime import date

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for

from config import ACCESS_CODE, BASE_URL, DEBUG, PLANT_NAME, PORT, SECRET_KEY

from barcodes import (
    generate_barcode_png,
    generate_qr_png,
    parse_scan_input,
    ubt_scan_url,
    ubt_to_barcode,
)
from ubt_units import UBT_UNITS, is_valid_ubt, normalize_ubt
from maquinas import MAQUINAS, MAQUINA_OPTIONS, maquina_label
from tecnicos import TECNICOS
from database import get_connection, init_db
from network import get_lan_ip
from pdf_codigos import generate_codigos_pdf

app = Flask(__name__)
app.secret_key = SECRET_KEY


def is_authenticated():
    return session.get("authenticated") is True


@app.get("/api/acceso")
def verificar_acceso():
    return jsonify({"authenticated": is_authenticated()})


@app.post("/api/acceso")
def login_acceso():
    data = request.get_json(silent=True) or {}
    codigo = (data.get("codigo") or "").strip()
    if codigo != ACCESS_CODE:
        return jsonify({"error": "Código de acceso incorrecto."}), 401
    session["authenticated"] = True
    return jsonify({"authenticated": True})


@app.before_request
def require_auth_for_api():
    public_api_paths = {"/api/acceso", "/api/escanear"}
    if request.path.startswith("/api/") and request.path not in public_api_paths:
        if not is_authenticated():
            return jsonify({"error": "Ingresa el código de acceso."}), 401


def get_base_url():
    if BASE_URL:
        return BASE_URL
    host = request.host
    if host.startswith("127.0.0.1") or host.startswith("localhost"):
        return request.url_root.rstrip("/")
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    return f"{scheme}://{host}".rstrip("/")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "plant": PLANT_NAME})


@app.before_request
def ensure_db():
    init_db()


def serialize_reparacion(row):
    return {
        "id": row["id"],
        "ubt": row["ubt"],
        "fecha": row["fecha"],
        "descripcion": row["descripcion"],
        "tecnico": row["tecnico"],
        "maquina": row["maquina"],
        "maquina_label": maquina_label(row["maquina"]),
        "tiempo_estimado_minutos": row["tiempo_estimado_minutos"],
        "created_at": row["created_at"],
        "repuestos": json.loads(row["repuestos"]),
    }


def fetch_reparaciones(ubt=None, fecha=None, tecnico=None, maquina=None):
    query = """
        SELECT
            r.id,
            r.ubt,
            r.fecha,
            r.descripcion,
            r.tecnico,
            r.maquina,
            r.tiempo_estimado_minutos,
            r.created_at,
            COALESCE(
                json_group_array(
                    json_object('nombre', p.nombre, 'cantidad', p.cantidad)
                ) FILTER (WHERE p.id IS NOT NULL),
                '[]'
            ) AS repuestos
        FROM reparaciones r
        LEFT JOIN repuestos p ON p.reparacion_id = r.id
        WHERE 1 = 1
    """
    params = []
    if ubt is not None:
        query += " AND r.ubt = ?"
        params.append(ubt)
    if fecha:
        query += " AND r.fecha = ?"
        params.append(fecha)
    if tecnico:
        query += " AND r.tecnico = ?"
        params.append(tecnico)
    if maquina:
        query += " AND r.maquina = ?"
        params.append(maquina)
    query += " GROUP BY r.id ORDER BY r.created_at DESC, r.id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [serialize_reparacion(row) for row in rows]


def validate_reparacion_payload(data):
    ubt = normalize_ubt(str(data.get("ubt") or "").strip())
    fecha = (data.get("fecha") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    tecnico = (data.get("tecnico") or "").strip()
    maquina = (data.get("maquina") or "").strip()
    tiempo_estimado_minutos = data.get("tiempo_estimado_minutos")
    repuestos = data.get("repuestos") or []

    errors = []
    if not is_valid_ubt(ubt):
        errors.append("Selecciona una UBT válida.")
    if not fecha:
        errors.append("La fecha es obligatoria.")
    if not descripcion:
        errors.append("La descripción es obligatoria.")
    if tecnico not in TECNICOS:
        errors.append("Selecciona un técnico válido.")
    if maquina not in MAQUINAS:
        errors.append("Selecciona la máquina que reparaste.")
    try:
        tiempo_estimado_minutos = int(tiempo_estimado_minutos)
        if tiempo_estimado_minutos < 1:
            errors.append("El tiempo estimado debe ser mayor a cero.")
    except (TypeError, ValueError):
        errors.append("El tiempo estimado es obligatorio.")
        tiempo_estimado_minutos = None

    cleaned_repuestos = []
    for item in repuestos:
        nombre = (item.get("nombre") or "").strip()
        cantidad = item.get("cantidad", 1)
        if not nombre:
            continue
        try:
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            errors.append("La cantidad de repuestos debe ser un número entero.")
            break
        if cantidad < 1:
            errors.append("La cantidad de repuestos debe ser mayor a cero.")
            break
        cleaned_repuestos.append({"nombre": nombre, "cantidad": cantidad})

    return errors, ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos, cleaned_repuestos


def render_escanear(initial_ubt=None):
    return render_template(
        "escanear.html",
        ubt_options=UBT_UNITS,
        today=date.today().isoformat(),
        initial_ubt=initial_ubt,
        maquinas=MAQUINA_OPTIONS,
        tecnicos=TECNICOS,
    )


@app.get("/")
def escanear():
    ubt = normalize_ubt(request.args.get("ubt", ""))
    if is_valid_ubt(ubt):
        return render_escanear(initial_ubt=ubt)
    return render_escanear()


@app.get("/u/<path:ubt_code>")
def escanear_ubt(ubt_code):
    ubt = normalize_ubt(ubt_code)
    if not is_valid_ubt(ubt):
        return redirect(url_for("escanear"))
    return render_escanear(initial_ubt=ubt)


@app.get("/registro")
def registro():
    return render_template("index.html", ubt_options=UBT_UNITS, maquinas=MAQUINA_OPTIONS, tecnicos=TECNICOS)


@app.get("/historial")
def historial():
    return render_template(
        "historial.html",
        ubt_options=UBT_UNITS,
        maquinas=MAQUINA_OPTIONS,
        tecnicos=TECNICOS,
    )


@app.get("/codigos")
def codigos():
    base_url = request.args.get("servidor") or get_base_url()
    if "127.0.0.1" in base_url or "localhost" in base_url:
        base_url = f"http://{get_lan_ip()}:{PORT}"
    return render_template(
        "codigos.html",
        ubt_options=UBT_UNITS,
        base_url=base_url,
        plant_name=PLANT_NAME,
        labels=[
            {
                "ubt": ubt,
                "code": ubt_to_barcode(ubt),
                "url": ubt_scan_url(base_url, ubt),
            }
            for ubt in UBT_UNITS
        ],
    )


@app.get("/codigos.pdf")
def codigos_pdf():
    base_url = request.args.get("servidor") or get_base_url()
    pdf_bytes = generate_codigos_pdf(base_url)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=ubt-codigos-qr.pdf"},
    )


@app.get("/codigos-barra/<path:ubt_code>.png")
def codigo_barra_imagen(ubt_code):
    ubt = normalize_ubt(ubt_code)
    if not is_valid_ubt(ubt):
        return jsonify({"error": "UBT no válida."}), 404
    return Response(generate_barcode_png(ubt), mimetype="image/png")


@app.get("/codigos-qr/<path:ubt_code>.png")
def codigo_qr_imagen(ubt_code):
    ubt = normalize_ubt(ubt_code)
    if not is_valid_ubt(ubt):
        return jsonify({"error": "UBT no válida."}), 404
    base_url = request.args.get("servidor") or get_base_url()
    scan_url = ubt_scan_url(base_url, ubt)
    return Response(generate_qr_png(scan_url), mimetype="image/png")


@app.post("/api/escanear")
def escanear_codigo():
    data = request.get_json(silent=True) or {}
    code = data.get("codigo") or request.form.get("codigo") or ""
    ubt = parse_scan_input(code)
    if ubt is None:
        return jsonify({"error": "Código no reconocido."}), 400
    return jsonify({"ubt": ubt, "codigo": ubt_to_barcode(ubt), "mensaje": f"UBT {ubt}"})


@app.get("/api/reparaciones")
def list_reparaciones():
    ubt = normalize_ubt(request.args.get("ubt", ""))
    if not is_valid_ubt(ubt):
        ubt = None
    fecha = request.args.get("fecha", type=str) or None
    tecnico = request.args.get("tecnico", type=str) or None
    maquina = request.args.get("maquina", type=str) or None
    repairs = fetch_reparaciones(ubt=ubt, fecha=fecha, tecnico=tecnico, maquina=maquina)
    return jsonify({"total": len(repairs), "reparaciones": repairs})


@app.get("/api/reparaciones/hoy")
def list_reparaciones_hoy():
    ubt = normalize_ubt(request.args.get("ubt", ""))
    if not is_valid_ubt(ubt):
        ubt = None
    fecha = request.args.get("fecha", date.today().isoformat())
    repairs = fetch_reparaciones(ubt=ubt, fecha=fecha)
    return jsonify({"fecha": fecha, "total": len(repairs), "reparaciones": repairs})


@app.post("/api/reparaciones")
def create_reparacion():
    data = request.get_json(silent=True) or {}
    errors, ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos, cleaned_repuestos = validate_reparacion_payload(data)
    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reparaciones (ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos),
        )
        reparacion_id = cursor.lastrowid
        for repuesto in cleaned_repuestos:
            conn.execute(
                """
                INSERT INTO repuestos (reparacion_id, nombre, cantidad)
                VALUES (?, ?, ?)
                """,
                (reparacion_id, repuesto["nombre"], repuesto["cantidad"]),
            )
        row = conn.execute(
            """
            SELECT
                r.id,
                r.ubt,
                r.fecha,
                r.descripcion,
                r.tecnico,
                r.maquina,
                r.tiempo_estimado_minutos,
                r.created_at,
                COALESCE(
                    json_group_array(
                        json_object('nombre', p.nombre, 'cantidad', p.cantidad)
                    ) FILTER (WHERE p.id IS NOT NULL),
                    '[]'
                ) AS repuestos
            FROM reparaciones r
            LEFT JOIN repuestos p ON p.reparacion_id = r.id
            WHERE r.id = ?
            GROUP BY r.id
            """,
            (reparacion_id,),
        ).fetchone()

    return jsonify(serialize_reparacion(row)), 201


@app.get("/api/resumen")
def resumen():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ubt, COUNT(*) AS total
            FROM reparaciones
            GROUP BY ubt
            ORDER BY ubt
            """
        ).fetchall()

    counts = {unit: 0 for unit in UBT_UNITS}
    for row in rows:
        counts[row["ubt"]] = row["total"]
    return jsonify(counts)


@app.get("/api/resumen/hoy")
def resumen_hoy():
    fecha = request.args.get("fecha", date.today().isoformat())
    ubt = normalize_ubt(request.args.get("ubt", ""))
    if not is_valid_ubt(ubt):
        ubt = None
    query = """
        SELECT ubt, COUNT(*) AS total
        FROM reparaciones
        WHERE fecha = ?
    """
    params = [fecha]
    if ubt is not None:
        query += " AND ubt = ?"
        params.append(ubt)
    query += " GROUP BY ubt ORDER BY ubt"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    counts = {unit: 0 for unit in UBT_UNITS}
    for row in rows:
        counts[row["ubt"]] = row["total"]
    total = sum(counts.values())

    tiempo_query = """
        SELECT COALESCE(SUM(tiempo_estimado_minutos), 0) AS tiempo_total
        FROM reparaciones
        WHERE fecha = ?
    """
    tiempo_params = [fecha]
    if ubt is not None:
        tiempo_query += " AND ubt = ?"
        tiempo_params.append(ubt)

    with get_connection() as conn:
        tiempo_total = conn.execute(tiempo_query, tiempo_params).fetchone()["tiempo_total"]

    return jsonify({
        "fecha": fecha,
        "total": total,
        "por_ubt": counts,
        "ubt": ubt,
        "tiempo_total_minutos": tiempo_total,
    })


if __name__ == "__main__":
    from network import get_lan_ip

    init_db()
    lan_ip = get_lan_ip()
    print(f"UBT Fix - {PLANT_NAME}")
    print(f"Red planta: http://{lan_ip}:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
