"""
Test manuel du Module IA #1 NLP.
Lance : python backend/tests/test_nlp_manual.py
"""
import asyncio, json, sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.services.ia_service import ia_comprendre_question
QUESTIONS = [
    "Combien de clients avons-nous en tout ?",
    "Quels sont les 5 produits les plus vendus ce mois ?",
    "Liste des clients de Tunis sans commande depuis 3 mois",
    "What is the total revenue for last year?",
    "Quelle est la météo à Sousse ?",  # Hors périmètre
]
async def main():
    print("\n🧠 TEST MODULE IA #1 — NLP")
    print("="*50)
    for q in QUESTIONS:
        print(f"\n📩 {q}")
        result = await ia_comprendre_question(q)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        hors = result.get("hors_perimetre", False)
        print(f"→ {'⛔ HORS PÉRIMÈTRE' if hors else '✅ OK — intention: '+result['intention']}")
asyncio.run(main())