import sys
from pathlib import Path

from pdf_codigos import generate_codigos_pdf


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_pdf.py https://tu-app.onrender.com")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    pdf_bytes = generate_codigos_pdf(base_url)
    output = Path(__file__).parent / "ubt-codigos-qr.pdf"
    output.write_bytes(pdf_bytes)
    print(f"PDF generado: {output}")
    print(f"URL usada: {base_url}")


if __name__ == "__main__":
    main()
