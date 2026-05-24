"""Thread-local que armazena o tenant ativo da requisição corrente.

Usado por `TenantManager` para filtrar querysets sem que cada view precise
passar `company` explicitamente. Definido em `TenantMiddleware`.

ATENÇÃO: em código rodando fora de request (tarefas em background, shell,
testes), use `with company_scope(company): ...` para garantir o filtro.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from apps.companies.models import Company

_current_company: ContextVar["Company | None"] = ContextVar(
    "lupa_current_company", default=None
)


def set_current_company(company: "Company | None") -> None:
    """Define o tenant ativo. Chamado pelo middleware no início da request."""
    _current_company.set(company)


def get_current_company() -> "Company | None":
    """Retorna o tenant ativo, ou None se nenhum foi definido."""
    return _current_company.get()


@contextmanager
def company_scope(company: "Company | None") -> Iterator[None]:
    """Define o tenant em um escopo limitado (background tasks, scripts).

    Exemplo:
        with company_scope(empresa):
            Ticket.objects.filter(status="confirmed")
    """
    token = _current_company.set(company)
    try:
        yield
    finally:
        _current_company.reset(token)
