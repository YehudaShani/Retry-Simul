"""Unit tests for symbolic polynomial formatting."""

from retry_simul.symbols import (
    UI_MONOMIAL_STATE_LABELS,
    format_success_probability_polynomial,
    format_signed_polynomial_sum,
)


def test_compact_labels_no_p_prefix():
    coeffs = {(2, 0, 0, 0): 1}
    out = format_success_probability_polynomial(
        coeffs,
        variable_prefix="",
        state_labels=UI_MONOMIAL_STATE_LABELS,
        multiline=False,
        use_unicode=False,
    )
    assert out == "S^2"
    assert "p_SAFE" not in out
    assert "_" not in out  # no p_LOST-style joins


def test_compact_signed_polynomial_sum_uses_letters():
    diff = {(1, 0, 0, 0): 1, (0, 1, 0, 0): -1}
    out = format_signed_polynomial_sum(
        diff,
        variable_prefix="",
        state_labels=UI_MONOMIAL_STATE_LABELS,
        multiline=False,
        use_unicode=False,
    )
    assert "S" in out
    assert "O" in out
    assert "p_" not in out
