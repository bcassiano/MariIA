# Erro de Build no Cloud Run: Permission Denied no Artifact Registry

**Data:** 2026-01-09  
**Projeto:** MariIA Backend  
**Ambiente:** Google Cloud Platform

---

## 📋 Resumo do Problema

Ao tentar fazer deploy do backend para o Cloud Run usando `gcloud builds submit`, o build completava com sucesso, mas o **push da imagem Docker para o Artifact Registry falhava** com o erro:

```
denied: Permission "artifactregistry.repositories.uploadArtifacts" denied on resource 
"projects/amazing-firefly-475113-p3/locations/us-central1/repositories/mariia-repo-2" 
(or it may not exist)
```

O sistema fazia 10 tentativas de push antes de falhar com `retry budget exhausted`.

---

## 🔍 Investigação Realizada

### Tentativas que NÃO Funcionaram

1. **Adicionar permissões para a conta do Cloud Build:**
   ```bash
   gcloud artifacts repositories add-iam-policy-binding mariia-repo-2 \
     --member=serviceAccount:635293407607@cloudbuild.gserviceaccount.com \
     --role=roles/artifactregistry.writer
   ```
   ❌ Não resolveu

2. **Adicionar permissões para o Cloud Build Service Agent:**
   ```bash
   gcloud artifacts repositories add-iam-policy-binding mariia-repo-2 \
     --member=serviceAccount:service-635293407607@gcp-sa-cloudbuild.iam.gserviceaccount.com \
     --role=roles/artifactregistry.repoAdmin
   ```
   ❌ Não resolveu

3. **Adicionar permissões no nível do Projeto:**
   ```bash
   gcloud projects add-iam-policy-binding amazing-firefly-475113-p3 \
     --member=serviceAccount:635293407607@cloudbuild.gserviceaccount.com \
     --role=roles/artifactregistry.admin
   ```
   ❌ Não resolveu

4. **Aguardar propagação IAM (30-60 segundos):**
   ❌ Não resolveu

5. **Tentar usar gcr.io (Container Registry legado):**
   ❌ Também falhou

---

## ✅ Causa Raiz Identificada

Ao analisar os detalhes do build com:
```bash
gcloud builds describe <BUILD_ID> --format="yaml(serviceAccount)"
```

Descobriu-se que o Cloud Build estava usando a conta de serviço **do Compute Engine**, não a conta do Cloud Build:

| O que eu achava | O que realmente acontecia |
|-----------------|---------------------------|
| `635293407607@cloudbuild.gserviceaccount.com` | `635293407607-compute@developer.gserviceaccount.com` |

### Por que isso acontece?

Quando você usa `gcloud builds submit` sem especificar uma conta de serviço com `--service-account`, o Cloud Build usa a **conta de serviço padrão do Compute Engine** do projeto.

---

## 🛠️ Solução

Aplicar as permissões `artifactregistry.repoAdmin` para a conta de serviço do **Compute Engine** nos repositórios:

```bash
# Para o repositório mariia-repo-2
gcloud artifacts repositories add-iam-policy-binding mariia-repo-2 \
  --location=us-central1 \
  --member=serviceAccount:635293407607-compute@developer.gserviceaccount.com \
  --role=roles/artifactregistry.repoAdmin \
  --project=amazing-firefly-475113-p3

# Para o repositório cloud-run-source-deploy (usado por gcloud run deploy --source)
gcloud artifacts repositories add-iam-policy-binding cloud-run-source-deploy \
  --location=us-central1 \
  --member=serviceAccount:635293407607-compute@developer.gserviceaccount.com \
  --role=roles/artifactregistry.repoAdmin \
  --project=amazing-firefly-475113-p3
```

---

## 📊 Resultado

Após aplicar as permissões corretas:

```
Build: SUCCESS ✅
Push: SUCCESS ✅
Deploy: mariia-backend-00023-b5s ✅
```

---

## 🧠 Lições Aprendidas

1. **Sempre verificar qual conta de serviço está sendo usada:**
   ```bash
   gcloud builds describe <BUILD_ID> --format="yaml(serviceAccount)"
   ```

2. **Existem TRÊS contas de serviço envolvidas no Cloud Build:**
   - `<PROJECT_NUMBER>@cloudbuild.gserviceaccount.com` - Conta do Cloud Build
   - `service-<PROJECT_NUMBER>@gcp-sa-cloudbuild.iam.gserviceaccount.com` - Cloud Build Service Agent
   - `<PROJECT_NUMBER>-compute@developer.gserviceaccount.com` - Compute Engine (PADRÃO!)

3. **O Cloud Build usa a conta do Compute Engine por padrão** quando não especificado.

4. **Para evitar esse problema no futuro**, pode-se especificar a conta de serviço no comando:
   ```bash
   gcloud builds submit --tag <IMAGE_TAG> \
     --service-account=projects/<PROJECT>/serviceAccounts/<SA_EMAIL>
   ```

---

## 📚 Referências

- [Cloud Build Service Accounts](https://cloud.google.com/build/docs/cloud-build-service-account)
- [Artifact Registry IAM](https://cloud.google.com/artifact-registry/docs/access-control)
- [Configuring Custom Service Accounts for Cloud Build](https://cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts)
