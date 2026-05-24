"""Validators de documentos e contatos brasileiros.

Algoritmos oficiais — não confiar em regex bonita.
Frontend espelha em static/js/masks.js, mas backend é a fonte da verdade.
"""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
_DIGITS_ONLY = re.compile(r"\D")


def only_digits(value: str | None) -> str:
    return _DIGITS_ONLY.sub("", value or "")


# ─────────────────────────────────────────────────────────
# CPF
# ─────────────────────────────────────────────────────────
def _cpf_check_digit(digits: str, weights: range) -> int:
    total = sum(int(d) * w for d, w in zip(digits, weights, strict=False))
    rest = total % 11
    return 0 if rest < 2 else 11 - rest


def is_valid_cpf(value: str) -> bool:
    cpf = only_digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    if _cpf_check_digit(cpf[:9], range(10, 1, -1)) != int(cpf[9]):
        return False
    if _cpf_check_digit(cpf[:10], range(11, 1, -1)) != int(cpf[10]):
        return False
    return True


def format_cpf(value: str) -> str:
    cpf = only_digits(value)
    if len(cpf) != 11:
        return value
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


# ─────────────────────────────────────────────────────────
# CNPJ
# ─────────────────────────────────────────────────────────
def _cnpj_check_digit(digits: str, weights: list[int]) -> int:
    total = sum(int(d) * w for d, w in zip(digits, weights, strict=False))
    rest = total % 11
    return 0 if rest < 2 else 11 - rest


def is_valid_cnpj(value: str) -> bool:
    cnpj = only_digits(value)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    if _cnpj_check_digit(cnpj[:12], w1) != int(cnpj[12]):
        return False
    if _cnpj_check_digit(cnpj[:13], w2) != int(cnpj[13]):
        return False
    return True


def format_cnpj(value: str) -> str:
    cnpj = only_digits(value)
    if len(cnpj) != 14:
        return value
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


# ─────────────────────────────────────────────────────────
# Validators Django (uso em Field.validators=[...])
# ─────────────────────────────────────────────────────────
def validate_cpf(value: str) -> None:
    if not is_valid_cpf(value):
        raise ValidationError(
            "CPF inválido. Verifique os números e tente novamente.",
            code="cpf_invalid",
        )


def validate_cnpj(value: str) -> None:
    if not is_valid_cnpj(value):
        raise ValidationError(
            "CNPJ inválido. Verifique os números e tente novamente.",
            code="cnpj_invalid",
        )


def validate_cpf_or_cnpj(value: str) -> None:
    """Aceita CPF ou CNPJ — útil pra empresa (MEI usa CPF, demais usam CNPJ)."""
    digits = only_digits(value)
    if len(digits) == 11:
        validate_cpf(digits)
    elif len(digits) == 14:
        validate_cnpj(digits)
    else:
        raise ValidationError(
            "Informe um CPF (11 dígitos) ou CNPJ (14 dígitos).",
            code="doc_invalid_length",
        )


def normalize_document(value: str) -> str:
    """Retorna o documento formatado conforme o tipo (CPF ou CNPJ)."""
    digits = only_digits(value)
    if len(digits) == 11:
        return format_cpf(digits)
    if len(digits) == 14:
        return format_cnpj(digits)
    return value


# ─────────────────────────────────────────────────────────
# Telefone BR
# ─────────────────────────────────────────────────────────
def is_valid_phone(value: str) -> bool:
    digits = only_digits(value)
    # Aceita 10 (fixo: DD+8) ou 11 (móvel: DD+9) dígitos.
    if len(digits) not in (10, 11):
        return False
    # DDD entre 11 e 99 (1º dígito 1-9, 2º dígito 1-9)
    if digits[0] == "0" or digits[1] == "0":
        return False
    # Móvel começa com 9
    if len(digits) == 11 and digits[2] != "9":
        return False
    return True


def format_phone(value: str) -> str:
    digits = only_digits(value)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return value


def validate_phone_br(value: str) -> None:
    if not is_valid_phone(value):
        raise ValidationError(
            "Telefone inválido. Use o formato (DD) 9XXXX-XXXX ou (DD) XXXX-XXXX.",
            code="phone_invalid",
        )
