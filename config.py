import os

SECRET_KEY = os.environ.get("SECRET_KEY", "ubt-fix-planta-2-tb-cambiar-en-produccion")
ACCESS_CODE = os.environ.get("ACCESS_CODE", "1010")
PLANT_NAME = os.environ.get("PLANT_NAME", "Planta 2 TB")
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
