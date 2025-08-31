data = [
    {"name": "Alice", "points": 50},
    {"name": "Bob", "points": 75},
    {"name": "Charlie", "points": 60}
]

def show_leaderboard():
    sorted_data = sorted(data, key=lambda x: x["points"], reverse=True)
    print(sorted_data)

show_leaderboard()