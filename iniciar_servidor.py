from app import app
from config import DEBUG, PLANT_NAME, PORT
from database import init_db
from network import get_lan_ip

if __name__ == "__main__":
    init_db()
    lan_ip = get_lan_ip()
    print("=" * 50)
    print(f"  UBT Fix - {PLANT_NAME}")
    print("=" * 50)
    print(f"  PC local:    http://127.0.0.1:{PORT}")
    print(f"  Red planta:  http://{lan_ip}:{PORT}")
    print(f"  Etiquetas:   http://{lan_ip}:{PORT}/codigos")
    print(f"  PDF QR:      http://{lan_ip}:{PORT}/codigos.pdf")
    print(f"  Codigo app:  1010")
    print("=" * 50)
    print("  Deja esta ventana abierta mientras trabajas.")
    print("=" * 50)
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
