# get-cifras-web/config.py

import os

class Config:
    """Configurações base do aplicativo."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-bem-aleatoria-e-segura'
    DEBUG = True  # Mude para False em produção
    # Outras configurações podem ser adicionadas aqui, se necessário