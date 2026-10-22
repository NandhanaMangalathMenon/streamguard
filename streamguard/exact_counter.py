from collections import Counter


class ExactCounter:
    def __init__(self):
        # Stores the exact frequency of every traffic item.
        self.counts = Counter()

    def add(self, item):
        # Increase the frequency of one traffic item.
        self.counts[item] += 1

    def update(self, items):
        # Count multiple traffic items.
        self.counts.update(items)

    def estimate(self, item):
        # Return the exact frequency of an item.
        return self.counts[item]

    def get_top_k(self, k):
        # Reject a negative value of k.
        if k < 0:
            raise ValueError("K cannot be negative")

        # Sort by frequency, then alphabetically by item.
        return sorted(
            self.counts.items(),
            key=lambda item: (-item[1], item[0])
        )[:k]


def count_items(items):
    # Count the exact occurrences of every item.
    return Counter(items)


def get_top_k(exact_counts, k):
    if k < 0:
        raise ValueError("K cannot be negative")

    # Sort by descending frequency, then by item name.
    return sorted(
        exact_counts.items(),
        key=lambda item: (-item[1], item[0])
    )[:k]


def process_csv(filename):
    # Import the CSV loader from the traffic generator module.
    from streamguard.traffic_generator import load_traffic_csv

    traffic = load_traffic_csv(filename)
    return count_items(traffic)


if __name__ == "__main__":
    sample_traffic = ["A", "B", "A", "C", "A", "B"]

    counts = count_items(sample_traffic)

    print("Exact counts:", dict(counts))
    print("Top 2:", get_top_k(counts, 2))
