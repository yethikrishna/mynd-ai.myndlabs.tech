"""
User/org-level LLM credentials, OAuth connections, and credential resolution.

System-level provider config still lives in Onyx's admin (``onyx.db.llm``).
This package layers user- and org-scoped credentials on top and resolves which
one to use at inference time with precedence:  user -> org -> system.
"""

from mynd.llm_auth.resolver import ResolvedCredential
from mynd.llm_auth.resolver import resolve_llm_credential

__all__ = ["ResolvedCredential", "resolve_llm_credential"]
