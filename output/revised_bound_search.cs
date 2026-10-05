using System;
using System.Collections.Generic;
using System.IO;

// Exact common-denominator grid search for the proposed pairwise-safe region.
// Compile from the repository root with:
//   Add-Type -Path output/revised_bound_search.cs -OutputAssembly output/revised_bound_search.exe -OutputType ConsoleApplication
// Run with:
//   output/revised_bound_search.exe 6 40
public static class RevisedBoundSearch
{
    private sealed class WalletData
    {
        public int[] Terms;
        public bool[] Truth;
        public int IncompleteCount;
        public int[] IncompleteRanks;
        public bool IsDictator;
        public SparsePoly Score;
        public SparsePoly[] Gains;
    }

    private sealed class SparsePoly
    {
        public int[] Codes;
        public int[] Coeffs;
    }

    private static int PopCount(int x)
    {
        int count = 0;
        while (x != 0) { x &= x - 1; ++count; }
        return count;
    }

    private static bool IsPowerOfTwo(int x)
    {
        return x > 0 && (x & (x - 1)) == 0;
    }

    // The cache JSON is just a nested array of nonnegative integers. This
    // deliberately tiny parser avoids external package dependencies.
    private static List<int[]> ReadWallets(string path)
    {
        string text = File.ReadAllText(path);
        var wallets = new List<int[]>();
        var current = new List<int>();
        int depth = 0;
        for (int i = 0; i < text.Length; ++i)
        {
            char ch = text[i];
            if (ch == '[')
            {
                ++depth;
                if (depth == 2) current.Clear();
            }
            else if (ch == ']')
            {
                if (depth == 2) wallets.Add(current.ToArray());
                --depth;
            }
            else if (depth == 2 && ch >= '0' && ch <= '9')
            {
                int value = 0;
                while (i < text.Length && text[i] >= '0' && text[i] <= '9')
                {
                    value = 10 * value + (text[i] - '0');
                    ++i;
                }
                --i;
                current.Add(value);
            }
        }
        return wallets;
    }

    private static bool[] BuildTruth(int n, int[] terms)
    {
        int size = 1 << n;
        var truth = new bool[size];
        for (int mask = 0; mask < size; ++mask)
        {
            for (int j = 0; j < terms.Length; ++j)
            {
                if ((mask & terms[j]) == terms[j])
                {
                    truth[mask] = true;
                    break;
                }
            }
        }
        return truth;
    }

    private static int[] IncompleteRanks(int n, bool[] truth)
    {
        var result = new List<int>();
        for (int rank = 0; rank <= n; ++rank)
        {
            int total = 0, covered = 0;
            for (int mask = 0; mask < truth.Length; ++mask)
            {
                if (PopCount(mask) == rank)
                {
                    ++total;
                    if (truth[mask]) ++covered;
                }
            }
            if (covered > 0 && covered < total) result.Add(rank);
        }
        return result.ToArray();
    }

    private static int Encode(int n, int safe, int stolen, int leaked, int lost)
    {
        int b = n + 1;
        return ((safe * b + stolen) * b + leaked) * b + lost;
    }

    private static int[] StateCodes(int n)
    {
        int size = 1 << n;
        var codes = new int[size * size];
        int full = size - 1;
        for (int owner = 0; owner < size; ++owner)
        {
            for (int attacker = 0; attacker < size; ++attacker)
            {
                int leaked = PopCount(owner & attacker);
                int safe = PopCount(owner & (~attacker) & full);
                int stolen = PopCount((~owner) & attacker & full);
                int lost = n - safe - stolen - leaked;
                codes[owner * size + attacker] = Encode(n, safe, stolen, leaked, lost);
            }
        }
        return codes;
    }

    private static SparsePoly ScorePoly(int n, bool[] truth, int[] stateCodes)
    {
        int b = n + 1;
        var dense = new int[b * b * b * b];
        int size = 1 << n;
        for (int owner = 0; owner < size; ++owner)
        {
            if (!truth[owner]) continue;
            int offset = owner * size;
            for (int attacker = 0; attacker < size; ++attacker)
            {
                if (!truth[attacker]) ++dense[stateCodes[offset + attacker]];
            }
        }
        return SparseFromDense(dense);
    }

    private static SparsePoly Difference(SparsePoly after, SparsePoly before, int denseLength)
    {
        var dense = new int[denseLength];
        for (int i = 0; i < after.Codes.Length; ++i) dense[after.Codes[i]] += after.Coeffs[i];
        for (int i = 0; i < before.Codes.Length; ++i) dense[before.Codes[i]] -= before.Coeffs[i];
        return SparseFromDense(dense);
    }

    private static SparsePoly SparseFromDense(int[] dense)
    {
        var codes = new List<int>();
        var coeffs = new List<int>();
        for (int i = 0; i < dense.Length; ++i)
        {
            if (dense[i] != 0)
            {
                codes.Add(i);
                coeffs.Add(dense[i]);
            }
        }
        return new SparsePoly { Codes = codes.ToArray(), Coeffs = coeffs.ToArray() };
    }

    private static bool[] EditTruth(int n, bool[] original, int rank, bool value)
    {
        var edited = (bool[])original.Clone();
        for (int mask = 0; mask < edited.Length; ++mask)
            if (PopCount(mask) == rank) edited[mask] = value;
        return edited;
    }

    private static long[] Powers(int value, int n)
    {
        var powers = new long[n + 1];
        powers[0] = 1;
        for (int i = 1; i <= n; ++i) powers[i] = powers[i - 1] * value;
        return powers;
    }

    private static long[] Weights(int n, int safe, int stolen, int leaked, int lost)
    {
        int b = n + 1;
        var weights = new long[b * b * b * b];
        long[] ps = Powers(safe, n), pt = Powers(stolen, n);
        long[] pe = Powers(leaked, n), pl = Powers(lost, n);
        for (int a = 0; a <= n; ++a)
            for (int t = 0; t <= n - a; ++t)
                for (int e = 0; e <= n - a - t; ++e)
                {
                    int l = n - a - t - e;
                    weights[Encode(n, a, t, e, l)] = ps[a] * pt[t] * pe[e] * pl[l];
                }
        return weights;
    }

    private static long Evaluate(SparsePoly poly, long[] weights)
    {
        long sum = 0;
        for (int i = 0; i < poly.Codes.Length; ++i)
            sum += (long)poly.Coeffs[i] * weights[poly.Codes[i]];
        return sum;
    }

    private static decimal[] PowersDecimal(int value, int n)
    {
        var powers = new decimal[n + 1];
        powers[0] = 1m;
        for (int i = 1; i <= n; ++i) powers[i] = powers[i - 1] * value;
        return powers;
    }

