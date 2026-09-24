# Fluxo: cadastro e login como médico

## Como deve funcionar

1. **Tela de login** → escolha "Sou Doutor" → clique em "Cadastre-se como doutor".
2. **Preencha o cadastro** (nome, e-mail, CRM, especialidade, senha com 6+ caracteres) → Cadastrar.
3. **Você é redirecionado para a tela do médico** (dashboard).
4. **Da próxima vez**: na tela de login, entre com o mesmo e-mail e senha → deve abrir de novo a tela do médico (`/doctor`).

## O que precisa estar rodando

- **Backend**: no terminal, na pasta `MedChain`:
  ```bash
  uvicorn app.main:app --reload
  ```
  (ou `python -m uvicorn app.main:app --reload`)

- **Banco de dados**: PostgreSQL com o banco configurado no `.env` (ou variáveis de ambiente).

- **Frontend**: em outro terminal, na pasta `MedChain-front`:
  ```bash
  npm run dev
  ```
  Depois acesse o endereço que aparecer (ex.: http://localhost:5173).

## Se der "Failed to fetch"

O frontend em desenvolvimento usa o proxy do Vite para o backend. Confira se:

1. O backend está rodando na porta 8000.
2. Você acessa o front pelo endereço do Vite (ex.: http://localhost:5173), não abrindo o HTML direto.

## Se der "Usuário já existe"

Significa que esse e-mail já tem conta de login, mas ainda não tem perfil de médico. Duas opções:

- **Pelo próprio cadastro**: preencha de novo o formulário de "Cadastrar como Doutor" com o **mesmo e-mail e senha**. O sistema completa o perfil de médico e já faz o login.
- **Pelo navegador**: acesse `http://localhost:8000/api/v1/auth/complete-doctor` com método POST e body JSON:
  `{"email":"seu@email.com","full_name":"Seu Nome","CRM":"12345-SP","specialty":"Clínica Geral"}`  
  Depois faça login normalmente.

## Se ao logar abrir a tela de paciente em vez da do médico

O backend define o tipo pelo perfil (médico ou paciente). Se você é médico e ainda assim cai em paciente:

1. Chame no navegador: `http://localhost:8000/api/v1/auth/fix-doctor-roles`  
   Isso ajusta o `role` de quem já é médico no banco.
2. Faça logout e login de novo.
