
import csv
import random
import ipaddress
import os


def generate_traffic(
    num_packets=1000,
    num_sources=100,
    heavy_hitter_count=5,
    heavy_hitter_probability=0.60,
    seed=42
):
    # Check that the number of packets is valid.
    if num_packets < 0:
        raise ValueError("Number of packets cannot be negative")

    # At least one source IP address is required.
    if num_sources <= 0:
        raise ValueError("Number of sources must be positive")

    # Heavy hitters cannot exceed the total number of sources.
    if heavy_hitter_count < 0 or heavy_hitter_count > num_sources:
        raise ValueError("Invalid number of heavy hitters")

    # Probability must be between 0 and 1.
    if not 0 <= heavy_hitter_probability <= 1:
        raise ValueError("Probability must be between 0 and 1")

    # Use a local random generator for reproducible results.
    rng = random.Random(seed)

    # Create unique IPv4 addresses for the traffic sources.
    source_ips = [
        str(ipaddress.IPv4Address(0x0A000001 + i))
        for i in range(num_sources)
    ]

    # Select the first few IP addresses as heavy hitters.
    heavy_hitters = source_ips[:heavy_hitter_count]

    # All remaining IP addresses are normal sources.
    normal_sources = source_ips[heavy_hitter_count:]

    # Store the generated traffic events.
    traffic = []

    # Generate the requested number of packets.
    for _ in range(num_packets):

        # Choose a heavy hitter with the specified probability.
        if heavy_hitters and (
            not normal_sources
            or rng.random() < heavy_hitter_probability
        ):
            source = rng.choice(heavy_hitters)

        # Otherwise, choose a normal source.
        else:
            source = rng.choice(normal_sources)

        # Add the source IP to the traffic list.
        traffic.append(source)

    # Return the complete list of generated IP addresses.
    return traffic


def generate_stream(
    num_packets=1000,
    num_sources=100,
    heavy_hitter_count=5,
    heavy_hitter_probability=0.60,
    seed=42
):
    # Generate traffic using the existing function.
    traffic = generate_traffic(
        num_packets=num_packets,
        num_sources=num_sources,
        heavy_hitter_count=heavy_hitter_count,
        heavy_hitter_probability=heavy_hitter_probability,
        seed=seed
    )

    # Yield each event individually for stream processing.
    for source_ip in traffic:
        yield source_ip


def save_traffic_csv(traffic, filename="data/sample_traffic.csv"):
    # Create the parent directory if it does not exist.
    directory = os.path.dirname(filename)

    if directory:
        os.makedirs(directory, exist_ok=True)

    # Open the CSV file for writing.
    with open(filename, "w", newline="", encoding="utf-8") as file:

        # Create a CSV writer.
        writer = csv.writer(file)

        # Write the column headings.
        writer.writerow(["packet_id", "source_ip"])

        # Write each packet with its ID and source IP.
        for packet_id, source_ip in enumerate(traffic, start=1):
            writer.writerow([packet_id, source_ip])


def load_traffic_csv(filename="data/sample_traffic.csv"):
    # Open the existing CSV file for reading.
    with open(filename, newline="", encoding="utf-8") as file:

        # Read the rows using their column names.
        reader = csv.DictReader(file)

        # Return a list containing the source IP addresses.
        return [row["source_ip"] for row in reader]


if __name__ == "__main__":

    # Generate 1,000 simulated packets.
    traffic = generate_traffic()

    # Save the packets to a CSV file.
    save_traffic_csv(traffic)

    # Display the number of packets generated.
    print("Generated packets:", len(traffic))

    # Display the CSV output location.
    print("Saved to data/sample_traffic.csv")

    # Test the stream generator with five packets.
    sample_stream = list(generate_stream(num_packets=5))

    print("Sample stream:", sample_stream)
