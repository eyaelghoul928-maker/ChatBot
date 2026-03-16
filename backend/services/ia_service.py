"""
ia_service.py — Pipeline IA universel
S'adapte automatiquement à n'importe quelle base de données MariaDB.
Le schéma est découvert dynamiquement au démarrage.
"""
from openai import AsyncOpenAI
from config import settings
from loguru import logger
import json
import httpx
client = AsyncOpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1",
)

# Schéma découvert dynamiquement (rempli au démarrage via discover_schema())
_DB_SCHEMA = ""


async def discover_schema() -> str:
    """
    Découvre automatiquement toutes les tables et colonnes
    de la base de données connectée.
    Appelé une seule fois au démarrage du backend.
    """
    global _DB_SCHEMA
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            # Demander au MCP Server le schéma complet
            resp = await http.post(
                f"{settings.mcp_base_url}/schema",
                headers={"x-internal-key": settings.mcp_internal_key}
            )
            if resp.status_code == 200:
                schema_data = resp.json()
                _DB_SCHEMA = schema_data["schema"]
                logger.info(f"[SCHEMA] Découvert: {schema_data['nb_tables']} tables")
                return _DB_SCHEMA
    except Exception as e:
        logger.error(f"[SCHEMA] Erreur découverte: {e}")
        _DB_SCHEMA = "Schéma non disponible"
        return _DB_SCHEMA


def get_schema() -> str:
    return _DB_SCHEMA


def build_nlp_prompt() -> str:
    return """Tu es un expert NLP multilingue. Analyse la question et retourne UNIQUEMENT un JSON valide.

Champs obligatoires:
- intention: comptage|liste|aggregation|classement|recherche|calcul|hors_perimetre
- entites: liste des entités mentionnées dans la question
- tables_cibles: tables SQL probablement concernées (basé sur les entités)
- langue: fr|ar|en
- complexite: simple|complexe
- periode: null|aujourd_hui|semaine_courante|mois_courant|annee_courante|historique
- limite: nombre entier ou null
- hors_perimetre: true UNIQUEMENT si la question n'a aucun rapport avec les données métier

Retourne UNIQUEMENT le JSON, sans texte avant ou après."""


def build_sql_prompt() -> str:
    schema = get_schema()
    return f"""Tu es un expert SQL MariaDB avec 15 ans d'expérience.

SCHÉMA COMPLET DE LA BASE DE DONNÉES:
{schema}

RÈGLES ABSOLUES — NE JAMAIS VIOLER:
1. Retourne UNIQUEMENT la requête SQL brute — zéro texte, zéro backtick, zéro explication
2. Utilise EXCLUSIVEMENT SELECT — jamais INSERT, UPDATE, DELETE, DROP, ALTER
3. Ajoute LIMIT {settings.sql_limit_max} si aucune limite n'est précisée
4. Utilise des aliases lisibles: COUNT(*) AS nb_colis, SUM(prix) AS total_ventes
5. Vérifie que toutes les tables et colonnes existent dans le schéma ci-dessus
6. Pour les dates: NOW(), CURDATE(), MONTH(), YEAR(), DATE_SUB(), INTERVAL
7. Joins explicites: JOIN table ON cond (jamais de virgule entre tables)
8. GROUP BY obligatoire si tu utilises COUNT/SUM/AVG avec d'autres colonnes
9. Si la question est ambiguë, génère la requête la plus utile possible"""


SYSTEM_NLG = {
    "fr": "Tu es un assistant business expert. Reformule ces données en réponse claire, naturelle et professionnelle en français. Commence directement par la réponse sans phrase d'introduction générique.",
    "ar": "أنت مساعد أعمال خبير. أعد صياغة هذه البيانات كإجابة واضحة وطبيعية ومهنية باللغة العربية.",
    "en": "You are an expert business assistant. Reformulate this data as a clear, natural and professional response in English. Start directly with the answer.",
}


async def ia_comprendre_question(question: str) -> dict:
    logger.info(f"[NLP] ← {question[:70]}")
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": build_nlp_prompt()},
                {"role": "user", "content": f"Question: {question}"}
            ],
            temperature=settings.temperature_nlp,
            max_tokens=settings.max_tokens_nlp,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        logger.info(f"[NLP] → intention={result.get('intention')} langue={result.get('langue')} hors_perimetre={result.get('hors_perimetre')}")
        return result
    except Exception as e:
        logger.error(f"[NLP] Erreur: {e}")
        return {
            "intention": "erreur", "entites": [], "tables_cibles": [],
            "langue": "fr", "complexite": "simple", "periode": None,
            "limite": None, "hors_perimetre": False, "_error": str(e)
        }


