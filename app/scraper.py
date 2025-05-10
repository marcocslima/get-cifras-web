# get-cifras-web/app/scraper.py

import requests
from bs4 import BeautifulSoup
import re
from slugify import slugify # pip install python-slugify

BASE_URL = "https://www.cifraclub.com.br"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def buscar_musicas_artista(nome_artista):
    """
    Busca as músicas de um artista no Cifra Club.
    Retorna uma lista de tuplas (nome_musica, url_relativa_musica).
    """
    url_artista_slug = slugify(nome_artista)
    url_busca = f"{BASE_URL}/{url_artista_slug}/"
    musicas_encontradas = []
    headers = {'User-Agent': USER_AGENT}

    print(f"Buscando músicas para: {nome_artista} em {url_busca}")

    try:
        response = requests.get(url_busca, headers=headers, timeout=20) # Timeout aumentado
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tentar seletores mais robustos e comuns
        # 1. Lista principal de músicas com classes 'art_musics' ou 'list-links'
        song_list_container = soup.find('ul', class_=re.compile(r'(art_musics|list-links|songs-list)'))

        # 2. Fallback para <ol id="js-a-songs"> (estrutura mais antiga)
        if not song_list_container:
            song_list_container = soup.find('ol', id='js-a-songs')

        # 3. Fallback para um container mais genérico se os outros falharem
        if not song_list_container:
            # Tenta encontrar um div que pareça ser um container de abas de cifras
            tabs_container = soup.find('div', class_=re.compile(r'(g-tabs_content.*cifras|song-list-container)'))
            if tabs_container:
                song_list_container = tabs_container.find('ul') # Pega o primeiro <ul> dentro

        if song_list_container:
            # Dentro do container, procurar por tags <a> que tenham href
            links = song_list_container.find_all('a', href=True)
            for link_tag in links:
                href = link_tag['href']
                # O nome da música pode estar em um span específico ou ser o texto do link
                nome_musica_tag = link_tag.find('span', class_=re.compile(r'(art_music-song|song-name|title)'))
                nome_musica = nome_musica_tag.text.strip() if nome_musica_tag else link_tag.text.strip()

                # Validações para garantir que é um link de música do artista
                if nome_musica and href.startswith(f"/{url_artista_slug}/") and \
                   not href.endswith(f"/{url_artista_slug}/") and \
                   not any(kw in href for kw in ['/videoaula/', '/tabs/', '/imprimir.html', '/partituras/', 'javascript:;']):
                    musicas_encontradas.append((nome_musica, href))
        else:
            print(f"HTML da busca por {nome_artista} não contém lista de músicas esperada.")
            # Para depuração, você pode querer salvar o HTML:
            # with open(f"debug_{url_artista_slug}.html", "w", encoding="utf-8") as f:
            #     f.write(soup.prettify())
            return [] # Retorna lista vazia se nenhum container for encontrado

        # Remover duplicatas e ordenar
        if musicas_encontradas:
            # Usar um set de tuplas para remover duplicatas e depois converter de volta para lista e ordenar
            musicas_encontradas = sorted(list(set(musicas_encontradas)), key=lambda x: x[0].lower())
        
        print(f"Encontradas {len(musicas_encontradas)} músicas para {nome_artista}.")
        return musicas_encontradas

    except requests.RequestException as e:
        print(f"Erro na requisição ao buscar músicas de {nome_artista}: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado ao processar músicas de {nome_artista}: {e}")
        return []


def obter_link_impressao_cifra(url_relativa_musica):
    """
    Obtém o link da versão de impressão de uma cifra.
    Retorna a URL completa de impressão ou None.
    """
    if not url_relativa_musica:
        return None

    # Garante que a URL relativa comece com / e não com o BASE_URL
    if url_relativa_musica.startswith(BASE_URL):
        url_relativa_musica = url_relativa_musica.replace(BASE_URL, "")
    if not url_relativa_musica.startswith("/"):
        url_relativa_musica = "/" + url_relativa_musica
        
    url_musica_completa = f"{BASE_URL}{url_relativa_musica}"
    headers = {'User-Agent': USER_AGENT}
    print(f"Buscando link de impressão para: {url_musica_completa}")

    try:
        response = requests.get(url_musica_completa, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tentativa 1: Botão de impressão com data-url-imprimir (mais comum e atual)
        print_button = soup.find(lambda tag: tag.name == 'a' and tag.has_attr('data-url-imprimir') and 'js-print' in tag.get('class', []))
        if not print_button: # Fallback para id (menos comum agora)
            print_button = soup.find('a', {'id': 'js-printButton', 'data-url-imprimir': True})

        if print_button and print_button.get('data-url-imprimir'):
            link_impressao_relativo = print_button['data-url-imprimir']
            # Garante que o link relativo comece com /
            if not link_impressao_relativo.startswith("/"):
                link_impressao_relativo = "/" + link_impressao_relativo
            url_impressao = f"{BASE_URL}{link_impressao_relativo}"
            print(f"  Link de impressão (botão): {url_impressao}")
            return url_impressao

        # Tentativa 2: Construir o link (padrão comum: /artista/musica/imprimir.html)
        # Remove query params e fragmentos da URL relativa antes de adicionar /imprimir.html
        base_path = url_relativa_musica.split('?')[0].split('#')[0]
        if base_path.endswith('/'):
            url_impressao_construida = f"{BASE_URL}{base_path}imprimir.html"
        else:
            url_impressao_construida = f"{BASE_URL}{base_path}/imprimir.html"
        
        print(f"  Link de impressão (construído): {url_impressao_construida}")
        return url_impressao_construida # Retorna o construído se o botão não for encontrado

    except requests.RequestException as e:
        print(f"Erro na requisição ao buscar página da música {url_musica_completa} para link de impressão: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao obter link de impressão para {url_musica_completa}: {e}")
        return None

def preparar_dados_cifras_csv(musicas_selecionadas_info):
    """
    Prepara os dados para o CSV.
    musicas_selecionadas_info: lista de tuplas (nome_musica_original, url_relativa_musica)
    Retorna uma lista de dicionários, cada um com {'song_name': ..., 'link': ...}.
    """
    dados_para_csv = []
    if not musicas_selecionadas_info:
        return dados_para_csv

    for nome_musica_original, url_relativa_musica in musicas_selecionadas_info:
        nome_musica_slug = slugify(nome_musica_original)
        print(f"Processando para CSV: {nome_musica_original} ({url_relativa_musica})")

        url_impressao_completa = obter_link_impressao_cifra(url_relativa_musica)

        if url_impressao_completa:
            print(f"  Link de impressão adicionado ao CSV: {url_impressao_completa}")
            dados_para_csv.append({
                'song_name': nome_musica_slug,
                'link': url_impressao_completa
            })
        else:
            print(f"  Não foi possível obter o link de impressão para CSV de {nome_musica_original}.")
            # Pode-se optar por adicionar uma entrada com link vazio ou uma nota de erro
            # dados_para_csv.append({'song_name': nome_musica_slug, 'link': 'ERRO_LINK_NAO_ENCONTRADO'})

    return dados_para_csv