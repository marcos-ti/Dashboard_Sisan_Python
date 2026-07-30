from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o sistema
load_dotenv()

# Inicializa o cliente do Gemini puxando a variável segura
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

app = Flask(__name__)

# Variável global para guardar os KPIs e dados processados
kpi_cache = {}
df_global = None  # Variável global para o DataFrame do Excel

print("Carregando e processando base de dados do Excel...")
try:
    # 1. Carregamento do arquivo Excel bruto para um DataFrame do Pandas
    df_global = pd.read_excel("Base_Painel_Indicadores_municipais.xlsx")
    
    # Substitui valores nulos/vazios por strings vazias para evitar erros nas operações de string
    df_global = df_global.fillna("")
    
    # Mapeamento exato das colunas conforme a sua base
    col_adesao = 'Adesão (atualizado em mar/2026)'
    col_ano = 'Ano de adesão ao SISAN'
    col_resolucao = 'Resolução de Adesão ao SISAN (mar/2026)'
    col_mun = 'Código do Município'
    col_nome_mun = 'Nome do município (IBGE)'
    col_nome_regiao = 'Região'
    col_habitantes = 'Número de habitantes (Censo 2022)'
    col_rm = 'RM'
    col_uf = 'UF'  # Sigla UF
    
    # Geo Referenciamento
    col_geo = 'georef_location'
    col_lat = 'lat'
    col_long = 'long'
    col_ibge7 = 'geocodigo'

    # CÁLCULO 1: Total de Municípios
    total = len(df_global)
    
    # Inicializa variáveis padrão
    aderidos = 0
    sem_adesao = total
    
    if col_adesao in df_global.columns:
        v_adesao = df_global[col_adesao].astype(str).str.strip().str.lower()
        
        # CÁLCULO 3: Municípios Aderidos
        aderidos = int(v_adesao.isin(['sim', 's', 'aderido']).sum())
        
        # CÁLCULO 4: Sem Adesão ao SISAN
        sem_adesao = int(v_adesao.isin(['nao', 'não', 'n', '']).sum())

    em_processo = 0 
    suspensa = 0    

    # CÁLCULO 7: Evolução das Adesões por Ano (Gráfico de Barras) - Ordem decrescente (começando em 2026)
    evolucao_anos = []
    evolucao_valores = []
    
    if col_adesao in df_global.columns and col_ano in df_global.columns:
        mask = (v_adesao.isin(['sim', 's', 'aderido'])) & (~df_global[col_ano].astype(str).str.strip().isin(['-', '', 'nan', 'NaT', 'DF aderido']))
        df_filtrado = df_global[mask].copy()
        
        if not df_filtrado.empty:
            df_filtrado['ano_num'] = pd.to_numeric(df_filtrado[col_ano], errors='coerce')
            df_filtrado = df_filtrado.dropna(subset=['ano_num'])
            
            df_evolucao = df_filtrado.groupby('ano_num').size().reset_index(name='quantidade')
            df_evolucao = df_evolucao.sort_values(by='ano_num', ascending=False)

            evolucao_anos = df_evolucao['ano_num'].astype(int).astype(str).tolist()
            evolucao_valores = df_evolucao['quantidade'].tolist()

    # CÁLCULO 8: Resoluções por Ano (Tabela e Detalhes de Municípios)
    tabela_resolucoes = []
    
    if all(c in df_global.columns for c in [col_resolucao, col_ano, col_adesao, col_mun]):
        df_aderidos = df_global[v_adesao.isin(['sim', 's', 'aderido'])].copy()
        df_aderidos = df_aderidos[~df_aderidos[col_resolucao].astype(str).str.strip().isin(['-', '', 'nan', 'NaT', 'None'])]
        
        df_aderidos = df_aderidos[~df_aderidos[col_ano].astype(str).str.strip().isin(['-', '', 'nan', 'NaT', 'None', 'DF aderido'])]
        df_aderidos['ano_num'] = pd.to_numeric(df_aderidos[col_ano], errors='coerce')
        df_aderidos = df_aderidos.dropna(subset=['ano_num'])
        
        if not df_aderidos.empty:
            for ano, df_ano in sorted(df_aderidos.groupby('ano_num'), key=lambda x: x[0], reverse=True):
                ano_str = str(int(ano))
                resolucoes_do_ano = []
                
                for resolucao, df_res in df_ano.groupby(col_resolucao):
                    res_str = str(resolucao).strip()
                    if res_str in ['-', '', 'nan', 'NaT', 'None']:
                        continue
                        
                    resolucoes_do_ano.append({
                        "resolucao": res_str,
                        "quantidade": len(df_res),
                        "municipios": df_res.to_dict(orient='records')
                    })
                
                if resolucoes_do_ano:
                    tabela_resolucoes.append({
                        "ano": ano_str,
                        "resolucoes": resolucoes_do_ano,
                        "total_ano": sum(r["quantidade"] for r in resolucoes_do_ano)
                    })

    # CÁLCULO 9: Dados por Município/UF para o Mapa Interativo
    status_por_uf = {}
    if col_uf in df_global.columns and col_adesao in df_global.columns:
        df_uf = df_global.groupby(col_uf)[col_adesao].agg(
            total_mun='count',
            aderidos=lambda x: sum(str(v).strip().lower() in ['sim', 's', 'aderido'] for v in x)
        ).reset_index()
        
        for _, row in df_uf.iterrows():
            uf_sigla = str(row[col_uf]).strip().upper()
            status_por_uf[uf_sigla] = {
                "total": int(row['total_mun']),
                "aderidos": int(row['aderidos'])
            }

    # CÁLCULO 10: Lista de Municípios para o Filtro Analítico
    lista_municipios = []
    if col_nome_mun in df_global.columns and col_uf in df_global.columns:
        df_mun_sorted = df_global[[col_nome_mun, col_uf]].drop_duplicates().sort_values(by=col_nome_mun)
        for _, row in df_mun_sorted.iterrows():
            nome = str(row[col_nome_mun]).strip()
            uf = str(row[col_uf]).strip().upper()
            if nome and nome != 'nan':
                lista_municipios.append(f"{nome} ({uf})")

    kpi_cache = {
        "total": total,
        "aderidos": aderidos,
        "sem_adesao": sem_adesao,
        "em_processo": em_processo,
        "suspensa": suspensa,
        "evolucao_anos": evolucao_anos,
        "evolucao_valores": evolucao_valores,
        "tabela_resolucoes": tabela_resolucoes,
        "status_por_uf": status_por_uf,
        "lista_municipios": lista_municipios
    }
    
    print(f"Base processada com sucesso! Total: {total} registros.")
