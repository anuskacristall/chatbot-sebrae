import pypdf
import os

def extrair_texto_pdf(caminho_do_pdf):
    
    texto_completo = ""
    nome_arquivo = os.path.basename(caminho_do_pdf)
    
    try:
        # Abre o arquivo PDF
        with open(caminho_do_pdf, "rb") as arquivo:
            leitor = pypdf.PdfReader(arquivo)
            # Percorre cada página do PDF
            for pagina in leitor.pages:
                # Extrai o texto da página e adiciona ao texto total
                texto_pagina = pagina.extract_text() or ""
                texto_completo += texto_pagina + "\n"

        if not texto_completo.strip():
            print(f"Atenção: o PDF {nome_arquivo} não contém texto legível.")
            return None

        return {"texto": texto_completo, "fonte": nome_arquivo}
    except Exception as e:
        print(f"Erro ao ler o PDF {caminho_do_pdf}: {e}")
        return None

# Teste rápido pra ver se ele consegue ler os arquivos na pasta
if __name__ == "__main__":
    pasta_pdfs = "backend/data/pdfs"
    # Lista todos os arquivos que terminam com .pdf na pasta
    arquivos = [f for f in os.listdir(pasta_pdfs) if f.endswith('.pdf')]
    
    if not arquivos:
        print("Atenção: Nenhum arquivo PDF encontrado em backend/data/pdfs/")
    else:
        for arquivo in arquivos:
            caminho = os.path.join(pasta_pdfs, arquivo)
            resultado = extrair_texto_pdf(caminho)
            if resultado:
                print(f"✅ Sucesso! Lidos {len(resultado)} caracteres do arquivo: {arquivo}")