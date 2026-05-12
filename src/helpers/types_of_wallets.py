import itertools


def symmetric_wallet(key_count, threshold):
    """Generate a symmetric (k-of-n) wallet as OR of all size-k conjunctions."""
    if key_count <= 0:
        raise ValueError("key_count must be positive")
    if threshold <= 0 or threshold > key_count:
        raise ValueError("threshold must be in [1, key_count]")

    wallet = []
    for combo in itertools.combinations(range(1, key_count + 1), threshold):
        mask = 0
        for idx in combo:
            mask |= 1 << (idx - 1)
        wallet.append(mask)
    return wallet


def symmetric_wallet_threshold(wallet):
    """Infer the k threshold from a symmetric wallet."""
    if not wallet:
        raise ValueError("wallet must not be empty")

    threshold = int(wallet[0]).bit_count()
    if any(int(bitmask).bit_count() != threshold for bitmask in wallet):
        raise ValueError("wallet is not symmetric: bitmasks have different sizes")

    return threshold


def generate_all_bitmasks(key_count):
    return [i for i in range(2 ** key_count)]


def generate_bitmasks_above_threshold(key_count, threshold):
    return [i for i in range(2 ** key_count) if bin(i).count("1") >= threshold]


def generate_single_bitmask(amount_of_available_keys):
    return 2 ** amount_of_available_keys - 1

