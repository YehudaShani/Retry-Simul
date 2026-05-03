"""Unit tests for wallet_state module."""
import pytest
from retry_simul.wallet_state import WalletState


class TestWalletStateConstruction:
    def test_valid_construction(self, uniform_probs):
        ws = WalletState(3, [0b011, 0b100], uniform_probs)
        assert ws.key_count == 3
        assert ws.bitmasks == [0b011, 0b100]

    def test_invalid_key_count_raises(self, uniform_probs):
        with pytest.raises(ValueError, match="positive"):
            WalletState(0, [], uniform_probs)
        with pytest.raises(ValueError, match="positive"):
            WalletState(-1, [], uniform_probs)

    def test_negative_bitmask_raises(self, uniform_probs):
        with pytest.raises(ValueError, match="non-negative"):
            WalletState(3, [-1], uniform_probs)


class TestAddRemoveBitmask:
    def test_add_bitmask(self, uniform_probs):
        ws = WalletState(3, [], uniform_probs)
        ws.add_bitmask(0b011)
        assert 0b011 in ws.bitmasks
        ws.add_bitmask(0b100)
        assert ws.bitmasks == [0b011, 0b100]

    def test_remove_bitmask(self, uniform_probs):
        ws = WalletState(3, [0b011, 0b100], uniform_probs)
        ws.remove_bitmask(0b011)
        assert ws.bitmasks == [0b100]

    def test_add_invalid_raises(self, uniform_probs):
        ws = WalletState(3, [], uniform_probs)
        with pytest.raises(ValueError, match="non-negative"):
            ws.add_bitmask(-1)

    def test_remove_bitmask_and_subsets_1(self, uniform_probs):
        ws = WalletState(3, [0b001, 0b011, 0b111], uniform_probs)
        ws.remove_bitmask_and_subsets(0b011)
        assert ws.bitmask_is_in_wallet(0b111)

    def test_remove_bitmask_and_subsets_2(self, uniform_probs):
        ws = WalletState(3, [0b001, 0b010, 0b011, 0b100], uniform_probs)
        ws.remove_bitmask_and_subsets(0b011)
        assert ws.bitmask_is_in_wallet(0b100)

    def test_remove_bitmask_and_subsets_3(self, uniform_probs):
        ws = WalletState(3, [0b001, 0b010], uniform_probs)
        ws.remove_bitmask_and_subsets(0b001)
        assert ws.bitmask_is_in_wallet(0b101)
        assert ws.bitmask_is_in_wallet(0b111)

    def test_remove_bitmask_and_subsets_4(self, uniform_probs):
        ws = WalletState(3, [0b001, 0b011], uniform_probs)
        ws.remove_bitmask_and_subsets(0b011)
        assert ws.bitmask_is_in_wallet(0b101)
        assert ws.bitmask_is_in_wallet(0b111)

    def test_add_then_remove(self, uniform_probs):
        ws = WalletState(3, [], uniform_probs)
        ws.add_bitmask(0b111)
        ws.add_bitmask(0b011)
        ws.add_bitmask(0b101)
        ws.add_bitmask(0b110)
        ws.remove_bitmask(0b110)
        assert ws.bitmask_is_in_wallet(0b011)

    def test_add_then_remove2(self, uniform_probs):
        ws = WalletState(5, [], uniform_probs)
        ws.add_bitmask(15)
        ws.add_bitmask(23)
        ws.add_bitmask(27)
        ws.add_bitmask(29)
        ws.add_bitmask(3)
        ws.add_bitmask(5)
        ws.add_bitmask(6)
        ws.add_bitmask(9)
        ws.add_bitmask(10)
        ws.add_bitmask(12)
        ws.add_bitmask(17)
        ws.add_bitmask(18)
        ws.add_bitmask(20)
        ws.add_bitmask(24)
        ws.remove_bitmask_and_subsets(15)
        assert not ws.bitmask_is_in_wallet(15)

class TestComputeSuccessProbability:
    def test_returns_valid_probability(self, uniform_probs):
        ws = WalletState(3, [0b111], uniform_probs)
        p = ws.compute_success_probability()
        assert 0 <= p <= 1.0

    def test_empty_wallet_zero_success(self, uniform_probs):
        ws = WalletState(3, [], uniform_probs)
        p = ws.compute_success_probability()
        assert p == pytest.approx(0.0)


class TestStr:
    def test_str_includes_bitmasks_and_key_count(self, uniform_probs):
        ws = WalletState(3, [0b011, 0b100], uniform_probs)
        s = str(ws)
        assert "3" in s
        assert "bitmasks" in s or str(ws.bitmasks) in s
