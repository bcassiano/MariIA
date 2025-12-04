import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import sys
import argparse
import csv
import json
import time
from typing import List, Dict

# --- CONFIGURAÇÕES DE INFRAESTRUTURA ---
PROJECT_ID = "amazing-firefly-475113-p3"
LOCATION = "us-central1"
GLOBAL_ENDPOINT = "aiplatform.googleapis.com"
MODEL_ID = "gemini-3-pro-preview"

# Inicialização
vertexai.init(project=PROJECT_ID, location=LOCATION, api_endpoint=GLOBAL_ENDPOINT)

class InventoryAgent:
    def __init__(self):
        self.system_instruction = """
        Você é um Analista Sênior de Inventário e Logística. 
        Sua missão é analisar SKUs técnicos, identificar especificações críticas e categorizar produtos.
        Seja direto, técnico e use terminologia padrão da indústria.
        Se a informação for ambígua, declare a ambiguidade.
        """
        try:
            self.model = GenerativeModel(
                model_name=MODEL_ID,
                system_instruction=self.system_instruction
            )
        except Exception as e:
            print(f"ERRO DE INICIALIZAÇÃO: {e}")
            sys.exit(1)

    def analyze_sku(self, sku_code: str, context_data: str = "") -> str:
        """Processa um único SKU e retorna texto puro."""
        prompt = f"""
        TAREFA: Analise o SKU: {sku_code}
        CONTEXTO: {context_data}
        
        SAÍDA (Responda estritamente neste formato JSON sem markdown):
        {{
            "categoria": "...",
            "especificacoes": ["...", "..."],
            "riscos": ["..."],
            "ambiguidade_detectada": true/false
        }}
        """
        
        generation_config = {
            "max_output_tokens": 8192,
            "temperature": 0.2,
            "top_p": 0.95,
            "response_mime_type": "application/json" # Força saída JSON estruturada
        }

        safety_settings = [
            SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
        ]

        try:
            response = self.model.generate_content(
                prompt, 
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            return response.text
        except Exception as e:
            return json.dumps({"erro": str(e)})

    def process_batch(self, input_file: str, output_file: str):
        """Lê CSV, processa SKUs e salva JSONL."""
        print(f"--- Iniciando Processamento em Lote: {input_file} ---")
        
        results = []
        try:
            with open(input_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Validação básica de colunas
                if 'sku' not in reader.fieldnames:
                    print("ERRO: O arquivo CSV deve ter uma coluna chamada 'sku'.")
                    return

                rows = list(reader)
                total = len(rows)
                
                print(f">>> {total} itens encontrados na fila.")

                for i, row in enumerate(rows):
                    sku = row['sku']
                    context = row.get('contexto', '') # Coluna opcional
                    
                    print(f"[{i+1}/{total}] Processando: {sku}...")
                    
                    analysis_json = self.analyze_sku(sku, context)
                    
                    try:
                        parsed_data = json.loads(analysis_json)
                    except:
                        parsed_data = {"raw_text": analysis_json, "error": "Falha no parse JSON"}

                    result_record = {
                        "sku": sku,
                        "input_context": context,
                        "analysis": parsed_data
                    }
                    results.append(result_record)
                    
                    # Rate limiting preventivo para não estourar a cota da API Preview
                    time.sleep(1) 

            # Salvar resultado
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n>>> SUCESSO! Resultados salvos em: {output_file}")

        except FileNotFoundError:
            print(f"ERRO: Arquivo {input_file} não encontrado.")

# --- CLI ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente de Inventário Gemini 3.0")
    
    # Grupo mutuamente exclusivo: ou processa um SKU ou um Arquivo
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sku", type=str, help="SKU único")
    group.add_argument("--file", type=str, help="Arquivo CSV de entrada (colunas: sku, contexto)")
    
    parser.add_argument("--context", type=str, default="", help="Contexto (apenas para modo SKU único)")
    parser.add_argument("--out", type=str, default="resultado_analise.json", help="Arquivo de saída (apenas para modo arquivo)")
    
    args = parser.parse_args()
    
    agent = InventoryAgent()
    
    if args.sku:
        # Modo Debug (Single Shot)
        print(f"\n>>> MODO SINGLE: {args.sku}")
        print(agent.analyze_sku(args.sku, args.context))
    elif args.file:
        # Modo Produção (Batch)
        agent.process_batch(args.file, args.out)