async def ia_generer_sql(analyse: dict, retry_error: str = None) -> str:
    prompt = f"Analyse NLP: {json.dumps(analyse, ensure_ascii=False)}"
    if retry_error:
        prompt += f"\n\nCette requête a échoué: {retry_error}\nCorrige-la."

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": build_sql_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.temperature_sql,
            max_tokens=settings.max_tokens_sql,
        )
        sql = response.choices[0].message.content.strip()
        # Nettoyer les backticks si GPT en met quand même
        sql = sql.replace("```sql", "").replace("```", "").strip()
        logger.info(f"[SQL] → {sql[:100]}")
        return sql
    except Exception as e:
        logger.error(f"[SQL] Erreur: {e}")
        raise


async def ia_reformuler_reponse(question: str, data: list, langue: str) -> str:
    if not data:
        messages = {
            "fr": "Aucun résultat trouvé pour cette question dans la base de données.",
            "ar": "لم يتم العثور على نتائج لهذا السؤال في قاعدة البيانات.",
            "en": "No results found for this question in the database.",
        }
        return messages.get(langue, messages["fr"])

    system = SYSTEM_NLG.get(langue, SYSTEM_NLG["fr"])
    # Envoyer max 10 lignes à GPT pour économiser les tokens
    data_preview = data[:10]
    total = len(data)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": (
                    f"Question posée: {question}\n"
                    f"Données ({total} résultats au total, voici les premiers):\n"
                    f"{json.dumps(data_preview, ensure_ascii=False, default=str)}"
                )}
            ],
            temperature=settings.temperature_nlg,
            max_tokens=settings.max_tokens_nlg,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[NLG] Erreur: {e}")
        return f"{len(data)} résultat(s) trouvé(s). Erreur de reformulation: {str(e)}"


async def run_full_pipeline(question: str, user_id: int, user_role: str) -> dict:
    from services.cache_service import get_cached_response, set_cached_response

    # ── 1. Cache Redis ────────────────────────────────────────────────
    cached = await get_cached_response(question)
    if cached:
        cached["cached"] = True
        logger.info(f"[PIPELINE] Cache HIT pour: {question[:40]}")
        return cached

    # ── 2. IA #1 — Comprendre la question ────────────────────────────
    analyse = await ia_comprendre_question(question)
    langue = analyse.get("langue", "fr")

    # ── 3. Hors périmètre ? ───────────────────────────────────────────
    if analyse.get("hors_perimetre"):
        messages = {
            "fr": "Je suis spécialisé dans l'analyse des données de cette base. Cette question est en dehors de mon domaine.",
            "ar": "أنا متخصص في تحليل بيانات قاعدة البيانات. هذا السؤال خارج نطاق عملي.",
            "en": "I specialize in analyzing this database. This question is outside my scope.",
        }
        return {
            "reponse": messages.get(langue, messages["fr"]),
            "sql": None, "nb_resultats": 0, "langue": langue, "cached": False
        }

    # ── 4. IA #2 + MCP — Générer SQL et exécuter (3 tentatives) ──────
    data = []
    sql = None
    last_error = None

    for attempt in range(3):
        try:
            sql = await ia_generer_sql(analyse, retry_error=last_error)

            async with httpx.AsyncClient(timeout=20.0) as http:
                resp = await http.post(
                    f"{settings.mcp_base_url}/execute",
                    json={"sql": sql, "user_id": user_id, "user_role": user_role},
                    headers={"x-internal-key": settings.mcp_internal_key}
                )

            if resp.status_code == 200:
                data = resp.json()["data"]
                logger.info(f"[PIPELINE] Tentative {attempt+1} OK — {len(data)} lignes")
                break
            else:
                last_error = resp.json().get("detail", f"Erreur HTTP {resp.status_code}")
                logger.warning(f"[PIPELINE] Tentative {attempt+1} échouée: {last_error}")

        except Exception as e:
            last_error = str(e)
            logger.error(f"[PIPELINE] Tentative {attempt+1} exception: {e}")

    # ── 5. IA #3 — Reformuler ─────────────────────────────────────────
    reponse = await ia_reformuler_reponse(question, data, langue)

    result = {
        "reponse": reponse,
        "sql": sql,
        "nb_resultats": len(data),
        "langue": langue,
        "cached": False,
    }

    # ── 6. Mettre en cache si succès ──────────────────────────────────
    if data:
        await set_cached_response(question, result)

    return result