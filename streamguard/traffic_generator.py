
import csv
import random
import ipaddress


def generate_traffic(
    num_packets=1000,
    num_sources=100,
    heavy_hitter_count=5,
    heavy_hitter_probability=0.60,
    seed=42
):
    # Reject invalid configurations before generating traffic.
    if num_packets < 0:
        raise ValueError("Number of packets cannot be negative")

    if num_sources <= 0:
        raise ValueError("Number of sources must be positive")

    if heavy_hitter_count < 0 or heavy_hitter_count > num_sources:
        raise ValueError("Invalid number of heavy hitters")

    if not 0 <= heavy_hitter_probability <= 1:
        raise ValueError("Probability must be between 0 and 1")

    # A local random generator makes experiments reproducible.
    rng = random.Random(seed)

    # Create distinct source IP addresses.
    source_ips = [
        str(ipaddress.IPv4Address(0x0A000001 + i))
        for i in range(num_sources)
    ]

    # Select the first few addresses as heavy hitters.
    heavy_hitters = source_ips[:heavy_hitter_count]
    normal_sources = source_ips[heavy_hitter_count:]

    traffic = []

    for _ in range(num_packets):
        # Generate frequent traffic from heavy hitters.
        if heavy_hitters and (
            not normal_sources
            or rng.random() < heavy_hitter_probability
        ):
            source = rng.choice(heavy_hitters)
        else:
            source = rng.choice(normal_sources)

        traffic.append(source)

    return traffic


def save_traffic_csv(traffic, filename="data/sample_traffic.csv"):
    # Write every generated packet as one CSV row.
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["packet_id", "source_ip"])

        for packet_id, source_ip in enumerate(traffic, start=1):
            writer.writerow([packet_id, source_ip])


def load_traffic_csv(filename):
    # Read source IP addresses from an existing traffic file.
    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [row["source_ip"] for row in reader]


if __name__ == "__main__":
    traffic = generate_traffic()
    save_traffic_csv(traffic)

    print("Generated packets:", len(traffic))
    print("Saved to data/sample_traffic.csv")