    private static decimal[] WeightsDecimal(
        int n, int safe, int stolen, int leaked, int lost)
    {
        int b = n + 1;
        var weights = new decimal[b * b * b * b];
        decimal[] ps = PowersDecimal(safe, n), pt = PowersDecimal(stolen, n);
        decimal[] pe = PowersDecimal(leaked, n), pl = PowersDecimal(lost, n);
        for (int a = 0; a <= n; ++a)
            for (int t = 0; t <= n - a; ++t)
                for (int e = 0; e <= n - a - t; ++e)
                {
                    int l = n - a - t - e;
                    weights[Encode(n, a, t, e, l)] = ps[a] * pt[t] * pe[e] * pl[l];
                }
        return weights;
    }

    private static decimal EvaluateDecimal(SparsePoly poly, decimal[] weights)
    {
        decimal sum = 0m;
        for (int i = 0; i < poly.Codes.Length; ++i)
            sum += poly.Coeffs[i] * weights[poly.Codes[i]];
        return sum;
    }

    private static string TermsString(int[] terms)
    {
        return "[" + string.Join(",", terms) + "]";
    }

    // Exact x^T K^(tensor n) (1-x), where
    // K = [[lost, stolen], [safe, leaked]] and all entries are integer
    // numerators over a common denominator.
    private static long TensorScore(
        int n, bool[] truth, int safe, int stolen, int leaked, int lost)
    {
        int size = 1 << n;
        var values = new long[size];
        for (int i = 0; i < size; ++i) values[i] = truth[i] ? 0 : 1;
        for (int bit = 0; bit < n; ++bit)
        {
            int step = 1 << bit;
            for (int block = 0; block < size; block += 2 * step)
                for (int j = 0; j < step; ++j)
                {
                    int i0 = block + j, i1 = i0 + step;
                    long v0 = values[i0], v1 = values[i1];
                    values[i0] = lost * v0 + stolen * v1;
                    values[i1] = safe * v0 + leaked * v1;
                }
        }
        long score = 0;
        for (int i = 0; i < size; ++i) if (truth[i]) score += values[i];
        return score;
    }

    private static int[] RandomAntichain(int n, Random rng)
    {
        int maxMask = (1 << n) - 1;
        int attempts = 2 + rng.Next(Math.Min(30, maxMask - 1));
        var terms = new List<int>();
        for (int k = 0; k < attempts; ++k)
        {
            int candidate = 1 + rng.Next(maxMask);
            bool redundant = false;
            for (int i = 0; i < terms.Count; ++i)
                if ((candidate & terms[i]) == terms[i]) { redundant = true; break; }
            if (redundant) continue;
            for (int i = terms.Count - 1; i >= 0; --i)
                if ((candidate & terms[i]) == candidate) terms.RemoveAt(i);
            terms.Add(candidate);
        }
        terms.Sort();
        return terms.ToArray();
    }

    private static int[] TruthToTerms(int n, bool[] truth)
    {
        var terms = new List<int>();
        for (int mask = 1; mask < (1 << n); ++mask)
        {
            if (!truth[mask]) continue;
            bool minimal = true;
            for (int bit = 0; bit < n; ++bit)
                if ((mask & (1 << bit)) != 0 && truth[mask ^ (1 << bit)])
                {
                    minimal = false;
                    break;
                }
            if (minimal) terms.Add(mask);
        }
        return terms.ToArray();
    }

    // Mixture of weighted thresholds, two-block count rules, and nested
    // near-dictators F=(x_1 AND P) OR Q with Q subset P.
    private static int[] StructuredAntichain(int n, Random rng)
    {
        int kind = rng.Next(4);
        int size = 1 << n;
        var truth = new bool[size];
        if (kind == 0)
        {
            var weights = new int[n];
            int total = 0;
            for (int i = 0; i < n; ++i) { weights[i] = 1 + rng.Next(9); total += weights[i]; }
            int threshold = 1 + rng.Next(total);
            for (int mask = 0; mask < size; ++mask)
            {
                int weight = 0;
                for (int i = 0; i < n; ++i) if ((mask & (1 << i)) != 0) weight += weights[i];
                truth[mask] = weight >= threshold;
            }
        }
        else if (kind == 1)
        {
            int split = 2 + rng.Next(n - 3);
            var minimalPairs = new List<int[]>();
            int pairCount = 1 + rng.Next(4);
            for (int k = 0; k < pairCount; ++k)
            {
                int a = rng.Next(split + 1), b = rng.Next(n - split + 1);
                if (a == 0 && b == 0) { a = 1; }
                bool dominated = false;
                for (int i = 0; i < minimalPairs.Count; ++i)
                    if (minimalPairs[i][0] <= a && minimalPairs[i][1] <= b)
                    { dominated = true; break; }
                if (dominated) continue;
                for (int i = minimalPairs.Count - 1; i >= 0; --i)
                    if (a <= minimalPairs[i][0] && b <= minimalPairs[i][1])
                        minimalPairs.RemoveAt(i);
                minimalPairs.Add(new int[] { a, b });
            }
            for (int mask = 0; mask < size; ++mask)
            {
                int first = PopCount(mask & ((1 << split) - 1));
                int second = PopCount(mask >> split);
                for (int i = 0; i < minimalPairs.Count; ++i)
                    if (first >= minimalPairs[i][0] && second >= minimalPairs[i][1])
                    { truth[mask] = true; break; }
            }
        }
        else if (kind == 2)
        {
            int rest = n - 1;
            var weights = new int[rest];
            int total = 0;
            for (int i = 0; i < rest; ++i) { weights[i] = 1 + rng.Next(5); total += weights[i]; }
            int low = rng.Next(total + 1);
            int high = low + rng.Next(total - low + 1);
            for (int mask = 0; mask < size; ++mask)
            {
                int weight = 0;
                for (int i = 0; i < rest; ++i)
                    if ((mask & (1 << (i + 1))) != 0) weight += weights[i];
                truth[mask] = weight >= (((mask & 1) != 0) ? low : high);
            }
        }
        else
        {
            int a = Math.Max(1, n / 3);
            int b = Math.Max(1, (n - a) / 2);
            int c = n - a - b;
            var triples = new List<int[]>();
            int tripleCount = 1 + rng.Next(6);
            for (int k = 0; k < tripleCount; ++k)
            {
                int x = rng.Next(a + 1), y = rng.Next(b + 1), z = rng.Next(c + 1);
                if (x == 0 && y == 0 && z == 0) x = 1;
                bool dominated = false;
                for (int i = 0; i < triples.Count; ++i)
                    if (triples[i][0] <= x && triples[i][1] <= y && triples[i][2] <= z)
                    { dominated = true; break; }
                if (dominated) continue;
                for (int i = triples.Count - 1; i >= 0; --i)
                    if (x <= triples[i][0] && y <= triples[i][1] && z <= triples[i][2])
                        triples.RemoveAt(i);
                triples.Add(new int[] { x, y, z });
            }
            int maskA = (1 << a) - 1;
            int maskB = ((1 << b) - 1) << a;
            for (int mask = 0; mask < size; ++mask)
            {
                int x = PopCount(mask & maskA);
                int y = PopCount(mask & maskB);
                int z = PopCount(mask >> (a + b));
                for (int i = 0; i < triples.Count; ++i)
                    if (x >= triples[i][0] && y >= triples[i][1] && z >= triples[i][2])
                    { truth[mask] = true; break; }
            }
        }
        return TruthToTerms(n, truth);
    }

