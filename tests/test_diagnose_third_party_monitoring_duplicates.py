import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Adiciona o diretório raiz ao path para que o script de diagnóstico possa ser importado
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Importa o script que queremos testar
from scripts import diagnose_third_party_monitoring_duplicates

# --- Mock Data ---

def create_mock_doc(doc_id, data):
    """Cria um mock para um documento do Firestore."""
    mock = MagicMock()
    mock.id = doc_id
    mock.to_dict.return_value = data
    return mock

# Cenário 1: Dados limpos, sem duplicatas
clean_data = [
    create_mock_doc('doc1', {'processo_id': 'p1', 'caso_id': 'c1', 'data_criacao': '2025-01-01'}),
    create_mock_doc('doc2', {'processo_id': 'p1', 'caso_id': 'c2', 'data_criacao': '2025-01-02'}),
    create_mock_doc('doc3', {'processo_id': 'p2', 'caso_id': 'c1', 'data_criacao': '2025-01-03'}),
]

# Cenário 2: Dados com duplicatas
duplicate_data = [
    # Grupo de duplicatas 1 (p1, c1)
    create_mock_doc('dup1_1', {'processo_id': 'p1', 'caso_id': 'c1', 'data_criacao': '2025-01-10'}),
    create_mock_doc('dup1_2', {'processo_id': 'p1', 'caso_id': 'c1', 'data_criacao': '2025-01-11'}),
    
    # Registro único
    create_mock_doc('unique1', {'processo_id': 'p2', 'caso_id': 'c2', 'data_criacao': '2025-01-12'}),
    
    # Grupo de duplicatas 2 (p3, c3) - 3 registros
    create_mock_doc('dup2_1', {'processo_id': 'p3', 'caso_id': 'c3', 'data_criacao': '2025-01-13'}),
    create_mock_doc('dup2_2', {'processo_id': 'p3', 'caso_id': 'c3', 'data_criacao': '2025-01-14'}),
    create_mock_doc('dup2_3', {'processo_id': 'p3', 'caso_id': 'c3', 'data_criacao': '2025-01-15'}),
]


# --- Testes ---

@patch('scripts.diagnose_third_party_monitoring_duplicates.get_db')
def test_main_with_no_duplicates(mock_get_db, capsys):
    """
    Testa a execução do script com dados limpos.
    Espera-se que o relatório indique que nenhuma duplicata foi encontrada.
    """
    # Configuração do mock do Firestore
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.stream.return_value = clean_data
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

    # Executa a função main do script
    result_code = diagnose_third_party_monitoring_duplicates.main()
    captured = capsys.readouterr()

    # Asserções
    assert result_code == 0
    assert "Total de registros encontrados: 3" in captured.out
    assert "Nenhuma duplicata encontrada! O sistema está íntegro." in captured.out
    assert "Encontrados 0 grupos de duplicatas" not in captured.out
    mock_db.collection.assert_called_once_with('third_party_monitoring')


@patch('scripts.diagnose_third_party_monitoring_duplicates.get_db')
def test_main_with_duplicates(mock_get_db, capsys):
    """
    Testa a execução do script com dados que contêm duplicatas.
    Espera-se que o relatório identifique e detalhe os grupos de duplicatas.
    """
    # Configuração do mock do Firestore
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.stream.return_value = duplicate_data
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

    # Executa a função main do script
    result_code = diagnose_third_party_monitoring_duplicates.main()
    captured = capsys.readouterr()

    # Asserções
    assert result_code == 0
    assert "Total de registros encontrados: 6" in captured.out
    assert "Nenhuma duplicata encontrada!" not in captured.out
    
    # Verifica o resumo
    assert "Encontrados 2 grupos de duplicatas por (processo_id, caso_id):" in captured.out
    assert "Total de registros duplicados (neste critério): 5" in captured.out
    
    # Verifica detalhes do grupo 1
    assert "Grupo (Processo: p1, Caso: c1) - 2 registros" in captured.out
    assert "ID: dup1_1" in captured.out
    assert "ID: dup1_2" in captured.out
    
    # Verifica detalhes do grupo 2
    assert "Grupo (Processo: p3, Caso: c3) - 3 registros" in captured.out
    assert "ID: dup2_1" in captured.out
    assert "ID: dup2_2" in captured.out
    assert "ID: dup2_3" in captured.out
    
    # Verifica que não há IDs de documento duplicados
    assert "Nenhum ID de documento duplicado encontrado." in captured.out


@patch('scripts.diagnose_third_party_monitoring_duplicates.get_db')
def test_main_with_no_records(mock_get_db, capsys):
    """
    Testa a execução do script quando não há registros no banco.
    """
    # Configuração do mock do Firestore
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.stream.return_value = [] # Lista vazia
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

    # Executa a função main do script
    result_code = diagnose_third_party_monitoring_duplicates.main()
    captured = capsys.readouterr()

    # Asserções
    assert result_code == 0
    assert "Total de registros encontrados: 0" in captured.out
    assert "Nenhum acompanhamento encontrado." in captured.out

