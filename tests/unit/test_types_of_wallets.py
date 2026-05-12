"""Unit tests for types_of_wallets module."""
import pytest
from helpers.types_of_wallets import symmetric_wallet, generate_all_bitmasks


class TestSymmetricWallet:
    def test_2_of_3_wallet(self):
        w = symmetric_wallet(3, 2)
        # C(3,2) = 3 combinations: (1,2), (1,3), (2,3)
        assert len(w) == 3
        assert 0b011 in w
        assert 0b101 in w
        assert 0b110 in w

    def test_1_of_n_all_single_keys(self):
        w = symmetric_wallet(4, 1)
        assert len(w) == 4
        assert w == [1, 2, 4, 8]

    def test_n_of_n_single_combination(self):
        w = symmetric_wallet(3, 3)
        assert len(w) == 1
        assert w[0] == 0b111

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            symmetric_wallet(3, 0)
        with pytest.raises(ValueError):
            symmetric_wallet(3, 4)


class TestGenerateAllBitmasks:
    def test_count(self):
        assert len(generate_all_bitmasks(3)) == 8
        assert len(generate_all_bitmasks(4)) == 16