except Exception as e:
    print(f"Erro ao processar a planilha: {e}")
    kpi_cache = {
        "total": 0, "aderidos": 0, "sem_adesao": 0, 
        "em_processo": 0, "suspensa": 0, 
        "evolucao_anos": [], "evolucao_valores": [], "tabela_resolucoes": [], "status_por_uf": {}, "lista_municipios": []
    }

# Rotas principais
@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/monitoramento")
def monitoramento():
    return render_template("monitoramento_das_adesoes.html")

# Rota de API: entrega os cálculos prontos em formato JSON para o front-end
@app.route("/api/dados")
def api_dados():
    return jsonify(kpi_cache)

# Rota de API para o mapa georreferenciado
@app.route("/api/mapa_georef")
def api_mapa_georef():
    dados_geo = []
    try:
        if df_global is None:
            return jsonify([])
            
        df_local = df_global.copy()
        df_local.columns = df_local.columns.str.strip().str.replace('\n', '').str.replace('\r', '')

        col_adesao = 'Adesão (atualizado em mar/2026)'
        col_resolucao = 'Resolução de Adesão ao SISAN (mar/2026)'
        col_nome_mun = 'Nome do município (IBGE)'
        col_uf = 'UF'
        col_lat = 'lat'
        col_long = 'long'
        col_ibge7 = 'geocodigo'

        limites_uf = {
            'RO': (-13.8, -7.9, -66.8, -59.8), 'AC': (-11.2, -7.1, -74.0, -66.6),
            'AM': (-9.8, 2.3, -73.8, -56.1), 'RR': (-1.6, 5.3, -64.8, -58.8),
            'PA': (-9.9, 2.6, -58.9, -46.0), 'AP': (-1.4, 4.4, -54.9, -49.9),
            'TO': (-13.5, -5.0, -50.9, -45.7), 'MA': (-10.5, -1.2, -48.7, -40.2),
            'PI': (-10.9, -2.7, -45.9, -40.3), 'CE': (-7.6, -2.7, -41.4, -37.2),
            'RN': (-6.8, -4.7, -38.6, -34.9), 'PB': (-8.3, -6.0, -38.8, -34.7),
            'PE': (-9.5, -7.2, -41.4, -34.8), 'AL': (-10.5, -8.8, -38.2, -35.1),
            'SE': (-11.6, -9.5, -38.2, -36.4), 'BA': (-18.4, -8.5, -46.6, -37.3),
            'MG': (-22.9, -14.2, -51.0, -39.8), 'ES': (-21.3, -17.8, -41.9, -39.6),
            'RJ': (-23.4, -20.7, -44.9, -40.9), 'SP': (-25.4, -19.8, -53.1, -44.1),
            'PR': (-26.7, -22.5, -54.6, -48.0), 'SC': (-29.4, -25.9, -53.8, -48.3),
            'RS': (-33.8, -27.0, -57.6, -49.6), 'MS': (-24.5, -17.2, -58.2, -50.9),
            'MT': (-18.0, -9.6, -61.3, -50.2), 'GO': (-19.5, -12.4, -53.2, -45.9),
            'DF': (-16.1, -15.5, -48.3, -47.3)
        }

        for _, row in df_local.iterrows():
            try:
                ibge_raw = row.get(col_ibge7, '')
                if pd.isna(ibge_raw):
                    continue
                
                ibge_str = str(ibge_raw).strip()
                if '.' in ibge_str:
                    ibge_str = ibge_str.split('.')[0]
                
                if not ibge_str.isdigit() or len(ibge_str) != 7:
                    continue

                raw_lat = row.get(col_lat, '')
                raw_long = row.get(col_long, '')

                if pd.isna(raw_lat) or pd.isna(raw_long) or str(raw_lat).strip() == '' or str(raw_long).strip() == '':
                    continue

                val_lat = float(raw_lat)
                val_long = float(raw_long)

                lat = val_lat / 1000.0 if abs(val_lat) > 180 else val_lat
                long = val_long / 1000.0 if abs(val_long) > 180 else val_long

                if not (-34.5 <= lat <= 5.3 and -74.0 <= long <= -32.4):
                    if -34.5 <= long <= 5.3 and -74.0 <= lat <= -32.4:
                        lat, long = long, lat
                    else:
                        continue

                uf_mun = str(row.get(col_uf, '')).strip().upper()
                
                if uf_mun in limites_uf:
                    min_lat, max_lat, min_long, max_long = limites_uf[uf_mun]
                    if not (min_lat <= lat <= max_lat and min_long <= long <= max_long):
                        continue
                else:
                    if not (-34.0 <= lat <= 5.3 and -73.9 <= long <= -34.7):
                        continue

                status_adesao = str(row.get(col_adesao, '')).strip().lower()
                is_aderido = status_adesao in ['sim', 's', 'aderido']
                
                nome_mun = str(row.get(col_nome_mun, 'Município')).strip()
                
                resolucao = "Sem resolução"
                res_val = str(row.get(col_resolucao, '')).strip()
                if res_val.lower() not in ['nan', 'none', '-', '', 'nat']:
                    resolucao = res_val
                    
                dados_geo.append({
                    "nome": nome_mun,
                    "uf": uf_mun,
                    "ibge": ibge_str,
                    "lat": lat,
                    "long": long,
                    "aderido": is_aderido,
                    "resolucao": resolucao
                })
            except (ValueError, TypeError):
                continue
    except Exception as e:
        print(f"Erro: {e}")

    return jsonify(dados_geo)


