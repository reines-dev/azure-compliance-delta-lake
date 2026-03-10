"""
ComplianceGuard - Suite de Aceptación E2E (AWS Production)
===========================================================
Diseño: Un registro verificado por cada fuente activa del Data Lake.
Ejecutar: python tests/acceptance_e2e_aws.py

Diseño de la prueba:
- Cada caso busca un nombre que se sabe existe en una fuente específica.
- La búsqueda se hace SIN filtro de fuente (global) para evitar errores 500
  si una partición no existe todavía en el Gold Layer.
- Se verifica que al menos un resultado provenga de la 'expected_source'.
- Esto prueba: Lambda (API Gateway) → S3 Gold Layer → búsqueda fuzzy.
"""
import requests
import sys
import os

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get(
    "COMPLIANCE_API_URL",
    "https://a4r3h4j1kl.execute-api.us-east-1.amazonaws.com/prod/check/"
)
API_KEY = os.environ.get("COMPLIANCE_API_KEY", "1UvGBiR4nW3S68KJmbKB59V7nHMU5kdJ7aHFFp07")
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

# ---------------------------------------------------------------------------
# Casos de prueba: un registro verificado por fuente
#
# expected_source: valor exacto de la columna `fuente` en el Parquet
# threshold: umbral de similitud (80+ es estricto, 60+ es permisivo)
#
# Registros seleccionados (verificados en producción el 2026-03-08):
#   OFAC:                GUSTAVO ANTONIA PETRO URREGO (sancionado SDN)
#   ONU:                 Al-Qaida (régimen ONU 1267)
#   US_FBI_MOST_WANTED:  OCHICHENKO (fugitivo FBI, apellido eslavo inusual)
#   US_DEA_FUGITIVES:    Sebastian Marset Cabrera (narco uruguayo)
#   INTERPOL_RED_NOTICES:Guzman Loera (El Chapo)
#   WORLDBANK:           China State Construction (empresa debarred)
#   EU_FSF:              Vladimir Putin (sanciones financieras UE)
#   FTO:                 Hizballah (organización terrorista)
#   CONTRALORIA:         ELECTRICARIBE (inhabilitada Colombia)
# ---------------------------------------------------------------------------
ACCEPTANCE_TESTS = [
    {
        "expected_source": "OFAC",
        "query": "Gustavo Petro Urrego",
        "threshold": 80,
        "note": "Presidente de Colombia sujeto a sanciones OFAC SDN"
    },
    {
        "expected_source": "ONU",
        "query": "Al-Qaida",
        "threshold": 70,
        "note": "Al-Qaida – régimen ONU Resolución 1267"
    },
    {
        "expected_source": "US_FBI_MOST_WANTED",
        "query": "OCHICHENKO",
        "threshold": 60,
        "note": "Fugitivo FBI – apellido eslavo de baja frecuencia"
    },
    {
        "expected_source": "US_DEA_FUGITIVES",
        "query": "Marset Cabrera",
        "threshold": 70,
        "note": "Sebastian Marset Cabrera – narco uruguayo buscado por el DEA"
    },
    {
        "expected_source": "INTERPOL_RED_NOTICES",
        "query": "Guzman Loera",
        "threshold": 70,
        "note": "Joaquín El Chapo Guzmán – Notificación Roja Interpol"
    },
    {
        "expected_source": "WORLDBANK",
        "query": "China State Construction",
        "threshold": 60,
        "note": "Empresa sancionada por Banco Mundial (debarred)"
    },
    {
        "expected_source": "EU_FSF",
        "query": "Vladimir Putin",
        "threshold": 75,
        "note": "Presidente de Rusia – Sanciones Financieras de la Unión Europea"
    },
    {
        "expected_source": "FTO",
        "query": "Hizballah",
        "threshold": 75,
        "note": "Hizballah – Organización terrorista FTO designada por EEUU"
    },
    {
        "expected_source": "CONTRALORIA",
        "query": "ELECTRICARIBE",
        "threshold": 70,
        "note": "Empresa inhabilitada por la Contraloría General de Colombia"
    },
]


def run_acceptance_suite(refresh_first: bool = True) -> int:
    print("=" * 90)
    print("  🛡️  COMPLIANCEGUARD – SUITE DE ACEPTACIÓN E2E (AWS Production)")
    print("=" * 90)
    print(f"  API:     {BASE_URL}")
    print(f"  Fuentes: {len(ACCEPTANCE_TESTS)}")
    print("=" * 90)
    print(f"{'FUENTE ESPERADA':<25} | {'BÚSQUEDA':<30} | RESULTADO")
    print("-" * 90)

    passed = 0
    failed = []

    for i, test in enumerate(ACCEPTANCE_TESTS):
        expected_src = test["expected_source"]
        query        = test["query"]
        thresh       = test["threshold"]

        # El primer request regenera el caché global del Lambda
        use_refresh = "true" if (refresh_first and i == 0) else "false"

        # Búsqueda global (sin source filter) para evitar 500 en particiones vacías
        params = {
            "name":      query,
            "threshold": thresh,
            "limit":     20,
            "refresh":   use_refresh,
        }

        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                status = f"❌ HTTP {resp.status_code}"
                failed.append({**test, "reason": f"HTTP {resp.status_code}"})
                print(f"{expected_src:<25} | {query:<30} | {status}")
                continue

            data = resp.json()
            results = data.get("results", [])

            # Verificar que al menos un resultado viene de la fuente esperada
            matching = [r for r in results if r.get("fuente") == expected_src]

            if matching:
                top = matching[0]
                score  = top["score"]
                nombre = top["nombre_original"][:38]
                passed += 1
                status = f"✅ PASSED  {score}% | '{nombre}'"
            else:
                # Puede haber resultados, pero de otras fuentes
                fuentes_encontradas = list({r["fuente"] for r in results})
                if fuentes_encontradas:
                    status = f"❌ FUENTE NO ENCONTRADA (resultados en {fuentes_encontradas})"
                else:
                    status = f"❌ NO ENCONTRADO (umbral {thresh}%)"
                failed.append({**test, "reason": status})

        except requests.exceptions.Timeout:
            status = "❌ TIMEOUT (>30s)"
            failed.append({**test, "reason": "TIMEOUT"})
        except Exception as e:
            status = f"❌ ERROR: {str(e)[:40]}"
            failed.append({**test, "reason": str(e)[:60]})

        print(f"{expected_src:<25} | {query:<30} | {status}")

    total = len(ACCEPTANCE_TESTS)
    pct   = (passed / total) * 100

    print("=" * 90)
    print(f"  RESULTADO: {passed}/{total} fuentes operativas ({pct:.1f}%)")
    print("=" * 90)

    if failed:
        print("\n  ⚠️  Fuentes con problemas:")
        for f in failed:
            print(f"     • [{f['expected_source']}] {f['query']}")
            print(f"       Razón: {f['reason']}")
            print(f"       Nota:  {f['note']}")

    if passed == total:
        print("\n  🎉 ¡SISTEMA COMPLETAMENTE CERTIFICADO PARA PRODUCCIÓN!\n")
        return 0
    else:
        print(f"\n  🔴  {total - passed} fuente(s) fallaron. Revisar pipeline ELT.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_acceptance_suite())
