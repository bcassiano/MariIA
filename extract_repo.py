import os
import subprocess

# --- CONFIGURAÇÃO BRUTAL ---
# Arquivos e pastas que serão ignorados impiedosamente.
# Adicione aqui qualquer coisa que não ajude a IA a entender a LÓGICA do negócio.
IGNORE_PATTERNS = [
    '.git', '.idea', '.vscode', '__pycache__', 'node_modules', 
    'venv', 'env', 'dist', 'build', 'coverage', 
    '.DS_Store', '*.lock', '*.log', '*.png', '*.jpg', '*.jpeg', 
    '*.gif', '*.ico', '*.svg', '*.eot', '*.ttf', '*.woff', '*.woff2', 
    '*.mp4', '*.mp3', '*.pdf', '*.zip', '*.tar', '*.gz', '*.rar', 
    '*.exe', '*.dll', '*.so', '*.dylib', '*.class', '*.jar', 
    'package-lock.json', 'yarn.lock'
]

OUTPUT_FILE = "FULL_PROJECT_CONTEXT.txt"

def should_ignore(path, is_dir=False):
    """Verifica se o caminho deve ser ignorado."""
    name = os.path.basename(path)
    
    # Ignora diretórios/arquivos ocultos (começam com .) exceto .gitignore (opcional)
    if name.startswith('.') and name != '.gitignore':
        return True
        
    for pattern in IGNORE_PATTERNS:
        # Correspondência simples de padrão
        if pattern == name:
            return True
        if pattern.startswith('*') and name.endswith(pattern[1:]):
            return True
            
    return False

def get_git_history():
    """Extrai o histórico do git com estatísticas de mudança."""
    print(">>> Extraindo histórico do Git...")
    try:
        # Pega os últimos 50 commits com estatísticas e nomes de arquivos alterados
        # Formato: Hash - Autor - Data - Mensagem + Stats
        result = subprocess.run(
            ['git', 'log', '-n', '50', '--stat', '--pretty=format:Commit: %h%nAuthor: %an%nDate: %ad%nMessage: %s%n'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace' # Não quebra se tiver caracteres estranhos
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Erro ao ler git log: {result.stderr}"
    except Exception as e:
        return f"Git não encontrado ou erro na execução: {str(e)}"

def is_binary(file_path):
    """Detecta arquivos binários lendo o início do arquivo."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except:
        return True

def process_repository():
    root_dir = os.getcwd()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # Cabeçalho XML para o Prompt
        outfile.write("<repository_context>\n")
        
        # 1. Inserir Histórico do Git
        outfile.write("  <git_history>\n")
        outfile.write(get_git_history())
        outfile.write("\n  </git_history>\n\n")
        
        # 2. Inserir Arquivos de Código
        outfile.write("  <source_code>\n")
        
        print(">>> Varrendo arquivos...")
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Modifica dirnames in-place para impedir a descida em pastas ignoradas
            dirnames[:] = [d for d in dirnames if not should_ignore(os.path.join(dirpath, d), is_dir=True)]
            
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                
                # Pula arquivo de saída e o próprio script
                if filename == OUTPUT_FILE or filename == os.path.basename(__file__):
                    continue
                    
                if should_ignore(file_path):
                    continue
                
                if is_binary(file_path):
                    print(f"Ignorando binário: {filename}")
                    continue

                # Caminho relativo para facilitar a leitura da IA
                rel_path = os.path.relpath(file_path, root_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Estrutura XML clara para cada arquivo
                        outfile.write(f'    <file path="{rel_path}">\n')
                        outfile.write(f'<![CDATA[\n{content}\n]]>\n')
                        outfile.write('    </file>\n')
                        print(f"Processado: {rel_path}")
                        
                except Exception as e:
                    print(f"Erro ao ler {rel_path}: {e}")

        outfile.write("  </source_code>\n")
        outfile.write("</repository_context>\n")

    print(f"\n>>> CONCLUÍDO. Arquivo gerado: {OUTPUT_FILE}")
    print(">>> Agora, faça upload deste arquivo no seu prompt junto com os PDFs.")

if __name__ == "__main__":
    process_repository()