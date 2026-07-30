# Painel SISAN - Monitoramento de Adesões Municipais

Este é um projeto web desenvolvido em **Python (Flask)** para o monitoramento de dados de adesão e indicadores do **SISAN (Sistema Nacional de Segurança Alimentar e Nutricional)** nos municípios brasileiros. O sistema processa uma base de dados em Excel utilizando **Pandas** e exibe as informações através de um painel interativo estilizado com **Bootstrap**.

---

## Demonstração e Links Oficiais

* ** Acessar o Sistema Online:** [Painel SISAN - Monitoramento](https://dashboard-sisan-python.onrender.com/monitoramento)
* ** Vídeo de Demonstração (1 min):** [Assistir no GitHub](https://github.com/marcos-ti/Dashboard_Sisan_Python/blob/main/Painel-Sisan-Python-IA-2026-07-30.mp4)

---

## Funcionalidades

* ** Indicadores Principais (KPIs):** Visão geral do total de municípios, municípios aderidos, sem adesão e status de processos.
* ** Evolução Temporal:** Gráficos interativos (via Chart.js) mostrando o histórico de adesões por ano.
* ** Mapa Interativo:** Visualização geoespacial das adesões por estado/UF utilizando Leaflet.js.
* ** Detalhamento por Resoluções:** Tabelas organizadas por ano e número de resolução, permitindo consultar os municípios correspondentes.
* ** Filtros e Responsividade:** Layout moderno e adaptável para diferentes tamanhos de tela (computadores, tablets e celulares) utilizando Bootstrap.
* ** Consulta Inteligente por IA:** Ferramenta de perguntas e respostas para extrair insights e dados do monitoramento do Sisan com o auxílio de inteligência artificial.

---

## Tecnologias Utilizadas

O projeto foi construído utilizando as seguintes tecnologias e bibliotecas:

* ** [Python](https://www.python.org/) ** (Versão 3.x)
* ** [Flask](https://flask.palletsprojects.com/) ** (Microframework web)
* ** [Pandas](https://pandas.pydata.org/) ** (Manipulação e análise de dados)
* ** [Openpyxl](https://openpyxl.readthedocs.io/) ** (Leitura de arquivos Excel)
* ** [Bootstrap 4.6](https://getbootstrap.com/) ** (Estilização e componentes visuais)
* ** [Chart.js](https://www.chartjs.org/) ** (Gráficos interativos)
* ** [Leaflet.js](https://leafletjs.com/) ** (Mapas interativos)
* ** [FontAwesome](https://fontawesome.com/) ** (Ícones)
* ** [Gunicorn](https://gunicorn.org/) ** (Servidor WSGI para produção)
* ** [Google GenAI](https://ai.google.dev/) ** (Integração com Inteligência Artificial)
* ** [Python-Dotenv](https://saurabh-kumar.com/python-dotenv/) ** (Gerenciamento de variáveis de ambiente)

---

## 📁 Estrutura do Projeto

```text
Dashboard_Sisan_Python/
│
├── static/                  # Arquivos estáticos (imagens, CSS, JavaScript, geolocalização)
├── templates/               # Arquivos HTML do projeto (Jinja2)
├── .env                     # Variáveis de ambiente locais (não versionado)
├── .gitignore               # Arquivos ignorados pelo Git
├── app.py                   # Arquivo principal do Flask com rotas e lógica de IA
├── requirements.txt         # Lista de dependências do projeto
├── README.md                # Documentação do projeto
├── Painel-Sisan-Python-IA-2026-07-30.mp4 # Vídeo de demonstração do sistema
└── Base_Painel_Indicadores_municipais.xlsx # Base de dados (Excel)
