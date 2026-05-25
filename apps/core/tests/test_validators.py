"""Bateria de testes pra garantir que os validators não regridem."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.core.validators import (
    format_cnpj,
    format_cpf,
    format_phone,
    is_valid_cnpj,
    is_valid_cpf,
    is_valid_phone,
    normalize_document,
    validate_cpf,
    validate_cpf_or_cnpj,
)

# CPFs válidos conhecidos (verificadores corretos):
VALID_CPFS = ["52998224725", "11144477735", "390.533.447-05"]
INVALID_CPFS = [
    "12345678901",  # check digits errados
    "11111111111",  # sequência
    "00000000000",  # zeros
    "529.982.247-26",  # último dígito errado
    "529.982.247",  # incompleto
    "abcdefghijk",  # não-numérico
    "",  # vazio
]

VALID_CNPJS = ["11444777000161", "11.222.333/0001-81"]
INVALID_CNPJS = [
    "12345678000100",
    "11111111111111",
    "11.444.777/0001-62",
    "11444777000",
    "",
]


@pytest.mark.parametrize("cpf", VALID_CPFS)
def test_valid_cpf(cpf):
    assert is_valid_cpf(cpf)


@pytest.mark.parametrize("cpf", INVALID_CPFS)
def test_invalid_cpf(cpf):
    assert not is_valid_cpf(cpf)


def test_format_cpf():
    assert format_cpf("52998224725") == "529.982.247-25"


@pytest.mark.parametrize("cnpj", VALID_CNPJS)
def test_valid_cnpj(cnpj):
    assert is_valid_cnpj(cnpj)


@pytest.mark.parametrize("cnpj", INVALID_CNPJS)
def test_invalid_cnpj(cnpj):
    assert not is_valid_cnpj(cnpj)


def test_format_cnpj():
    assert format_cnpj("11444777000161") == "11.444.777/0001-61"


def test_validate_cpf_raises():
    with pytest.raises(ValidationError):
        validate_cpf("00000000000")


def test_validate_cpf_or_cnpj_accepts_both():
    validate_cpf_or_cnpj("52998224725")
    validate_cpf_or_cnpj("11.444.777/0001-61")


def test_validate_cpf_or_cnpj_rejects_intermediate_length():
    with pytest.raises(ValidationError):
        validate_cpf_or_cnpj("123456789012")  # 12 dígitos: nem cpf nem cnpj


def test_normalize_document():
    assert normalize_document("52998224725") == "529.982.247-25"
    assert normalize_document("11444777000161") == "11.444.777/0001-61"
    assert normalize_document("X") == "X"


@pytest.mark.parametrize(
    "phone",
    ["(11) 91234-5678", "11912345678", "(85) 3344-5566", "8533445566"],
)
def test_valid_phone(phone):
    assert is_valid_phone(phone)


@pytest.mark.parametrize(
    "phone",
    [
        "1234",
        "(00) 91234-5678",  # DDD começando com 0
        "(11) 81234-5678",  # móvel sem 9
        "",
    ],
)
def test_invalid_phone(phone):
    assert not is_valid_phone(phone)


def test_format_phone():
    assert format_phone("11912345678") == "(11) 91234-5678"
    assert format_phone("8533445566") == "(85) 3344-5566"
