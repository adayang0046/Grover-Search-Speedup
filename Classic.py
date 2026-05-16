def index_to_bitstring(index, n):
    return format(index, f"0{n}b")


def classical_search(n, target):
    N = 2 ** n

    for i in range(N):
        candidate = index_to_bitstring(i, n)

        if candidate == target:
            return candidate, i + 1

    return None, N