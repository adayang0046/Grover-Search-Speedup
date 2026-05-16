import csv
import math
import os
import random
from datetime import datetime

from Classic import classical_search, index_to_bitstring
from Grover import run_grover_search


RESULT_FILE = "grover_search_results.csv"


def generate_random_target(n):
    
    #Generate a random n bit target state.
    
    N = 2 ** n
    random_index = random.randint(0, N - 1)
    return index_to_bitstring(random_index, n)


def get_next_global_run_number():
    
    #Get the next global run number based on the existing CSV file.
    
    if not os.path.exists(RESULT_FILE):
        return 1

    with open(RESULT_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        return 1

    last_run_number = max(int(row["global_run_number"]) for row in rows)
    return last_run_number + 1


def save_result(row):
    
    #Save one experiment result to CSV.
    
    file_exists = os.path.exists(RESULT_FILE)

    fieldnames = [
        "timestamp",
        "global_run_number",
        "batch_run_number",
        "n",
        "N",
        "sqrt_N",
        "target",
        "classical_checks",
        "grover_oracle_calls",
        "speedup",
    ]

    with open(RESULT_FILE, "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def load_results():
    
    #Load all saved experiment results from CSV.
    
    if not os.path.exists(RESULT_FILE):
        return []

    with open(RESULT_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def calculate_average_speedup(rows):
    
    #Calculate average speedup from a list of rows.
    
    if not rows:
        return None

    total_runs = len(rows)
    avg_speedup = sum(float(row["speedup"]) for row in rows) / total_runs

    return {
        "total_runs": total_runs,
        "avg_speedup": avg_speedup,
    }


def filter_rows_by_n(rows, n):
    
    # Keep only rows with the same number of qubits.
    
    return [row for row in rows if int(row["n"]) == n]


def print_single_run_summary(row):
    
    #Print a short summary for each run.
    
    print(
        f"Run {row['batch_run_number']}: "
        f"target={row['target']}, "
        f"classical_checks={row['classical_checks']}, "
        f"grover_calls={row['grover_oracle_calls']}, "
        f"speedup={float(row['speedup']):.4f}x"
    )


def print_speedup_average(title, average):
    
    # Print average speedup only.
    
    if average is None:
        return

    print()
    print(title)
    print("-" * len(title))
    print(f"Total runs: {average['total_runs']}")
    print(f"Average speedup: {average['avg_speedup']:.4f}x")


def run_one_experiment(n, global_run_number, batch_run_number, shots=1000):
    
    # Run one classical-vs-Grover experiment.
    
    N = 2 ** n
    sqrt_N = math.sqrt(N)

    target = generate_random_target(n)

    # Classical search
    _, classical_checks = classical_search(n, target)

    # Grover search
    grover_result = run_grover_search(n, target, shots=shots)

    grover_oracle_calls = grover_result["iterations"]

    speedup = classical_checks / grover_oracle_calls

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "global_run_number": global_run_number,
        "batch_run_number": batch_run_number,
        "n": n,
        "N": N,
        "sqrt_N": sqrt_N,
        "target": target,
        "classical_checks": classical_checks,
        "grover_oracle_calls": grover_oracle_calls,
        "speedup": speedup,
    }

    return row


def run_experiment():
    print("Grover vs Classical Search Experiment")
    print("-------------------------------------")

    try:
        n = int(input("Enter number of qubits, 1-10: "))
    except ValueError:
        print("Error: please enter an integer from 1 to 10.")
        return

    if n < 1 or n > 10:
        print("Error: number of qubits must be between 1 and 10.")
        return

    try:
        number_of_runs = int(input("Enter number of runs: "))
    except ValueError:
        print("Error: please enter a valid integer for number of runs.")
        return

    if number_of_runs < 1:
        print("Error: number of runs must be at least 1.")
        return

    shots = 1000
    batch_rows = []

    next_global_run_number = get_next_global_run_number()

    print()
    print(f"Running {number_of_runs} experiment(s) with {n} qubit(s)...")
    print()

    for batch_run_number in range(1, number_of_runs + 1):
        global_run_number = next_global_run_number + batch_run_number - 1

        row = run_one_experiment(
            n=n,
            global_run_number=global_run_number,
            batch_run_number=batch_run_number,
            shots=shots,
        )

        save_result(row)
        batch_rows.append(row)

        print_single_run_summary(row)

    all_rows = load_results()
    

    batch_average = calculate_average_speedup(batch_rows)
    grouped_results = calculate_average_speedup_grouped_by_N(all_rows)

    N = 2 ** n
    sqrt_N = math.sqrt(N)

    classical_average_case = (N + 1) / 2
    grover_estimate = (math.pi / 4) * sqrt_N
    theoretical_average_speedup = classical_average_case / grover_estimate

    print()
    print("Theoretical Reference for Current N")
    print("-----------------------------------")
    print(f"N = 2^{n} = {N}")
    print(f"sqrt(N) = {sqrt_N:.4f}")
    print(f"Classical average-case checks ≈ {classical_average_case:.4f}")
    print(f"Grover oracle calls ≈ {grover_estimate:.4f}")
    print(f"Average speedup ≈ {theoretical_average_speedup:.4f}x")

    print_speedup_average("Current Batch Average Speedup", batch_average)
    print_grouped_average_by_N(grouped_results)

    print()
    print(f"Results saved to: {RESULT_FILE}")

def calculate_average_speedup_grouped_by_N(rows):
    
    #Group all saved results by search space size N, then calculate the average speedup for each N.
    
    groups = {}

    for row in rows:
        N = int(row["N"])

        if N not in groups:
            groups[N] = []

        groups[N].append(row)

    grouped_results = []

    for N, group_rows in groups.items():
        total_runs = len(group_rows)
        avg_speedup = sum(float(row["speedup"]) for row in group_rows) / total_runs

        n = int(group_rows[0]["n"])
        sqrt_N = math.sqrt(N)

        classical_average_case = (N + 1) / 2
        grover_estimate = (math.pi / 4) * sqrt_N
        theoretical_average_speedup = classical_average_case / grover_estimate

        grouped_results.append({
            "n": n,
            "N": N,
            "total_runs": total_runs,
            "avg_speedup": avg_speedup,
            "sqrt_N": sqrt_N,
            "theoretical_average_speedup": theoretical_average_speedup,
        })

    grouped_results.sort(key=lambda item: item["N"])

    return grouped_results

def print_grouped_average_by_N(grouped_results):
    
    #Print average speedup grouped by N.
    
    if not grouped_results:
        return

    print()
    print("Average Speedup Grouped by Search Space Size N")
    print("----------------------------------------------")
    print(
        f"{'n':>3} | {'N':>6} | {'runs':>6} | "
        f"{'avg speedup':>12} " #| {'sqrt(N)':>10} | {'theory avg speedup':>20}
    )
    print("-" * 72)

    for item in grouped_results:
        print(
            f"{item['n']:>3} | "
            f"{item['N']:>6} | "
            f"{item['total_runs']:>6} | "
            f"{item['avg_speedup']:>12.4f} | "
            #f"{item['sqrt_N']:>10.4f} | "
            #f"{item['theoretical_average_speedup']:>20.4f}"
        )

if __name__ == "__main__":
    run_experiment()