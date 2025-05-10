# get-cifras-web/app/routes.py

from flask import render_template, request, Response, redirect, url_for, flash, session
from app import app_flask # Importa a instância do app de app/__init__.py
from app.scraper import buscar_musicas_artista, preparar_dados_cifras_csv
import io
import csv
from slugify import slugify

@app_flask.route('/', methods=['GET', 'POST'])
def index():
    musicas = []
    artista_buscado = session.get('ultimo_artista_buscado', '') # Pega da sessão se existir

    if request.method == 'POST':
        # Se o POST for para buscar artista (name="buscar_artista")
        if 'buscar_artista' in request.form:
            artista = request.form.get('artista')
            if artista:
                artista_buscado = artista
                session['ultimo_artista_buscado'] = artista # Salva na sessão
                print(f"Formulário de busca recebido para artista: {artista}")
                musicas = buscar_musicas_artista(artista)
                if not musicas:
                    flash(f"Nenhuma música encontrada para '{artista}' ou erro na busca. Verifique o nome ou tente novamente.", "warning")
                else:
                    flash(f"{len(musicas)} música(s) encontrada(s) para '{artista}'.", "info")
            else:
                flash("Por favor, insira o nome de um artista.", "warning")
                artista_buscado = "" # Limpa se o campo estiver vazio
                session.pop('ultimo_artista_buscado', None) # Remove da sessão
        
        # Se o POST for para gerar CSV (o form de gerar CSV é separado)
        # Esta lógica será movida para /gerar_csv, mas pode haver um POST aqui
        # se o usuário tentar submeter o form de busca sem preencher, por exemplo.

    # Se for GET e houver artista na sessão, tentar buscar automaticamente (opcional)
    elif request.method == 'GET' and artista_buscado:
         musicas = buscar_musicas_artista(artista_buscado)
         if not musicas and not get_flashed_messages(category_filter=["warning", "error"]):
             # Evita flash duplicado se já houve erro na tentativa de POST anterior
             flash(f"Tentando recarregar músicas para '{artista_buscado}', mas nada foi encontrado.", "info")


    return render_template('index.html', musicas=musicas, artista_buscado=artista_buscado)


@app_flask.route('/gerar_csv', methods=['POST'])
def gerar_csv():
    musicas_selecionadas_raw = request.form.getlist('musicas_selecionadas')
    # Pega o nome do artista do campo hidden ou da sessão como fallback
    artista_nome_original = request.form.get('artista_nome_original_csv') or session.get('ultimo_artista_buscado', 'artista_desconhecido')

    if not musicas_selecionadas_raw:
        flash("Nenhuma música selecionada para gerar o CSV.", "warning")
        return redirect(url_for('index'))

    musicas_info_para_processar = []
    for item_raw in musicas_selecionadas_raw:
        try:
            nome, url = item_raw.split('|', 1)
            musicas_info_para_processar.append((nome, url))
        except ValueError:
            print(f"Item selecionado mal formatado (ignorado): {item_raw}")
            continue
    
    if not musicas_info_para_processar:
        flash("Nenhuma música válida selecionada ou formato inválido.", "danger")
        return redirect(url_for('index'))

    dados_csv = preparar_dados_cifras_csv(musicas_info_para_processar)

    if not dados_csv:
        flash("Não foi possível gerar dados para o CSV (nenhum link de impressão encontrado para as músicas selecionadas).", "warning")
        return redirect(url_for('index'))

    # Criar CSV em memória
    si = io.StringIO()
    fieldnames = ['song_name', 'link']
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(dados_csv)
    
    output_csv = si.getvalue()
    si.close()

    nome_arquivo_csv = f"{slugify(artista_nome_original)}_cifras.csv"
    flash(f"CSV '{nome_arquivo_csv}' gerado com sucesso!", "success")

    return Response(
        output_csv,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{nome_arquivo_csv}\""} # Aspas no filename
    )

# Rota para limpar a sessão e o campo de busca (opcional)
@app_flask.route('/limpar', methods=['GET'])
def limpar_busca():
    session.pop('ultimo_artista_buscado', None)
    flash("Busca limpa.", "info")
    return redirect(url_for('index'))