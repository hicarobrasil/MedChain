"""
Popula o MedChain com dados de demonstração via API.

Uso (com o backend rodando em http://127.0.0.1:8000):

    cd MedChain
    .\\venv\\Scripts\\Activate.ps1
    python scripts/seed_demo_data.py

Credenciais geradas são impressas ao final.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import requests

BASE = "http://127.0.0.1:8000/api/v1"
PASSWORD = "senha123"


def req(method: str, path: str, token: str | None = None, **kwargs) -> Any:
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{BASE}{path}"
    res = requests.request(method, url, headers=headers, timeout=120, **kwargs)
    try:
        data = res.json()
    except Exception:
        data = {"raw": res.text}
    if res.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {res.status_code}: {data}")
    return data


def register_or_login_doctor(doctor: dict) -> dict:
    try:
        data = req("POST", "/auth/register-doctor", json={
            "full_name": doctor["full_name"],
            "email": doctor["email"],
            "password": PASSWORD,
            "CRM": doctor["CRM"],
            "specialty": doctor["specialty"],
        })
        print(f"  [ok] médico cadastrado: {doctor['email']}")
        return data
    except RuntimeError as err:
        msg = str(err).lower()
        if "existe" in msg or "409" in msg or "already" in msg or "crm" in msg:
            try:
                req("POST", "/auth/complete-doctor", json={
                    "email": doctor["email"],
                    "full_name": doctor["full_name"],
                    "CRM": doctor["CRM"],
                    "specialty": doctor["specialty"],
                })
            except Exception:
                pass
            data = req("POST", "/auth/login", json={
                "email": doctor["email"],
                "password": PASSWORD,
            })
            print(f"  [ok] médico já existia, login: {doctor['email']}")
            return data
        raise


def create_patient(token: str, patient: dict) -> dict:
    payload = {
        "name": patient["name"],
        "dateofbirth": patient["dateofbirth"],
        "gender": patient["gender"],
        "email": patient["email"],
        "phone": patient["phone"],
        "password": PASSWORD,
        "status": 1,
        "address_street": patient["street"],
        "address_number": patient["number"],
        "address_complement": patient.get("complement", ""),
        "address_neighborhood": patient["neighborhood"],
        "address_city": patient["city"],
        "address_state": patient["state"],
    }
    try:
        data = req("POST", "/patients/", token=token, json=payload)
        print(f"  [ok] paciente: {patient['name']}")
        return data
    except RuntimeError as err:
        if "409" in str(err) or "existe" in str(err).lower() or "ja" in str(err).lower():
            # tenta obter pelo login do paciente e mapear id
            login = req("POST", "/auth/login", json={
                "email": patient["email"],
                "password": PASSWORD,
            })
            pid = login.get("user", {}).get("patient_public_id") or login.get("user", {}).get("id")
            print(f"  [skip] paciente já existe: {patient['email']} ({pid})")
            return {"patient_public_id": pid, "uid": login.get("user", {}).get("id")}
        raise


def create_record(token: str, doctor_id: str, patient_id: str, record_type: str, data: dict) -> dict:
    body = {
        "type": record_type,
        "data": {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            **data,
        },
    }
    res = req("POST", "/medical-records/", token=token, json=body)
    anchored = res.get("anchored")
    flag = "ancorado" if anchored else "sem âncora"
    print(f"    · {record_type} ({flag})")
    return res


DOCTORS = [
    {
        "full_name": "Dra. Maria Silva",
        "email": "maria.silva@medchain.com",
        "CRM": "CRM-SP-10001",
        "specialty": "Clínica Geral",
    },
    {
        "full_name": "Dr. João Santos",
        "email": "joao.santos@medchain.com",
        "CRM": "CRM-SP-10002",
        "specialty": "Cardiologia",
    },
]

PATIENTS = [
    {
        "name": "Ana Oliveira",
        "email": "ana.oliveira@email.com",
        "phone": "11991001001",
        "dateofbirth": "1990-03-15",
        "gender": 1,
        "street": "Rua das Flores",
        "number": "120",
        "complement": "Apto 42",
        "neighborhood": "Jardins",
        "city": "São Paulo",
        "state": "SP",
        "doctor": "maria.silva@medchain.com",
        "records": [
            {
                "type": "consultation",
                "data": {
                    "chief_complaint": "Dor de cabeça recorrente há 2 semanas",
                    "history_of_present_illness": "Cefaleia tensional, piora ao final do expediente. Sem náuseas.",
                    "diagnosis": "Cefaleia tensional",
                    "treatment_plan": "Analgésico sob demanda, higiene do sono, retorno em 15 dias",
                    "prescription": {
                        "items": [
                            {
                                "medication_name": "Dipirona",
                                "dosage": "500mg",
                                "frequency": "8/8h se dor",
                                "treatment_duration": "7 dias",
                            }
                        ]
                    },
                },
            },
            {
                "type": "diagnostic",
                "data": {
                    "description": "Hemograma completo",
                    "issue_date": "2026-07-10",
                    "result": "Dentro dos limites da normalidade",
                },
            },
            {
                "type": "medical_certificate",
                "data": {
                    "purpose": "Afastamento para repouso por cefaleia intensa",
                    "period_of_leave": 2,
                },
            },
        ],
    },
    {
        "name": "Carlos Mendes",
        "email": "carlos.mendes@email.com",
        "phone": "11991001002",
        "dateofbirth": "1985-08-22",
        "gender": 0,
        "street": "Av. Paulista",
        "number": "1000",
        "complement": "Conj. 101",
        "neighborhood": "Bela Vista",
        "city": "São Paulo",
        "state": "SP",
        "doctor": "maria.silva@medchain.com",
        "records": [
            {
                "type": "consultation",
                "data": {
                    "chief_complaint": "Tosse produtiva e febre baixa",
                    "history_of_present_illness": "Sintomas há 5 dias após resfriado. Sem dispneia.",
                    "diagnosis": "Infecção de vias aéreas superiores",
                    "treatment_plan": "Hidratação, sintomáticos, observação",
                    "prescription": {
                        "items": [
                            {
                                "medication_name": "Amoxicilina",
                                "dosage": "500mg",
                                "frequency": "8/8h",
                                "treatment_duration": "7 dias",
                            },
                            {
                                "medication_name": "Xarope expectorante",
                                "dosage": "10ml",
                                "frequency": "8/8h",
                                "treatment_duration": "5 dias",
                            },
                        ]
                    },
                },
            },
            {
                "type": "diagnostic",
                "data": {
                    "description": "Radiografia de tórax",
                    "issue_date": "2026-07-18",
                    "result": "Sem alterações agudas",
                },
            },
        ],
    },
    {
        "name": "Beatriz Costa",
        "email": "beatriz.costa@email.com",
        "phone": "11991001003",
        "dateofbirth": "1998-11-05",
        "gender": 1,
        "street": "Rua Augusta",
        "number": "450",
        "complement": "",
        "neighborhood": "Consolação",
        "city": "São Paulo",
        "state": "SP",
        "doctor": "maria.silva@medchain.com",
        "records": [
            {
                "type": "consultation",
                "data": {
                    "chief_complaint": "Check-up anual",
                    "history_of_present_illness": "Assintomática. Histórico familiar de hipertensão.",
                    "diagnosis": "Exame clínico sem alterações",
                    "treatment_plan": "Manter hábitos saudáveis; solicitar perfil lipídico",
                },
            },
            {
                "type": "diagnostic",
                "data": {
                    "description": "Perfil lipídico",
                    "issue_date": "2026-07-20",
                    "result": "LDL levemente elevado — orientação dietética",
                },
            },
        ],
    },
    {
        "name": "Diego Ferreira",
        "email": "diego.ferreira@email.com",
        "phone": "11991001004",
        "dateofbirth": "1978-01-30",
        "gender": 0,
        "street": "Rua Vergueiro",
        "number": "890",
        "complement": "Casa",
        "neighborhood": "Vila Mariana",
        "city": "São Paulo",
        "state": "SP",
        "doctor": "joao.santos@medchain.com",
        "records": [
            {
                "type": "consultation",
                "data": {
                    "chief_complaint": "Dor torácica aos esforços",
                    "history_of_present_illness": "Dor opressiva ao subir escadas, melhora com repouso. Hipertenso.",
                    "diagnosis": "Angina estável — investigação",
                    "treatment_plan": "ECG, troponina, AAS; encaminhar ergometria",
                    "prescription": {
                        "items": [
                            {
                                "medication_name": "AAS",
                                "dosage": "100mg",
                                "frequency": "1x/dia",
                                "treatment_duration": "uso contínuo",
                            },
                            {
                                "medication_name": "Losartana",
                                "dosage": "50mg",
                                "frequency": "1x/dia",
                                "treatment_duration": "uso contínuo",
                            },
                        ]
                    },
                },
            },
            {
                "type": "diagnostic",
                "data": {
                    "description": "Eletrocardiograma",
                    "issue_date": "2026-07-22",
                    "result": "Ritmo sinusal; alterações inespecíficas de repolarização",
                },
            },
            {
                "type": "medical_certificate",
                "data": {
                    "purpose": "Afastamento para investigação cardiológica",
                    "period_of_leave": 3,
                },
            },
        ],
    },
    {
        "name": "Fernanda Lima",
        "email": "fernanda.lima@email.com",
        "phone": "11991001005",
        "dateofbirth": "1992-06-12",
        "gender": 1,
        "street": "Alameda Santos",
        "number": "220",
        "complement": "Apto 81",
        "neighborhood": "Cerqueira César",
        "city": "São Paulo",
        "state": "SP",
        "doctor": "joao.santos@medchain.com",
        "records": [
            {
                "type": "consultation",
                "data": {
                    "chief_complaint": "Palpitações e ansiedade",
                    "history_of_present_illness": "Episódios de taquicardia em situações de estresse.",
                    "diagnosis": "Palpitações benignas — correlacionar com ansiedade",
                    "treatment_plan": "Holter 24h, orientação sobre cafeína e sono",
                },
            },
            {
                "type": "diagnostic",
                "data": {
                    "description": "Holter 24 horas",
                    "issue_date": "2026-07-24",
                    "result": "Sem arritmias malignas; extrassístoles isoladas",
                },
            },
        ],
    },
    {
        "name": "Gabriel Souza",
        "email": "gabriel.souza@email.com",
        "phone": "11991001006",
        "dateofbirth": "2001-09-08",
        "gender": 0,
        "street": "Rua da Consolação",
        "number": "1500",
        "complement": "",
        "neighborhood": "Consolação",
        "city": "São Paulo",
        "state": "SP",
        "doctor": "maria.silva@medchain.com",
        "records": [
            {
                "type": "consultation",
                "data": {
                    "chief_complaint": "Dor lombar após academia",
                    "history_of_present_illness": "Dor mecânica há 4 dias, sem irradiação. Sem déficit neurológico.",
                    "diagnosis": "Lombalgia mecânica",
                    "treatment_plan": "Repouso relativo, alongamentos, AINE curto prazo",
                    "prescription": {
                        "items": [
                            {
                                "medication_name": "Ibuprofeno",
                                "dosage": "400mg",
                                "frequency": "8/8h",
                                "treatment_duration": "5 dias",
                            }
                        ]
                    },
                },
            },
            {
                "type": "medical_certificate",
                "data": {
                    "purpose": "Dispensa de atividade física intensa",
                    "period_of_leave": 5,
                },
            },
        ],
    },
]


def main() -> int:
    print("== MedChain seed demo ==")
    print(f"API: {BASE}\n")

    try:
        requests.get(f"{BASE.replace('/api/v1', '')}/docs", timeout=5)
    except Exception:
        print("ERRO: backend não respondeu em http://127.0.0.1:8000")
        print("Suba com: uvicorn app.main:app --reload")
        return 1

    sessions: dict[str, dict] = {}
    print("1) Médicos")
    for doctor in DOCTORS:
        sessions[doctor["email"]] = register_or_login_doctor(doctor)
        time.sleep(0.3)

    print("\n2) Pacientes + prontuários")
    for patient in PATIENTS:
        doctor_email = patient["doctor"]
        session = sessions[doctor_email]
        token = session["access_token"]
        doctor_id = session["user"].get("public_id") or session["user"].get("id")

        created = create_patient(token, patient)
        patient_id = created.get("patient_public_id") or created.get("uid")
        if not patient_id:
            print(f"  [erro] sem patient_public_id para {patient['email']}")
            continue

        for record in patient["records"]:
            try:
                create_record(token, doctor_id, patient_id, record["type"], record["data"])
                time.sleep(0.4)
            except Exception as exc:
                print(f"    [erro] {record['type']}: {exc}")

    print("\n" + "=" * 60)
    print("SEED CONCLUÍDO — use estas credenciais no front")
    print("=" * 60)
    print(f"\nSenha padrão de TODOS: {PASSWORD}\n")
    print("MÉDICOS")
    for d in DOCTORS:
        print(f"  {d['email']}  |  {d['full_name']}  |  {d['specialty']}")
    print("\nPACIENTES")
    for p in PATIENTS:
        print(f"  {p['email']}  |  {p['name']}  |  médico: {p['doctor']}")
    print("\nDica: login como maria.silva@medchain.com para ver dashboard cheio.")
    print("      Login como ana.oliveira@email.com (Sou Paciente) para ver o lado do paciente.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"\nFalha no seed: {exc}", file=sys.stderr)
        raise SystemExit(1)
