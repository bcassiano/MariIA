# Configuração do App Mobile (MariIA)

A estrutura de código fonte já foi criada na pasta `mobile/`. Agora você precisa inicializar o projeto Expo e instalar as dependências.

## 1. Inicializar o Projeto Expo
Abra um terminal na pasta `mobile/` e execute:

```bash
cd mobile
npx create-expo-app . --template blank
```
*(Se perguntar se quer sobrescrever arquivos, diga **NÃO** ou faça backup do `App.js` antes. O ideal é instalar as dependências abaixo se o projeto já existir)*.

**Alternativa Segura (Recomendada):**
Como eu já criei os arquivos de código (`App.js`, `src/`), apenas instale as dependências necessárias para eles funcionarem:

1. Crie o `package.json` (se não existir):
   ```bash
   npm init -y
   ```

2. Instale o Expo e bibliotecas:
   ```bash
   npx install-expo-modules@latest
   npm install react-native-web react-dom @expo/metro-runtime
   npm install @react-navigation/native @react-navigation/stack
   npm install react-native-screens react-native-safe-area-context
   npm install axios
   ```

## 2. Rodar o App
```bash
npx expo start
```
- Pressione `a` para abrir no Android (Emulador ou USB).
- Pressione `w` para abrir no Web Browser.
- Escaneie o QR Code com o app Expo Go no seu celular.

## 3. Configuração de IP
No arquivo `src/services/api.js`, verifique o `API_URL`:
- Se usar Emulador Android: `http://10.0.2.2:8000`
- Se usar Celular Físico: Troque pelo IP da sua máquina (ex: `http://192.168.1.X:8000`)
