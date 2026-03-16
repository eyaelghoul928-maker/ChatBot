import re


class SQLValidator:

    FORBIDDEN_KEYWORDS = {
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
        "INSERT", "UPDATE", "REPLACE", "RENAME", "LOCK",
        "UNLOCK", "GRANT", "REVOKE", "LOAD", "OUTFILE",
        "DUMPFILE", "INTO", "CALL", "EXEC", "EXECUTE",
        "SHUTDOWN", "FLUSH", "KILL", "RESET",
    }

    RESTRICTED_TABLES = {"users", "query_logs"}

    INJECTION_PATTERNS = [
        r"(\bOR\b\s+[\w'\"]+\s*=\s*[\w'\"]+)",
        r"UNION\s+SELECT",
        r"--\s*$",
        r"/\*.*?\*/",
        r";\s*\w+",
        r"0x[0-9a-fA-F]+",
        r"\bSLEEP\s*\(",
        r"\bBENCHMARK\s*\(",
        r"\bCHAR\s*\(",
    ]

    def validate(self, sql: str, user_role: str = "user", user_id: int = None) -> dict:
        sql = sql.strip()

        # 1. Doit commencer par SELECT
        if not sql.upper().startswith("SELECT"):
            return {"valid": False, "reason": "Seules les requêtes SELECT sont autorisées", "sql": sql}

        # 2. Mots-clés interdits
        sql_upper = sql.upper()
        for kw in self.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", sql_upper):
                return {"valid": False, "reason": f"Mot-clé interdit : {kw}", "sql": sql}

        # 3. Patterns d'injection
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return {"valid": False, "reason": "Pattern d'injection détecté", "sql": sql}

        # 4. Tables restreintes pour non-admin
        if user_role != "admin":
            for table in self.RESTRICTED_TABLES:
                if re.search(rf"\b{table}\b", sql, re.IGNORECASE):
                    return {"valid": False, "reason": f"Table restreinte : {table}", "sql": sql}

        # 5. Ajouter LIMIT si absent
        if "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + " LIMIT 100"

        return {"valid": True, "reason": None, "sql": sql}