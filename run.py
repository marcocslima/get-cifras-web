# get-cifras-web/run.py

from app import app_flask # Importa a instância do app do pacote 'app' (app/__init__.py)

if __name__ == '__main__':
    # host='0.0.0.0' torna o servidor acessível na sua rede local
    # útil para testar em outros dispositivos na mesma rede.
    # Em produção, você usaria um servidor WSGI como Gunicorn.
    app_flask.run(debug=app_flask.config.get('DEBUG', True), host='0.0.0.0', port=5000)