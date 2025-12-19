"""
Migração de Processos - Planilha Lenon 2025 (106 processos embutidos)
Rota: /visao-geral/migracao-processos
"""
from typing import Dict, Any, List
from nicegui import ui
import re, unicodedata, difflib

from ...core import layout
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace
from ...firebase_config import ensure_firebase_initialized, get_auth
from .processos.database import atualizar_campos_processo, buscar_processo_por_numero, criar_processo
from .pessoas.database import listar_pessoas, listar_envolvidos, listar_parceiros

PROCESSOS = [
{"n":"5002318-80.2025.8.24.0055","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"JHONNY SCHMIDMEIER","l":"Rio Negrinho","s":"Crimes contra a Flora","d":"2025-08-29"},
{"n":"5001851-28.2024.8.24.0026","c":"Procedimento Comum Cível","a":"GERMANO WOEHL JUNIOR","r":"JOSE ADILSON KOBICHEN","l":"Guaramirim","s":"Direito de imagem","d":"2024-04-05"},
{"n":"5003892-54.2023.8.24.0041","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"REFLORESTA EMPREENDIMENTOS LTDA","l":"Mafra","s":"Destruição ou Degradação","d":"2023-07-06"},
{"n":"5007539-04.2024.8.24.0015","c":"Procedimento Comum Cível","a":"EDSON LUIS RAABE","r":"IMA","l":"Canoinhas","s":"Anulação de multa ambiental","d":"2024-10-22"},
{"n":"5002478-31.2025.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"WALDIR JANTSCH","l":"Canoinhas","s":"Flora","d":"2025-04-07"},
{"n":"5003737-61.2025.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"MARIA PAULA FRIEDRICH","l":"Canoinhas","s":"Flora","d":"2025-05-27"},
{"n":"5000817-85.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"PEDRO COLACO","l":"Canoinhas","s":"Destruição ou Degradação","d":"2023-01-31"},
{"n":"5006110-65.2025.8.24.0015","c":"Ação Penal","a":"MPSC","r":"PEDRO COLACO","l":"Canoinhas","s":"Destruição ou Degradação","d":"2025-08-27"},
{"n":"5005980-75.2025.8.24.0015","c":"Execução ANPP","a":"MPSC","r":"ANDRE DA SILVEIRA","l":"Canoinhas","s":"ANPP","d":"2025-08-22"},
{"n":"5000504-56.2025.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"ANDRE DA SILVEIRA","l":"Regional Mafra","s":"Destruição ou Degradação","d":"2025-01-24"},
{"n":"5008581-25.2023.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"MARIA TRINDADE NEVES","l":"Canoinhas","s":"Dano ambiental","d":"2023-10-24"},
{"n":"5008587-32.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"EDIVAL DOBRYCHTOP","l":"Canoinhas","s":"Fiscalização","d":"2023-10-24"},
{"n":"5000758-67.2024.8.24.0143","c":"Ação Penal","a":"MPSC","r":"VALDECIR DALCANAL","l":"Rio do Campo","s":"Destruição","d":"2024-06-24"},
{"n":"5001089-98.2023.8.24.0041","c":"Procedimento Comum Cível","a":"LUCIANE SCHMIDMEIER","r":"ESTADO SC","l":"Mafra","s":"Ambiental","d":"2023-02-28"},
{"n":"0900172-96.2018.8.24.0015","c":"EXECUÇÃO FISCAL","a":"ESTADO SC","r":"ADIR PEREIRA DA ROCHA","l":"Exec Fiscal","s":"Dívida Ativa","d":"2018-10-04"},
{"n":"5003114-65.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"MARCELO NIEZELSKI","l":"Canoinhas","s":"Destruição","d":"2023-04-14"},
{"n":"5001271-95.2025.8.24.0047","c":"CRIMES AMBIENTAIS","a":"MPU","r":"CARLOS AUGUSTO PAPES","l":"Papanduva","s":"Meio Ambiente","d":"2025-07-07"},
{"n":"0900097-57.2018.8.24.0015","c":"EXECUÇÃO FISCAL","a":"ESTADO SC","r":"WALDIR JANTSCH","l":"Exec Fiscal","s":"Dívida Ativa","d":"2018-08-02"},
{"n":"5007275-84.2024.8.24.0015","c":"Produção Antecipada Prova","a":"EDSON LUIS RAABE","r":"IMA","l":"Canoinhas","s":"Dano Ambiental","d":"2024-10-11"},
{"n":"5006402-69.2025.8.24.0041","c":"CUMPRIMENTO DE SENTENÇA","a":"ESTADO SC","r":"LUCIANE SCHMIDMEIER","l":"Mafra","s":"Multas","d":"2025-11-19"},
{"n":"5002945-20.2019.8.24.0015","c":"EXECUÇÃO FISCAL","a":"ESTADO SC","r":"JOAO VARLEI NEVES","l":"Exec Fiscal","s":"Multas","d":"2019-11-05"},
{"n":"5006746-31.2025.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"LENON TAQUES","r":"JOSE LUIZ LACOWICZ","l":"Canoinhas","s":"Dano moral","d":"2025-09-19"},
{"n":"5004560-69.2024.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"PEDRO VATRAZ","l":"Canoinhas","s":"Flora","d":"2024-07-03"},
{"n":"5006935-94.2025.8.24.0019","c":"Representação Criminal","a":"MPSC","r":"MÁRCIO FABIANO HELBING","l":"Concórdia","s":"Destruição","d":"2025-07-18"},
{"n":"5003797-20.2025.8.24.0052","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"RICARDO JOSE TEIXEIRA","l":"Porto União","s":"Meio Ambiente","d":"2025-10-01"},
{"n":"5004968-26.2025.8.24.0015","c":"Ação Penal","a":"MPSC","r":"MARCOS HIROAKI NAGANO","l":"Canoinhas","s":"Ordenamento Urbano","d":"2025-07-15"},
{"n":"5003919-66.2025.8.24.0041","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"WALDIR JANTSCH","l":"Mafra","s":"Flora","d":"2025-07-18"},
{"n":"5020293-54.2024.8.24.0022","c":"Execução Pena Multa","a":"MPSC","r":"LUIS BENEDITO PACHECO","l":"Curitibanos","s":"Multa","d":"2024-09-11"},
{"n":"5009586-53.2021.8.24.0015","c":"Ação Penal","a":"MPSC","r":"LUIS BENEDITO PACHECO","l":"Canoinhas","s":"Poluição","d":"2021-12-17"},
{"n":"5001854-80.2024.8.24.0026","c":"Calúnia/Difamação","a":"GERMANO WOEHL JUNIOR","r":"JOSE ADILSON KOBICHEN","l":"Guaramirim","s":"Calúnia","d":"2024-04-05"},
{"n":"5004348-53.2021.8.24.0015","c":"Ação Penal","a":"MPSC","r":"ELIEZER JANTSCH","l":"Canoinhas","s":"Flora","d":"2021-06-18"},
{"n":"5003215-29.2020.8.24.0041","c":"ACP Cível","a":"MPSC","r":"DANIELLY VENEZIO RODRIGUES","l":"Mafra","s":"Flora","d":"2020-08-13"},
{"n":"5004465-44.2021.8.24.0015","c":"EXECUÇÃO FISCAL","a":"ESTADO SC","r":"ADAO LUCACHINSKI NETO","l":"Exec Fiscal","s":"Dívida Ativa","d":"2021-06-22"},
{"n":"5006682-89.2023.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"ANTONIO ROBERTO DE OLIVEIRA","l":"Canoinhas","s":"Dano ambiental","d":"2023-08-14"},
{"n":"5000136-23.2020.8.24.0015","c":"EXECUÇÃO FISCAL","a":"ESTADO SC","r":"ADIR PEREIRA DA ROCHA","l":"Exec Fiscal","s":"Dívida Ativa","d":"2020-01-10"},
{"n":"5003918-29.2025.8.24.0026","c":"JUIZADO ESPECIAL","a":"ADRIANO BLASZKOSKI","r":"GERMANO WOEHL JUNIOR","l":"Guaramirim","s":"Dano Moral","d":"2025-07-03"},
{"n":"5008779-96.2022.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"PEDRO COLACO","l":"Canoinhas","s":"Destruição","d":"2022-12-06"},
{"n":"5003148-55.2025.8.24.0052","c":"CUMPRIMENTO DE SENTENÇA","a":"IMA","r":"BIG SAFRA S/A","l":"Porto União","s":"Multa ambiental","d":"2025-08-18"},
{"n":"5003526-25.2025.8.24.0015","c":"MANDADO DE SEGURANÇA","a":"CAPITAL MATE","r":"IMA Canoinhas","l":"Canoinhas","s":"Multa ambiental","d":"2025-05-20"},
{"n":"5003390-65.2025.8.24.0520","c":"BUSCA E APREENSÃO","a":"PCSC","r":"FABIANA NUNES DA ROSA","l":"Regional Criciúma","s":"Maus Tratos","d":"2025-06-12"},
{"n":"5006117-28.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"CARLOS AUGUSTO PAPES","l":"Canoinhas","s":"Destruição","d":"2023-07-21"},
{"n":"5002496-52.2025.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"SILMAR VOREL","l":"Canoinhas","s":"Flora","d":"2025-04-08"},
{"n":"5002499-07.2025.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"ELIEZER JANTSCH","l":"Canoinhas","s":"Flora","d":"2025-04-08"},
{"n":"5001006-05.2019.8.24.0015","c":"Procedimento Comum Cível","a":"LENON TAQUES","r":"JOSE LUIZ LACOWICZ","l":"Canoinhas","s":"Dano moral","d":"2019-08-13"},
{"n":"5000194-32.2022.8.24.0055","c":"INQUÉRITO POLICIAL","a":"PCSC","r":"JHONNY SCHMIDMEIER","l":"Rio Negrinho","s":"Meio Ambiente","d":"2022-01-27"},
{"n":"0300014-62.2017.8.24.0068","c":"Procedimento Comum Cível","a":"AFRIB BIONDO","r":"ROBERT ALVES ELIAS","l":"Canoinhas","s":"Cheque","d":"2017-01-12"},
{"n":"5002168-94.2023.8.24.0047","c":"Ação Penal","a":"MPSC","r":"ADILSO FOLMER","l":"Papanduva","s":"Destruição","d":"2023-09-14"},
{"n":"5007625-09.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"VILA MULTISHOW LTDA","l":"Canoinhas","s":"Ordenamento Urbano","d":"2023-09-20"},
{"n":"5002297-64.2024.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"EDSON LUIS RAABE","l":"Canoinhas","s":"Destruição","d":"2024-04-10"},
{"n":"5005357-79.2023.8.24.0015","c":"Procedimento Comum Cível","a":"VINICIUS CORNELSEN","r":"MILI S/A","l":"Canoinhas","s":"Dano material","d":"2023-06-26"},
{"n":"5003105-26.2022.8.24.0052","c":"TERMO CIRCUNSTANCIADO","a":"PMSC","r":"RICARDO JOSE TEIXEIRA","l":"Porto União","s":"Ordenamento Urbano","d":"2022-07-13"},
{"n":"5002716-40.2023.8.24.0041","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"CARLOS SCHMIDMEIER","l":"Mafra","s":"Destruição","d":"2023-05-12"},
{"n":"5003387-15.2021.8.24.0015","c":"Ação Penal","a":"MPSC","r":"ANTONIO ROBERTO DE OLIVEIRA","l":"Canoinhas","s":"Flora","d":"2021-05-14"},
{"n":"5006894-13.2023.8.24.0015","c":"ACP Cível","a":"MPSC","r":"FERNANDO FARIAN","l":"Canoinhas","s":"Ambiental","d":"2023-08-22"},
{"n":"5001825-97.2023.8.24.0015","c":"Execução ANPP","a":"MPSC","r":"SAULO SUCHARA","l":"Canoinhas","s":"ANPP","d":"2023-03-03"},
{"n":"5007768-95.2023.8.24.0015","c":"Execução ANPP","a":"MPSC","r":"MATHEUS MELECHENCO","l":"Canoinhas","s":"ANPP","d":"2023-09-26"},
{"n":"5002086-33.2021.8.24.0015","c":"Ação Penal","a":"MPSC","r":"ALBERTO SCHOSTAK","l":"Canoinhas","s":"Flora","d":"2021-03-24"},
{"n":"5008400-24.2023.8.24.0015","c":"Produção Antecipada Prova","a":"VILA MULTISHOW","r":"IMA","l":"Canoinhas","s":"Dano ambiental","d":"2023-10-19"},
{"n":"5001971-90.2024.8.24.0052","c":"Procedimento Comum Cível","a":"BIG SAFRA S/A","r":"IMA","l":"Porto União","s":"Multa ambiental","d":"2024-05-20"},
{"n":"5002505-02.2021.8.24.0032","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"ADRIANO BLASZKOSKI","l":"Itaiópolis","s":"Flora","d":"2021-12-17"},
{"n":"5000025-80.2023.8.24.0032","c":"Ação Penal","a":"MPSC","r":"CARLOS SCHMIDMEIER","l":"Itaiópolis","s":"Destruição","d":"2023-01-11"},
{"n":"5003980-24.2025.8.24.0041","c":"Execução ANPP","a":"MPSC","r":"AUGUSTO SCHIMITBERGER","l":"Canoinhas","s":"ANPP","d":"2025-07-22"},
{"n":"5006783-92.2024.8.24.0015","c":"Execução ANPP","a":"MPSC","r":"MARCOS TODT","l":"Canoinhas","s":"ANPP","d":"2024-09-23"},
{"n":"5005751-86.2023.8.24.0015","c":"INQUÉRITO POLICIAL","a":"PCSC","r":"RENATO JARDEL GURTINSKI","l":"Canoinhas","s":"Meio Ambiente","d":"2023-07-07"},
{"n":"5001144-59.2025.8.24.0015","c":"RECURSO","a":"MPSC","r":"AUGUSTO SCHIMITBERGER","l":"Canoinhas","s":"Destruição","d":"2025-01-24"},
{"n":"5003861-78.2024.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"GENEZIO KUBIACK","l":"Canoinhas","s":"Destruição","d":"2024-06-11"},
{"n":"5007482-83.2024.8.24.0015","c":"Calúnia/Difamação","a":"RAFAEL BONFIM","r":"JESSE DE FARIA LOPES","l":"Canoinhas","s":"Difamação","d":"2024-10-19"},
{"n":"5005436-87.2025.8.24.0015","c":"INQUÉRITO POLICIAL","a":"PF/SC","r":"A APURAR","l":"Canoinhas","s":"Falsidade ideológica","d":"2025-08-01"},
{"n":"5002931-60.2024.8.24.0015","c":"TERMO CIRCUNSTANCIADO","a":"PCSC","r":"JOSIEL MAIA MOREIRA","l":"Canoinhas","s":"Violação domicílio","d":"2024-05-03"},
{"n":"5000503-71.2025.8.24.0015","c":"PIC-MP","a":"MPSC","r":"AUGUSTO SCHIMITBERGER","l":"Regional Mafra","s":"Destruição","d":"2025-01-24"},
{"n":"5002004-43.2024.8.24.0032","c":"JUIZADO ESPECIAL","a":"JOSE ADILSON KOBICHEN","r":"GERMANO WOEHL JUNIOR","l":"Itaiópolis","s":"Dano moral","d":"2024-10-24"},
{"n":"5001145-44.2025.8.24.0015","c":"RECURSO","a":"MPSC","r":"ANDRE DA SILVEIRA","l":"Canoinhas","s":"Destruição","d":"2025-01-24"},
{"n":"5002920-94.2025.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"LUIS BENEDITO PACHECO","l":"Canoinhas","s":"Flora","d":"2025-04-25"},
{"n":"5002158-15.2024.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"MARCOS HIROAKI NAGANO","l":"Canoinhas","s":"Ordenamento Urbano","d":"2024-04-05"},
{"n":"5003083-56.2022.8.24.0055","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"ELCIO ANTONIO PSCHEIDT","l":"Rio Negrinho","s":"Meio Ambiente","d":"2022-09-22"},
{"n":"5008988-65.2022.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"MARIA PAULA FRIEDRICH","l":"Canoinhas","s":"Destruição","d":"2022-12-14"},
{"n":"5001364-05.2023.8.24.0055","c":"Ação Penal","a":"MPSC","r":"SIEGRID SCHLUP","l":"Rio Negrinho","s":"Destruição","d":"2023-05-11"},
{"n":"5000200-91.2024.8.24.0015","c":"Produção Antecipada Prova","a":"MATHEUS MELECHENCO","r":"ESTADO SC","l":"Canoinhas","s":"Dano ambiental","d":"2024-01-17"},
{"n":"5004642-42.2020.8.24.0015","c":"ACP Cível","a":"MPSC","r":"WALDIR JANTSCH","l":"Canoinhas","s":"Flora","d":"2020-07-28"},
{"n":"5007339-94.2024.8.24.0015","c":"Embargos à Execução","a":"ADEMAR STAWAS","r":"MPSC","l":"Canoinhas","s":"APP","d":"2024-10-15"},
{"n":"5007373-06.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"MATHEUS MELECHENCO","l":"Regional Mafra","s":"Destruição","d":"2023-09-08"},
{"n":"5009151-45.2022.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"SAULO SUCHARA","l":"Regional Mafra","s":"Destruição","d":"2022-12-16"},
{"n":"5001435-30.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"FLAVIO CAVALHEIRO","l":"Canoinhas","s":"Destruição","d":"2023-02-17"},
{"n":"5000896-64.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"MARCOS TODT","l":"Canoinhas","s":"Destruição","d":"2023-02-02"},
{"n":"5003038-94.2022.8.24.0041","c":"EXECUÇÃO TÍTULO EXTRAJUDICIAL","a":"MPSC","r":"BIG SAFRA S/A","l":"Mafra","s":"Poluição","d":"2022-06-14"},
{"n":"5006545-10.2023.8.24.0015","c":"TERMO CIRCUNSTANCIADO","a":"PMSC","r":"DITER HERMANN MULLER","l":"Canoinhas","s":"Destruição","d":"2023-08-09"},
{"n":"5005494-32.2021.8.24.0015","c":"ACP Cível","a":"MPSC","r":"JOAO VARLEI NEVES","l":"Canoinhas","s":"Flora","d":"2021-07-22"},
{"n":"5004677-16.2023.8.24.0041","c":"TERMO CIRCUNSTANCIADO","a":"PMSC","r":"RODRIGO BALBINOTTI","l":"Mafra","s":"Destruição","d":"2023-08-09"},
{"n":"5004680-68.2023.8.24.0041","c":"TERMO CIRCUNSTANCIADO","a":"PMSC","r":"EDSON SCHECK","l":"Mafra","s":"Destruição","d":"2023-08-09"},
{"n":"5008276-41.2023.8.24.0015","c":"JUIZADO ESPECIAL","a":"WILLIAN CILAS SILVA","r":"AUTO PRATENSE LTDA","l":"Canoinhas","s":"Dano moral","d":"2023-10-16"},
{"n":"5002005-28.2024.8.24.0032","c":"JUIZADO ESPECIAL","a":"ADRIANO BLASZKOSKI","r":"GERMANO WOEHL JUNIOR","l":"Itaiópolis","s":"Dano moral","d":"2024-10-24"},
{"n":"5002714-24.2020.8.24.0058","c":"Representação Criminal","a":"MPSC","r":"RENAN CARVALHO OLIVEIRA","l":"São Bento Sul","s":"Flora","d":"2020-04-29"},
{"n":"5008881-55.2021.8.24.0015","c":"ACP Cível","a":"MPSC","r":"JOAO ARILDO BALAO","l":"Canoinhas","s":"Dano ambiental","d":"2021-11-25"},
{"n":"5000834-89.2023.8.24.0058","c":"Execução ANPP","a":"MPSC","r":"CRCO INCORPORADORA","l":"São Bento Sul","s":"ANPP","d":"2023-02-03"},
{"n":"5004658-89.2022.8.24.0026","c":"INQUÉRITO POLICIAL","a":"PCSC","r":"ADRIANO BLASZKOSKI","l":"Guaramirim","s":"Armas","d":"2022-08-26"},
{"n":"5005704-34.2023.8.24.0041","c":"MANDADO DE SEGURANÇA","a":"BIG SAFRA S/A","r":"IMA Mafra","l":"Mafra","s":"Licença Ambiental","d":"2023-09-29"},
{"n":"5002338-31.2024.8.24.0015","c":"TERMO CIRCUNSTANCIADO","a":"PCSC","r":"ANDREA GEOVANA HOFFMANN","l":"Canoinhas","s":"Dano","d":"2024-04-11"},
{"n":"5002495-04.2024.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"GENEZIO KUBIACK","l":"Canoinhas","s":"Destruição","d":"2024-04-16"},
{"n":"5005422-74.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"CLEBER FRIDRICH","l":"Canoinhas","s":"Estabelecimentos Poluidores","d":"2023-06-27"},
{"n":"5002623-24.2024.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"GENEZIO KUBIACK","l":"Canoinhas","s":"Destruição","d":"2024-04-22"},
{"n":"5008582-10.2023.8.24.0015","c":"CUMPRIMENTO DE SENTENÇA","a":"MPSC","r":"MARIA TRINDADE NEVES","l":"Canoinhas","s":"Dano ambiental","d":"2023-10-24"},
{"n":"5002670-32.2023.8.24.0015","c":"ACP Cível","a":"MPSC","r":"NILSO BECKER","l":"Canoinhas","s":"Dano ambiental","d":"2023-03-29"},
{"n":"0900003-75.2019.8.24.0015","c":"ACP Cível","a":"MPSC","r":"ADIR PEREIRA DA ROCHA","l":"Canoinhas","s":"Flora","d":"2019-01-17"},
{"n":"5005434-88.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"CARLOS AUGUSTO PAPES","l":"Canoinhas","s":"Destruição","d":"2023-06-27"},
{"n":"5007864-47.2022.8.24.0015","c":"MANDADO DE SEGURANÇA","a":"PLANEJA EMPREEND","r":"IMA Canoinhas","l":"Canoinhas","s":"Licença Ambiental","d":"2022-10-29"},
{"n":"5000169-08.2023.8.24.0015","c":"CRIMES AMBIENTAIS","a":"MPSC","r":"FLAVIO CAVALHEIRO","l":"Canoinhas","s":"Destruição","d":"2023-01-12"},
]

def _norm(s):
    s = str(s or '').lower().strip()
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))

def _parse_date(d):
    if not d: return ''
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', str(d))
    return f'{m.group(3)}/{m.group(2)}/{m.group(1)}' if m else str(d)

def _uid_lenon():
    try:
        for user in get_auth().list_users().users:
            if 'lenon' in (user.display_name or '').lower():
                return user.uid
    except: pass
    return ''

@ui.page('/visao-geral/migracao-processos')
def migracao_page():
    if not is_authenticated():
        ui.navigate.to('/login'); return
    definir_workspace('visao_geral')
    ensure_firebase_initialized()

    with layout('Migração de Processos'):
        ui.label('Migração de Processos — Planilha Lenon 2025').classes('text-2xl font-bold mb-4')
        ui.label(f'{len(PROCESSOS)} processos prontos. Selecione e migre.').classes('text-gray-600 mb-4')

        sobrescrever = ui.checkbox('Sobrescrever campos existentes', value=False)

        rows = [{'_key': p['n'], 'numero': p['n'], 'classe': p['c'][:40], 'reu': p['r'][:30], 'localidade': p['l'][:20], 'data': _parse_date(p['d']), '_raw': p} for p in PROCESSOS]

        tabela = ui.table(
            columns=[
                {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left', 'sortable': True},
                {'name': 'classe', 'label': 'Classe', 'field': 'classe', 'align': 'left'},
                {'name': 'reu', 'label': 'Réu', 'field': 'reu', 'align': 'left'},
                {'name': 'localidade', 'label': 'Localidade', 'field': 'localidade', 'align': 'left'},
                {'name': 'data', 'label': 'Data', 'field': 'data', 'align': 'left'},
            ],
            rows=rows, row_key='_key', selection='multiple', pagination={'rowsPerPage': 25},
        ).classes('w-full')

        async def _migrar():
            sel = tabela.selected_rows or []
            if not sel: ui.notify('Selecione ao menos 1.', type='warning'); return
            uid = _uid_lenon()
            criados = atualizados = erros = 0
            for row in sel:
                try:
                    p = row['_raw']
                    ex = await buscar_processo_por_numero(p['n'])
                    if ex:
                        campos = {}
                        if sobrescrever.value or not ex.get('titulo'): campos['titulo'] = f"{p['c']} - {p['s']}"
                        if sobrescrever.value or not ex.get('responsavel'): campos['responsavel'] = uid
                        if sobrescrever.value or not ex.get('nucleo'): campos['nucleo'] = 'Ambiental'
                        if sobrescrever.value or not ex.get('sistema_processual'): campos['sistema_processual'] = 'Eproc TJ Santa Catarina 1ª Instância'
                        if campos: await atualizar_campos_processo(ex['_id'], campos); atualizados += 1
                    else:
                        await criar_processo({'numero': p['n'], 'titulo': f"{p['c']} - {p['s']}", 'data_abertura': _parse_date(p['d']), 'responsavel': uid, 'sistema_processual': 'Eproc TJ Santa Catarina 1ª Instância', 'nucleo': 'Ambiental', 'estado': 'Santa Catarina', 'status': 'Em andamento', 'parte_contraria': p['r'], 'observacoes': f"Localidade: {p['l']}"})
                        criados += 1
                except Exception as e: print(f"Erro {p['n']}: {e}"); erros += 1
            ui.notify(f'✅ {criados} criados, {atualizados} atualizados' + (f', {erros} erros' if erros else ''), type='positive' if not erros else 'warning')

        with ui.row().classes('gap-2 mt-4'):
            ui.button('Migrar selecionados', icon='upload', on_click=_migrar).props('color=primary')
            ui.button('Selecionar todos', on_click=lambda: tabela.update(selected=rows)).props('flat')
            ui.button('Limpar seleção', on_click=lambda: tabela.update(selected=[])).props('flat')
            ui.button('Voltar', icon='arrow_back', on_click=lambda: ui.navigate.to('/visao-geral/processos')).props('flat')