# Inicializa o cliente do Gemini lendo a chave da variável de ambiente ou injetando de forma direta

# Lê a chave diretamente da variável de ambiente do seu computador
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


@app.route("/api/consulta-ia", methods=["POST"])
def consulta_ia():
    try:
        dados_requisicao = request.get_json()
        pergunta_usuario = dados_requisicao.get("prompt", "").strip()

        if not pergunta_usuario:
            return jsonify({"erro": "Nenhum prompt foi fornecido."}), 400

        if df_global is None:
            return jsonify({"erro": "Base de dados não carregada."}), 500

        colunas_disponiveis = list(df_global.columns)

        # 1. CRIAÇÃO DE UMA AMOSTRA INTELIGENTE (Pega um pouco de cada Estado, evitando focar só em RO)
        amostra_balanceada = []
        if 'UF' in df_global.columns:
            # Pega até 2 linhas de cada UF para o Gemini entender que o Brasil inteiro está presente
            for uf, grupo in df_global.groupby('UF'):
                amostra_balanceada.append(grupo.head(2))
            df_amostra = pd.concat(amostra_balanceada) if amostra_balanceada else df_global.head(30)
        else:
            df_amostra = df_global.head(30)

        amostra_dados = df_amostra.to_dict(orient="records")
        
        resumo_info = {
            "total_registros_base": len(df_global),
            "ufs_disponiveis": sorted(df_global['UF'].astype(str).unique().tolist()) if 'UF' in df_global.columns else []
        }

        # 2. INSTRUÇÃO RIGOROSA PARA O GEMINI
        system_instruction = (
            "Você é um assistente analítico avançado especializado no SISAN. "
            "A base de dados possui informações de MÚLTIPLOS ESTADOS DO BRASIL (veja a lista de UFs disponíveis nos metadados). "
            "ATENÇÃO: Nunca filtre apenas por um estado (como RO) a menos que o usuário peça explicitamente. "
            "Se o usuário fizer uma pergunta geral (ex: 'Adesões ao Sisan'), retorne dados variados de diferentes estados do país, "
            "respeitando rigorosamente o formato JSON de colunas e linhas solicitado."
        )

        prompt_enviado = (
            f"Metadados da base: {json.dumps(resumo_info, ensure_ascii=False)}\n"
            f"Colunas disponíveis: {colunas_disponiveis}\n"
            f"Amostra representativa (com vários estados): {json.dumps(amostra_dados, ensure_ascii=False)}\n\n"
            f"Pedido do usuário: {pergunta_usuario}"
        )

        # 3. CHAMADA AO GEMINI COM PARÂMETROS OTIMIZADOS
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt_enviado,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,  # Um pouco mais flexível para ele buscar variedade geográfica
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "colunas": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING),
                            description="Nomes das colunas da tabela."
                        ),
                        "linhas": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.STRING),
                            ),
                            description="Matriz de linhas correspondentes."
                        )
                    },
                    required=["colunas", "linhas"]
                ),
            ),
        )

        resultado_json = json.loads(response.text)
        return jsonify(resultado_json)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    

if __name__ == "__main__":
    app.run(debug=True, port=5006)