# get-cifras-web/app/__init__.py

from flask import Flask
from config import Config # Importa a classe Config do arquivo config.py na raiz

app_flask = Flask(__name__)
app_flask.config.from_object(Config)

# A importação de 'routes' deve vir DEPOIS da criação de 'app_flask'
# para evitar importações circulares, pois routes.py importará app_flask.
from app import routes # noqa: E402, F401 (ignora avisos de linter para esta linha)