    private static int[] SelfDualWeightedAntichain(int n, Random rng)
    {
        var weights = new int[n];
        int total = 0;
        for (int i = 0; i < n; ++i) { weights[i] = 1 + rng.Next(11); total += weights[i]; }
        if ((total & 1) == 0) { ++weights[n - 1]; ++total; }
        var truth = new bool[1 << n];
        for (int mask = 0; mask < truth.Length; ++mask)
        {
            int weight = 0;
            for (int i = 0; i < n; ++i) if ((mask & (1 << i)) != 0) weight += weights[i];
            truth[mask] = 2 * weight > total;
        }
        return TruthToTerms(n, truth);
    }

    private static int RandomBoundarySearch(
        int maxN, int denominator, int trials, int seed, bool selfDualFocused,
        bool asymmetricProbabilities = false)
    {
        var rng = new Random(seed);
        long tested = 0;
        long fourWayFailures = 0;
        long editFailures = 0, editFailureMiddle = 0, editFailureSelfDual = 0;
        for (int n = 7; n <= maxN; ++n)
        {
            int used = 0;
            while (used < trials)
            {
                int safe, stolen, leaked, lost;
                if (selfDualFocused && !asymmetricProbabilities)
                {
                    leaked = lost = 1 + rng.Next(Math.Max(1, denominator / 8));
                    int slack = 1 + rng.Next(Math.Max(1, denominator / 20));
                    int remainder = denominator - 3 * leaked - slack;
                    if (remainder < 0 || (remainder & 1) != 0) continue;
                    stolen = remainder / 2;
                    safe = stolen + leaked + slack;
                }
                else
                {
                    safe = rng.Next(denominator + 1);
                    stolen = rng.Next(denominator - safe + 1);
                    leaked = rng.Next(denominator - safe - stolen + 1);
                    lost = denominator - safe - stolen - leaked;
                }
                if (!(safe > stolen + leaked && safe > stolen + lost)) continue;
                int[] terms = selfDualFocused
                    ? SelfDualWeightedAntichain(n, rng)
                    : (rng.Next(2) == 0 ? RandomAntichain(n, rng) : StructuredAntichain(n, rng));
                bool[] truth = BuildTruth(n, terms);
                int[] ranks = IncompleteRanks(n, truth);
                if (ranks.Length < 2 || (terms.Length == 1 && IsPowerOfTwo(terms[0]))) continue;
                int r = ranks[0], q = ranks[ranks.Length - 1];
                bool[] remove = EditTruth(n, truth, r, false);
                bool[] fill = EditTruth(n, truth, q, true);
                bool[] both = EditTruth(n, remove, q, true);
                long baseScore = TensorScore(n, truth, safe, stolen, leaked, lost);
                long g0 = TensorScore(n, remove, safe, stolen, leaked, lost) - baseScore;
                long g1 = TensorScore(n, fill, safe, stolen, leaked, lost) - baseScore;
                long g2 = TensorScore(n, both, safe, stolen, leaked, lost) - baseScore;
                if (r + q == n &&
                    (long)safe * stolen <= (long)leaked * lost &&
                    ((lost >= leaked && g1 < 0) ||
                     (leaked >= lost && g0 < 0)))
                {
                    Console.WriteLine(
                        "RANDOM REVERSE ORIENTED-EDIT FAILURE n=" + n +
                        " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                        ")/" + denominator + " wallet=" + TermsString(terms) +
                        " ranks=" + string.Join(",", ranks) +
                        " gains=(" + g0 + "," + g1 + "," + g2 + ")");
                    return 4;
                }
                ++used;
                ++tested;
                if (g0 < 0 && g1 < 0 && g2 < 0)
                {
                    ++editFailures;
                    if (r + q == n) ++editFailureMiddle;
                    bool selfDual = true;
                    int full = (1 << n) - 1;
                    for (int mask = 0; mask <= full; ++mask)
                        if (truth[mask] == truth[full ^ mask])
                        { selfDual = false; break; }
                    if (selfDual) ++editFailureSelfDual;
                    long dictator = (long)safe * Powers(denominator, n - 1)[n - 1];
                    if (editFailures <= 5)
                        Console.WriteLine(
                            "RANDOM EDIT FAILURE n=" + n + " p=(" + safe + "," + stolen + "," +
                            leaked + "," + lost + ")/" + denominator +
                            " wallet=" + TermsString(terms) +
                            " ranks=" + string.Join(",", ranks) +
                            " selfdual=" + selfDual +
                            " score-minus-dictator=" + (baseScore - dictator) +
                            " gains=(" + g0 + "," + g1 + "," + g2 + ")");
                    if (baseScore > dictator)
                    {
                        ++fourWayFailures;
                        Console.WriteLine(
                            "RANDOM FOUR-WAY COUNTEREXAMPLE n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                            ")/" + denominator + " wallet=" + TermsString(terms) +
                            " ranks=" + string.Join(",", ranks) + " score-minus-dictator=" +
                            (baseScore - dictator) + " gains=(" + g0 + "," + g1 + "," + g2 + ")");
                        return 2;
                    }
                }
            }
            Console.WriteLine("random n=" + n + " exact boundary-edit trials=" + used + " failures=0");
        }
        Console.WriteLine("random exact boundary-edit total=" + tested +
            " edit-failures=" + editFailures +
            " edit-failure-rplusq=n=" + editFailureMiddle +
            " edit-failure-self-dual=" + editFailureSelfDual +
            " four-way-failures=" + fourWayFailures + " seed=" + seed);
        return 0;
    }

    private static List<WalletData> Prepare(int n, bool includeGains)
    {
        string path = Path.Combine("src", "helpers", "data", "wallet_cache", "wallets_" + n + ".json");
        List<int[]> raw = ReadWallets(path);
        int[] stateCodes = StateCodes(n);
        int b = n + 1;
        int denseLength = b * b * b * b;
        var data = new List<WalletData>(raw.Count);
        foreach (int[] terms in raw)
        {
            bool[] truth = BuildTruth(n, terms);
            int[] ranks = IncompleteRanks(n, truth);
            var item = new WalletData();
            item.Terms = terms;
            item.Truth = truth;
            item.IncompleteRanks = ranks;
            item.IncompleteCount = ranks.Length;
            item.IsDictator = terms.Length == 1 && IsPowerOfTwo(terms[0]);
            item.Score = ScorePoly(n, truth, stateCodes);
            if (includeGains && ranks.Length >= 2 && !item.IsDictator)
            {
                int r = ranks[0], q = ranks[ranks.Length - 1];
                bool[] remove = EditTruth(n, truth, r, false);
                bool[] fill = EditTruth(n, truth, q, true);
                bool[] both = EditTruth(n, remove, q, true);
                item.Gains = new SparsePoly[] {
                    Difference(ScorePoly(n, remove, stateCodes), item.Score, denseLength),
                    Difference(ScorePoly(n, fill, stateCodes), item.Score, denseLength),
                    Difference(ScorePoly(n, both, stateCodes), item.Score, denseLength)
                };
            }
            data.Add(item);
        }
        return data;
    }

    private static int ExactPointSearch(
        int maxN, int denominator, int safe, int stolen, int leaked, int lost)
    {
        bool failed = false;
        for (int n = 1; n <= maxN; ++n)
        {
            List<WalletData> wallets = Prepare(n, true);
            decimal[] weights = WeightsDecimal(n, safe, stolen, leaked, lost);
            decimal dictatorScore = safe * PowersDecimal(denominator, n - 1)[n - 1];
            decimal allBest = -1m, allowedBest = -1m;
            WalletData allWinner = null, allowedWinner = null;
            int fourWayFailures = 0;
            int editFailures = 0, editFailureMiddle = 0, editFailureSelfDual = 0;
            foreach (WalletData wallet in wallets)
            {
                decimal score = EvaluateDecimal(wallet.Score, weights);
                if (score > allBest) { allBest = score; allWinner = wallet; }
                if ((wallet.IncompleteCount <= 1 || wallet.IsDictator) && score > allowedBest)
                {
                    allowedBest = score; allowedWinner = wallet;
                }
                if (wallet.Gains != null &&
                    EvaluateDecimal(wallet.Gains[0], weights) < 0 &&
                    EvaluateDecimal(wallet.Gains[1], weights) < 0 &&
                    EvaluateDecimal(wallet.Gains[2], weights) < 0)
                {
                    ++editFailures;
                    int r = wallet.IncompleteRanks[0];
                    int q = wallet.IncompleteRanks[wallet.IncompleteRanks.Length - 1];
                    if (r + q == n) ++editFailureMiddle;
                    bool selfDual = true;
                    int full = (1 << n) - 1;
                    for (int mask = 0; mask <= full; ++mask)
                        if (wallet.Truth[mask] == wallet.Truth[full ^ mask])
                        { selfDual = false; break; }
                    if (selfDual) ++editFailureSelfDual;
                    if (score > dictatorScore) ++fourWayFailures;
                }
            }
            Console.WriteLine(
                "POINT n=" + n + " all=" + TermsString(allWinner.Terms) + " score=" +
                allBest + "/" + denominator + "^" + n + " allowed=" +
                TermsString(allowedWinner.Terms) + " score=" + allowedBest + "/" +
                denominator + "^" + n + " gap=" + (allBest - allowedBest) +
                " edit_failures=" + editFailures +
                " edit_failure_rplusq=n=" + editFailureMiddle +
                " edit_failure_self_dual=" + editFailureSelfDual +
                " four_way_failures=" + fourWayFailures);
            if (allBest > allowedBest) failed = true;
        }
        return failed ? 2 : 0;
    }

    private sealed class BlockFamily
    {
        public bool[] Truth;
        public int[] Ranks;
    }

    private static long Binomial(int n, int k)
    {
        if (k < 0 || k > n) return 0;
        long value = 1;
        for (int i = 1; i <= k; ++i) value = value * (n - k + i) / i;
        return value;
    }

    private static long Multinomial4(int n, int a, int b, int c, int d)
    {
        return Binomial(n, a) * Binomial(n - a, b) * Binomial(n - a - b, c);
    }

    private static long[] BlockMatrix(
        int m, int safe, int stolen, int leaked, int lost)
    {
        int z = m + 1;
        var matrix = new long[z * z];
        long[] ps = Powers(safe, m), pt = Powers(stolen, m);
        long[] pe = Powers(leaked, m), pl = Powers(lost, m);
        for (int sc = 0; sc <= m; ++sc)
            for (int tc = 0; tc <= m - sc; ++tc)
                for (int ec = 0; ec <= m - sc - tc; ++ec)
                {
                    int lc = m - sc - tc - ec;
                    int owner = sc + ec, attacker = tc + ec;
                    matrix[owner * z + attacker] +=
                        Multinomial4(m, sc, tc, ec, lc) *
                        ps[sc] * pt[tc] * pe[ec] * pl[lc];
                }
        return matrix;
    }

    private static long BlockScore(
        int a, int b, bool[] truth, long[] ma, long[] mb)
    {
        int za = a + 1, zb = b + 1;
        var stage = new long[za * zb];
        // Apply the B-block matrix to the attacker-B coordinate.
        for (int attackerA = 0; attackerA < za; ++attackerA)
            for (int ownerB = 0; ownerB < zb; ++ownerB)
            {
                long sum = 0;
                for (int attackerB = 0; attackerB < zb; ++attackerB)
                    if (!truth[attackerA * zb + attackerB])
                        sum += mb[ownerB * zb + attackerB];
                stage[attackerA * zb + ownerB] = sum;
            }
        long score = 0;
        for (int ownerA = 0; ownerA < za; ++ownerA)
            for (int ownerB = 0; ownerB < zb; ++ownerB)
            {
                if (!truth[ownerA * zb + ownerB]) continue;
                long sum = 0;
                for (int attackerA = 0; attackerA < za; ++attackerA)
                    sum += ma[ownerA * za + attackerA] * stage[attackerA * zb + ownerB];
                score += sum;
            }
        return score;
    }

    private static void GenerateThresholdsRec(
        int a, int b, int index, int maximum, int[] thresholds, List<BlockFamily> output)
    {
        if (index == a + 1)
        {
            int zb = b + 1;
            var truth = new bool[(a + 1) * zb];
            for (int i = 0; i <= a; ++i)
                for (int j = 0; j <= b; ++j)
                    truth[i * zb + j] = j >= thresholds[i];
            var ranks = new List<int>();
            for (int rank = 0; rank <= a + b; ++rank)
            {
                long total = Binomial(a + b, rank), covered = 0;
                for (int i = 0; i <= a; ++i)
                {
                    int j = rank - i;
                    if (j >= 0 && j <= b && truth[i * zb + j])
                        covered += Binomial(a, i) * Binomial(b, j);
                }
                if (covered > 0 && covered < total) ranks.Add(rank);
            }
            output.Add(new BlockFamily { Truth = truth, Ranks = ranks.ToArray() });
            return;
        }
        // q_i is nonincreasing in i; b+1 denotes an empty row.
        for (int q = maximum; q >= 0; --q)
        {
            thresholds[index] = q;
            GenerateThresholdsRec(a, b, index + 1, q, thresholds, output);
        }
    }

    private static List<BlockFamily> GenerateBlockFamilies(int a, int b)
    {
        var output = new List<BlockFamily>();
        GenerateThresholdsRec(a, b, 0, b + 1, new int[a + 1], output);
        return output;
    }

    private static int ExhaustiveBlockSearch(int maxN, int denominator, bool singletonFirstBlock)
    {
        bool found = false;
        for (int n = 7; n <= maxN; ++n)
        {
            int a = singletonFirstBlock ? 1 : n / 2, b = n - a, zb = b + 1;
            List<BlockFamily> families = GenerateBlockFamilies(a, b);
            long scenarios = 0, fourWayFailures = 0, classGlobalFailures = 0;
            for (int safe = 0; safe <= denominator; ++safe)
                for (int stolen = 0; stolen <= denominator - safe; ++stolen)
                    for (int leaked = 0; leaked <= denominator - safe - stolen; ++leaked)
                    {
                        int lost = denominator - safe - stolen - leaked;
                        if (!(safe > stolen + leaked && safe > stolen + lost)) continue;
                        ++scenarios;
                        long[] ma = BlockMatrix(a, safe, stolen, leaked, lost);
                        long[] mb = BlockMatrix(b, safe, stolen, leaked, lost);
                        long dictator = (long)safe * Powers(denominator, n - 1)[n - 1];
                        long best = -1, allowed = dictator;
                        BlockFamily winner = null;
                        foreach (BlockFamily family in families)
                        {
                            long baseScore = BlockScore(a, b, family.Truth, ma, mb);
                            if (baseScore > best) { best = baseScore; winner = family; }
                            if (family.Ranks.Length <= 1 && baseScore > allowed) allowed = baseScore;
                            if (family.Ranks.Length < 2) continue;
                            int r = family.Ranks[0], q = family.Ranks[family.Ranks.Length - 1];
                            bool[] remove = (bool[])family.Truth.Clone();
                            bool[] fill = (bool[])family.Truth.Clone();
                            bool[] both = (bool[])family.Truth.Clone();
                            for (int i = 0; i <= a; ++i)
                                for (int j = 0; j <= b; ++j)
                                {
                                    int ix = i * zb + j;
                                    if (i + j == r) { remove[ix] = false; both[ix] = false; }
                                    if (i + j == q) { fill[ix] = true; both[ix] = true; }
                                }
                            long g0 = BlockScore(a, b, remove, ma, mb) - baseScore;
                            long g1 = BlockScore(a, b, fill, ma, mb) - baseScore;
                            long g2 = BlockScore(a, b, both, ma, mb) - baseScore;
                            if (g0 < 0 && g1 < 0 && g2 < 0 && baseScore > dictator)
                            {
                                ++fourWayFailures;
                                found = true;
                                if (fourWayFailures <= 5)
                                    Console.WriteLine(
                                        "BLOCK FOUR-WAY FAILURE n=" + n + " split=" + a + "+" + b +
                                        " p=(" + safe + "," + stolen + "," + leaked + "," + lost + ")/" +
                                        denominator + " ranks=" + string.Join(",", family.Ranks) +
                                        " score-dictator=" + (baseScore - dictator) +
                                        " gains=(" + g0 + "," + g1 + "," + g2 + ")");
                            }
                        }
                        if (best > allowed)
                        {
                            ++classGlobalFailures;
                            found = true;
                            if (classGlobalFailures <= 5)
                                Console.WriteLine(
                                    "BLOCK-CLASS GLOBAL FAILURE n=" + n + " split=" + a + "+" + b +
                                    " p=(" + safe + "," + stolen + "," + leaked + "," + lost + ")/" +
                                    denominator + " ranks=" + string.Join(",", winner.Ranks) +
                                    " gap=" + (best - allowed));
                        }
                    }
            Console.WriteLine(
                "blocks n=" + n + " split=" + a + "+" + b + " families=" + families.Count +
                " scenarios=" + scenarios + " four-way-failures=" + fourWayFailures +
                " within-class-global-failures=" + classGlobalFailures);
        }
        return found ? 2 : 0;
    }

    private static long Block3Score(
        int a, int b, int c, bool[] truth, long[] ma, long[] mb, long[] mc)
    {
        int za = a + 1, zb = b + 1, zc = c + 1;
        var stageC = new long[za * zb * zc];
        for (int aa = 0; aa < za; ++aa)
            for (int ab = 0; ab < zb; ++ab)
                for (int oc = 0; oc < zc; ++oc)
                {
                    long sum = 0;
                    for (int ac = 0; ac < zc; ++ac)
                        if (!truth[(aa * zb + ab) * zc + ac])
                            sum += mc[oc * zc + ac];
                    stageC[(aa * zb + ab) * zc + oc] = sum;
                }
        var stageB = new long[za * zb * zc];
        for (int aa = 0; aa < za; ++aa)
            for (int ob = 0; ob < zb; ++ob)
                for (int oc = 0; oc < zc; ++oc)
                {
                    long sum = 0;
                    for (int ab = 0; ab < zb; ++ab)
                        sum += mb[ob * zb + ab] * stageC[(aa * zb + ab) * zc + oc];
                    stageB[(aa * zb + ob) * zc + oc] = sum;
                }
        long score = 0;
        for (int oa = 0; oa < za; ++oa)
            for (int ob = 0; ob < zb; ++ob)
                for (int oc = 0; oc < zc; ++oc)
                {
                    if (!truth[(oa * zb + ob) * zc + oc]) continue;
                    long sum = 0;
                    for (int aa = 0; aa < za; ++aa)
                        sum += ma[oa * za + aa] * stageB[(aa * zb + ob) * zc + oc];
                    score += sum;
                }
        return score;
    }

    private static void Generate3ThresholdsRec(
        int a, int b, int c, int position, int[] thresholds, List<BlockFamily> output)
    {
        int za = a + 1, zb = b + 1, zc = c + 1;
        if (position == za * zb)
        {
            var truth = new bool[za * zb * zc];
            for (int i = 0; i < za; ++i)
                for (int j = 0; j < zb; ++j)
                    for (int k = 0; k < zc; ++k)
                        truth[(i * zb + j) * zc + k] = k >= thresholds[i * zb + j];
            var ranks = new List<int>();
            for (int rank = 0; rank <= a + b + c; ++rank)
            {
                long total = Binomial(a + b + c, rank), covered = 0;
                for (int i = 0; i < za; ++i)
                    for (int j = 0; j < zb; ++j)
                    {
                        int k = rank - i - j;
                        if (k >= 0 && k < zc && truth[(i * zb + j) * zc + k])
                            covered += Binomial(a, i) * Binomial(b, j) * Binomial(c, k);
                    }
                if (covered > 0 && covered < total) ranks.Add(rank);
            }
            output.Add(new BlockFamily { Truth = truth, Ranks = ranks.ToArray() });
            return;
        }
        int row = position / zb, col = position % zb;
        int maximum = c + 1;
        if (row > 0) maximum = Math.Min(maximum, thresholds[(row - 1) * zb + col]);
        if (col > 0) maximum = Math.Min(maximum, thresholds[row * zb + col - 1]);
        for (int q = maximum; q >= 0; --q)
        {
            thresholds[position] = q;
            Generate3ThresholdsRec(a, b, c, position + 1, thresholds, output);
        }
    }

    private static int ExhaustiveBlock3Search(int maxN, int denominator)
    {
        bool found = false;
        for (int n = 7; n <= maxN; ++n)
        {
            int a = n / 3, b = (n - a) / 2, c = n - a - b;
            int zb = b + 1, zc = c + 1;
            var families = new List<BlockFamily>();
            Generate3ThresholdsRec(a, b, c, 0, new int[(a + 1) * (b + 1)], families);
            long scenarios = 0, fourWayFailures = 0, classGlobalFailures = 0;
            for (int safe = 0; safe <= denominator; ++safe)
                for (int stolen = 0; stolen <= denominator - safe; ++stolen)
                    for (int leaked = 0; leaked <= denominator - safe - stolen; ++leaked)
                    {
                        int lost = denominator - safe - stolen - leaked;
                        if (!(safe > stolen + leaked && safe > stolen + lost)) continue;
                        ++scenarios;
                        long[] ma = BlockMatrix(a, safe, stolen, leaked, lost);
                        long[] mb = BlockMatrix(b, safe, stolen, leaked, lost);
                        long[] mc = BlockMatrix(c, safe, stolen, leaked, lost);
                        long dictator = (long)safe * Powers(denominator, n - 1)[n - 1];
                        long best = -1, allowed = dictator;
                        BlockFamily winner = null;
                        foreach (BlockFamily family in families)
                        {
                            long baseScore = Block3Score(a, b, c, family.Truth, ma, mb, mc);
                            if (baseScore > best) { best = baseScore; winner = family; }
                            if (family.Ranks.Length <= 1 && baseScore > allowed) allowed = baseScore;
                            if (family.Ranks.Length < 2) continue;
                            int r = family.Ranks[0], q = family.Ranks[family.Ranks.Length - 1];
                            bool[] remove = (bool[])family.Truth.Clone();
                            bool[] fill = (bool[])family.Truth.Clone();
                            bool[] both = (bool[])family.Truth.Clone();
                            for (int i = 0; i <= a; ++i)
                                for (int j = 0; j <= b; ++j)
                                    for (int k = 0; k <= c; ++k)
                                    {
                                        int ix = (i * zb + j) * zc + k;
                                        if (i + j + k == r) { remove[ix] = false; both[ix] = false; }
                                        if (i + j + k == q) { fill[ix] = true; both[ix] = true; }
                                    }
                            long g0 = Block3Score(a, b, c, remove, ma, mb, mc) - baseScore;
                            long g1 = Block3Score(a, b, c, fill, ma, mb, mc) - baseScore;
                            long g2 = Block3Score(a, b, c, both, ma, mb, mc) - baseScore;
                            if (g0 < 0 && g1 < 0 && g2 < 0 && baseScore > dictator)
                            { ++fourWayFailures; found = true; }
                        }
                        if (best > allowed)
                        {
                            ++classGlobalFailures; found = true;
                            if (classGlobalFailures <= 3)
                                Console.WriteLine(
                                    "BLOCK3-CLASS GLOBAL FAILURE n=" + n + " p=(" + safe + "," +
                                    stolen + "," + leaked + "," + lost + ")/" + denominator +
                                    " ranks=" + string.Join(",", winner.Ranks) + " gap=" + (best - allowed));
                        }
                    }
            Console.WriteLine(
                "blocks3 n=" + n + " split=" + a + "+" + b + "+" + c +
                " families=" + families.Count + " scenarios=" + scenarios +
                " four-way-failures=" + fourWayFailures +
                " within-class-global-failures=" + classGlobalFailures);
        }
        return found ? 2 : 0;
    }

    public static int Main(string[] args)
    {
        int maxN = args.Length > 0 ? int.Parse(args[0]) : 6;
        int denominator = args.Length > 1 ? int.Parse(args[1]) : 30;
        string region = args.Length > 2 ? args[2].ToLowerInvariant() : "pairwise";
        if (region == "blocks" || region == "blocks1")
            return ExhaustiveBlockSearch(maxN, denominator, region == "blocks1");
        if (region == "blocks3")
            return ExhaustiveBlock3Search(maxN, denominator);
        if (region == "point")
        {
            if (args.Length < 7) throw new ArgumentException("point requires s,t,e,l numerators");
            return ExactPointSearch(
                maxN, denominator, int.Parse(args[3]), int.Parse(args[4]),
                int.Parse(args[5]), int.Parse(args[6]));
        }
        if (region == "random" || region == "selfdualrandom" ||
            region == "selfdualasym")
        {
            int trials = args.Length > 3 ? int.Parse(args[3]) : 10000;
            int seed = args.Length > 4 ? int.Parse(args[4]) : 1729;
            return RandomBoundarySearch(
                maxN, denominator, trials, seed,
                region == "selfdualrandom" || region == "selfdualasym",
                region == "selfdualasym");
        }
        int coefficientNumerator = 0, coefficientDenominator = 1;
        if (region == "coef" || region == "maxcoef" ||
            region == "band_e0" || region == "band_e0_range")
        {
            coefficientNumerator = args.Length > 3 ? int.Parse(args[3]) : 1;
            coefficientDenominator = args.Length > 4 ? int.Parse(args[4]) : 2;
        }
        int upperCoefficientNumerator = 0, upperCoefficientDenominator = 1;
        if (region == "band_e0_range")
        {
            upperCoefficientNumerator = args.Length > 5 ? int.Parse(args[5]) : 11;
            upperCoefficientDenominator = args.Length > 6 ? int.Parse(args[6]) : 20;
        }
        bool globalViolation = false;
        int printedGlobalFailures = 0;
        int printedFourWayFailures = 0;
        int bestFailurePairMargin = int.MinValue;
        string bestFailurePairMarginExample = "";
        int maxFourWayRatioNum = -1, maxFourWayRatioDen = 1;
        string maxFourWayRatioExample = "";
        int maxGlobalRatioNum = -1, maxGlobalRatioDen = 1;
        string maxGlobalRatioExample = "";
        int maxGlobalMaxRatioNum = -1, maxGlobalMaxRatioDen = 1;
        string maxGlobalMaxRatioExample = "";
        long scenarioCount = 0;
        double highestBadEditSafe = -1;
        string highestBadEdit = "";
        long editFailurePairsNonpositiveDeterminant = 0;
        string firstEditFailureNonpositiveDeterminant = "";
        long negativeJointPairsNonpositiveDeterminant = 0;
        string firstNegativeJointNonpositiveDeterminant = "";
        long bothSingleLossPairsNonpositiveDeterminant = 0;
        string firstBothSingleLossNonpositiveDeterminant = "";
        long weightedSingleCertificateFailures = 0;
        string firstWeightedSingleCertificateFailure = "";
        long leakLostWeightedCertificateFailures = 0;
        string firstLeakLostWeightedCertificateFailure = "";
        long orientedReverseEditFailures = 0;
        string firstOrientedReverseEditFailure = "";

        for (int n = 1; n <= maxN; ++n)
        {
            List<WalletData> wallets = Prepare(n, true);
            long localScenarios = 0;
            long globalFailures = 0;
            long editFailureScenarios = 0;
            long fourWayFailurePairs = 0;
            long fourWayFailureScenarios = 0;
            for (int safe = 0; safe <= denominator; ++safe)
                for (int stolen = 0; stolen <= denominator - safe; ++stolen)
                    for (int leaked = 0; leaked <= denominator - safe - stolen; ++leaked)
                    {
                        int lost = denominator - safe - stolen - leaked;
                        bool selected =
                            region == "all" ||
                            (region == "st" && safe > stolen) ||
                            (region == "avg" && 2 * (safe - stolen) > leaked + lost) ||
                            (region == "coef" &&
                             coefficientDenominator * (safe - stolen) >
                             coefficientNumerator * (leaked + lost)) ||
                            (region == "maxcoef" &&
                             coefficientDenominator * (safe - stolen) >
                             coefficientNumerator * Math.Max(leaked, lost)) ||
                            (region == "band_e0" && leaked == 0 &&
                             coefficientDenominator * (safe - stolen) >
                             coefficientNumerator * lost &&
                             2 * (safe - stolen) <= lost) ||
                            (region == "band_e0_range" && leaked == 0 &&
                             coefficientDenominator * (safe - stolen) >
                             coefficientNumerator * lost &&
                             upperCoefficientDenominator * (safe - stolen) <=
                             upperCoefficientNumerator * lost) ||
                            (region == "se" && safe > stolen + leaked) ||
                            (region == "sl" && safe > stolen + lost) ||
                            (region == "pairweak" && safe >= stolen + leaked && safe >= stolen + lost) ||
                            (region == "pairwise" && safe > stolen + leaked && safe > stolen + lost);
                        if (!selected) continue;
                        ++localScenarios;
                        ++scenarioCount;
                        long[] weights = Weights(n, safe, stolen, leaked, lost);
                        long allBest = -1, allowedBest = -1;
                        WalletData allWinner = null, allowedWinner = null;
                        bool editFailureHere = false;
                        bool fourWayFailureHere = false;
                        long dictatorScore = (long)safe * Powers(denominator, n - 1)[n - 1];
                        foreach (WalletData wallet in wallets)
                        {
                            long score = Evaluate(wallet.Score, weights);
                            if (score > allBest) { allBest = score; allWinner = wallet; }
                            if ((wallet.IncompleteCount <= 1 || wallet.IsDictator) && score > allowedBest)
                            {
                                allowedBest = score;
                                allowedWinner = wallet;
                            }
                            if (wallet.Gains != null)
                            {
                                long g0 = Evaluate(wallet.Gains[0], weights);
                                long g1 = Evaluate(wallet.Gains[1], weights);
                                long g2 = Evaluate(wallet.Gains[2], weights);
                                if (g2 < 0 &&
                                    wallet.IncompleteRanks[0] +
                                        wallet.IncompleteRanks[wallet.IncompleteRanks.Length - 1] == n &&
                                    (long)safe * stolen <= (long)leaked * lost)
                                {
                                    ++negativeJointPairsNonpositiveDeterminant;
                                    if (firstNegativeJointNonpositiveDeterminant.Length == 0)
                                        firstNegativeJointNonpositiveDeterminant =
                                            "n=" + n + " p=(" + safe + "," + stolen + "," +
                                            leaked + "," + lost + ")/" + denominator +
                                            " wallet=" + TermsString(wallet.Terms) +
                                            " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                            " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                }
                                if (g0 < 0 && g1 < 0 &&
                                    wallet.IncompleteRanks[0] +
                                        wallet.IncompleteRanks[wallet.IncompleteRanks.Length - 1] == n &&
                                    (long)safe * stolen <= (long)leaked * lost)
                                {
                                    ++bothSingleLossPairsNonpositiveDeterminant;
                                    if (firstBothSingleLossNonpositiveDeterminant.Length == 0)
                                        firstBothSingleLossNonpositiveDeterminant =
                                            "n=" + n + " p=(" + safe + "," + stolen + "," +
                                            leaked + "," + lost + ")/" + denominator +
                                            " wallet=" + TermsString(wallet.Terms) +
                                            " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                            " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                }
                                if (wallet.IncompleteRanks[0] +
                                        wallet.IncompleteRanks[wallet.IncompleteRanks.Length - 1] == n &&
                                    (long)safe * stolen <= (long)leaked * lost &&
                                    (long)(safe - stolen - lost) * g0 +
                                        (long)(safe - stolen - leaked) * g1 < 0)
                                {
                                    ++weightedSingleCertificateFailures;
                                    if (firstWeightedSingleCertificateFailure.Length == 0)
                                        firstWeightedSingleCertificateFailure =
                                            "n=" + n + " p=(" + safe + "," + stolen + "," +
                                            leaked + "," + lost + ")/" + denominator +
                                            " wallet=" + TermsString(wallet.Terms) +
                                            " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                            " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                }
                                if (wallet.IncompleteRanks[0] +
                                        wallet.IncompleteRanks[wallet.IncompleteRanks.Length - 1] == n &&
                                    (long)safe * stolen <= (long)leaked * lost &&
                                    ((lost >= leaked && g1 < 0) ||
                                     (leaked >= lost && g0 < 0)))
                                {
                                    ++orientedReverseEditFailures;
                                    if (firstOrientedReverseEditFailure.Length == 0)
                                        firstOrientedReverseEditFailure =
                                            "n=" + n + " p=(" + safe + "," + stolen + "," +
                                            leaked + "," + lost + ")/" + denominator +
                                            " wallet=" + TermsString(wallet.Terms) +
                                            " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                            " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                }
                                if (wallet.IncompleteRanks[0] +
                                        wallet.IncompleteRanks[wallet.IncompleteRanks.Length - 1] == n &&
                                    (long)safe * stolen <= (long)leaked * lost &&
                                    (long)leaked * g0 + (long)lost * g1 < 0)
                                {
                                    ++leakLostWeightedCertificateFailures;
                                    if (firstLeakLostWeightedCertificateFailure.Length == 0)
                                        firstLeakLostWeightedCertificateFailure =
                                            "n=" + n + " p=(" + safe + "," + stolen + "," +
                                            leaked + "," + lost + ")/" + denominator +
                                            " wallet=" + TermsString(wallet.Terms) +
                                            " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                            " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                }
                                if (g0 < 0 && g1 < 0 && g2 < 0)
                                {
                                    if ((long)safe * stolen <= (long)leaked * lost)
                                    {
                                        ++editFailurePairsNonpositiveDeterminant;
                                        if (firstEditFailureNonpositiveDeterminant.Length == 0)
                                            firstEditFailureNonpositiveDeterminant =
                                                "n=" + n + " p=(" + safe + "," + stolen + "," +
                                                leaked + "," + lost + ")/" + denominator +
                                                " wallet=" + TermsString(wallet.Terms) +
                                                " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                                " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                    }
                                    editFailureHere = true;
                                    if (score > dictatorScore)
                                    {
                                        ++fourWayFailurePairs;
                                        fourWayFailureHere = true;
                                        int ratioNum = safe - stolen, ratioDen = leaked + lost;
                                        if (ratioDen > 0 &&
                                            (maxFourWayRatioNum < 0 ||
                                             (long)ratioNum * maxFourWayRatioDen >
                                             (long)maxFourWayRatioNum * ratioDen))
                                        {
                                            maxFourWayRatioNum = ratioNum;
                                            maxFourWayRatioDen = ratioDen;
                                            maxFourWayRatioExample =
                                                "ratio=" + ratioNum + "/" + ratioDen +
                                                " n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                                                ")/" + denominator + " wallet=" + TermsString(wallet.Terms) +
                                                " score-minus-dictator=" + (score - dictatorScore) + "/" +
                                                denominator + "^" + n +
                                                " gains=(" + g0 + "," + g1 + "," + g2 + ")";
                                        }
                                        if (printedFourWayFailures < 20)
                                        {
                                            ++printedFourWayFailures;
                                            Console.WriteLine(
                                                "FOUR-WAY COUNTEREXAMPLE n=" + n + " p=(" +
                                                safe + "," + stolen + "," + leaked + "," + lost + ")/" + denominator +
                                                " wallet=" + TermsString(wallet.Terms) +
                                                " score-minus-dictator=" + (score - dictatorScore) +
                                                " gains=(" + g0 + "," + g1 + "," + g2 + ")/" +
                                                denominator + "^" + n);
                                        }
                                    }
                                    double safeValue = (double)safe / denominator;
                                    if (safeValue > highestBadEditSafe)
                                    {
                                        highestBadEditSafe = safeValue;
                                        highestBadEdit =
                                            "n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                                            ")/" + denominator + " wallet=" + TermsString(wallet.Terms) +
                                            " ranks=" + string.Join(",", wallet.IncompleteRanks) +
                                            " gains=(" + g0 + "," + g1 + "," + g2 + ")/" +
                                            denominator + "^" + n;
                                    }
                                }
                            }
                        }
                        if (editFailureHere) ++editFailureScenarios;
                        if (fourWayFailureHere) ++fourWayFailureScenarios;
                        if (allBest > allowedBest)
                        {
                            ++globalFailures;
                            globalViolation = true;
                            int pairMargin = Math.Min(safe - stolen - leaked, safe - stolen - lost);
                            int ratioNum = safe - stolen, ratioDen = leaked + lost;
                            int maxRatioDen = Math.Max(leaked, lost);
                            if (maxRatioDen > 0 &&
                                (maxGlobalMaxRatioNum < 0 ||
                                 (long)ratioNum * maxGlobalMaxRatioDen >
                                 (long)maxGlobalMaxRatioNum * maxRatioDen))
                            {
                                maxGlobalMaxRatioNum = ratioNum;
                                maxGlobalMaxRatioDen = maxRatioDen;
                                maxGlobalMaxRatioExample =
                                    "ratio=" + ratioNum + "/" + maxRatioDen +
                                    " n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                                    ")/" + denominator + " winner=" + TermsString(allWinner.Terms);
                            }
                            if (ratioDen > 0 &&
                                (maxGlobalRatioNum < 0 ||
                                 (long)ratioNum * maxGlobalRatioDen > (long)maxGlobalRatioNum * ratioDen))
                            {
                                maxGlobalRatioNum = ratioNum;
                                maxGlobalRatioDen = ratioDen;
                                maxGlobalRatioExample =
                                    "ratio=" + ratioNum + "/" + ratioDen +
                                    " n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                                    ")/" + denominator + " winner=" + TermsString(allWinner.Terms);
                            }
                            if (pairMargin > bestFailurePairMargin)
                            {
                                bestFailurePairMargin = pairMargin;
                                bestFailurePairMarginExample =
                                    "margin=" + pairMargin + "/" + denominator +
                                    " n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                                    ")/" + denominator + " winner=" + TermsString(allWinner.Terms);
                            }
                            if (printedGlobalFailures < 20)
                            {
                                ++printedGlobalFailures;
                                Console.WriteLine(
                                    "GLOBAL COUNTEREXAMPLE n=" + n + " p=(" + safe + "," + stolen + "," + leaked + "," + lost +
                                    ")/" + denominator + " winner=" + TermsString(allWinner.Terms) +
                                    " score=" + allBest + "/" + denominator + "^" + n +
                                    " allowed=" + TermsString(allowedWinner.Terms) +
                                    " score=" + allowedBest + "/" + denominator + "^" + n);
                            }
                        }
                    }
            Console.WriteLine(
                "n=" + n + " wallets=" + wallets.Count + " scenarios=" + localScenarios +
                " revised_global_failures=" + globalFailures +
                " scenarios_with_non_dictator_edit_failure=" + editFailureScenarios +
                " four_way_failure_pairs=" + fourWayFailurePairs +
                " four_way_failure_scenarios=" + fourWayFailureScenarios);
        }
        Console.WriteLine("TOTAL scenarios_by_n=" + scenarioCount);
        Console.WriteLine("highest-safe non-dictator edit failure: " +
            (highestBadEditSafe < 0 ? "none" : highestBadEdit));
        Console.WriteLine("edit-failure pairs with st<=el: " +
            editFailurePairsNonpositiveDeterminant +
            (firstEditFailureNonpositiveDeterminant.Length == 0
                ? ""
                : " first=" + firstEditFailureNonpositiveDeterminant));
        Console.WriteLine("negative-joint pairs with st<=el: " +
            negativeJointPairsNonpositiveDeterminant +
            (firstNegativeJointNonpositiveDeterminant.Length == 0
                ? ""
                : " first=" + firstNegativeJointNonpositiveDeterminant));
        Console.WriteLine("both-single-loss pairs with st<=el: " +
            bothSingleLossPairsNonpositiveDeterminant +
            (firstBothSingleLossNonpositiveDeterminant.Length == 0
                ? ""
                : " first=" + firstBothSingleLossNonpositiveDeterminant));
        Console.WriteLine("weighted-single certificate failures: " +
            weightedSingleCertificateFailures +
            (firstWeightedSingleCertificateFailure.Length == 0
                ? ""
                : " first=" + firstWeightedSingleCertificateFailure));
        Console.WriteLine("e/l-weighted certificate failures: " +
            leakLostWeightedCertificateFailures +
            (firstLeakLostWeightedCertificateFailure.Length == 0
                ? ""
                : " first=" + firstLeakLostWeightedCertificateFailure));
        Console.WriteLine("oriented reverse-edit failures: " +
            orientedReverseEditFailures +
            (firstOrientedReverseEditFailure.Length == 0
                ? ""
                : " first=" + firstOrientedReverseEditFailure));
        Console.WriteLine("closest global failure to pairwise region: " +
            (bestFailurePairMargin == int.MinValue ? "none" : bestFailurePairMarginExample));
        Console.WriteLine("maximum four-way failure ratio (s-t)/(e+l): " +
            (maxFourWayRatioNum < 0 ? "none" : maxFourWayRatioExample));
        Console.WriteLine("maximum global failure ratio (s-t)/(e+l): " +
            (maxGlobalRatioNum < 0 ? "none" : maxGlobalRatioExample));
        Console.WriteLine("maximum global failure ratio (s-t)/max(e,l): " +
            (maxGlobalMaxRatioNum < 0 ? "none" : maxGlobalMaxRatioExample));
        return globalViolation ? 2 : 0;
    }
}
