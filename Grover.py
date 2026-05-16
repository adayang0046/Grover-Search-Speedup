import math
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler


def get_recommended_iterations(n, number_of_solutions=1):

    N = 2 ** n
    M = number_of_solutions

    theta = math.asin(math.sqrt(M / N))
    iterations = round((math.pi / (4 * theta)) - 0.5)

    return max(1, iterations)


def apply_phase_flip_all_ones(qc, n):

    if n == 1:
        qc.z(0)
    else:
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)


def apply_oracle(qc, qiskit_target):

    n = len(qiskit_target)

    # Convert the target state into |111...1>
    for i, bit in enumerate(qiskit_target):
        if bit == "0":
            qc.x(i)

    apply_phase_flip_all_ones(qc, n)

    # Undo X gates
    for i, bit in enumerate(qiskit_target):
        if bit == "0":
            qc.x(i)


def apply_diffusion(qc, n):

    qubits = list(range(n))

    qc.h(qubits)
    qc.x(qubits)

    apply_phase_flip_all_ones(qc, n)

    qc.x(qubits)
    qc.h(qubits)


def build_grover_circuit(n, user_target, iterations):

    qiskit_target = user_target[::-1]

    qc = QuantumCircuit(n)

    # Create equal superposition
    qc.h(range(n))

    # Apply Grover iterations
    for _ in range(iterations):
        apply_oracle(qc, qiskit_target)
        apply_diffusion(qc, n)

    # Measure
    qc.measure_all()

    return qc


def run_grover_search(n, target, shots=1000):

    iterations = get_recommended_iterations(n)

    qc = build_grover_circuit(n, target, iterations)

    sampler = StatevectorSampler()
    job = sampler.run([qc], shots=shots)
    result = job.result()

    counts = result[0].data.meas.get_counts()

    target_count = counts.get(target, 0)
    success_rate = target_count / shots

    return {
        "iterations": iterations,
        "counts": counts,
        "target_count": target_count,
        "success_rate": success_rate,
        "circuit": qc,
    }