import pandas as pd
import random
import string
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(0)
random.seed(0)

# Utility Functions
def unique_id(prefix, length=4):
    return prefix + ''.join(random.choices(string.digits, k=length))

def random_date(start_year=2015, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime('%d-%m-%Y')

def score():
    win_score = 21
    lose_score = random.randint(0, 19)
    return f"{win_score} to {lose_score}"

# 1. Sponsorship Table
sponsorships = []
for i in range(15):
    sid = unique_id('SP')
    sponsorships.append({
        'sponsorship_id': sid,
        'sponsor_name': fake.company(),
        'sponsorship_amt': random.randint(10000, 100000)
    })
sponsorship_df = pd.DataFrame(sponsorships)
sponsorship_df.to_csv('Sponsorship.csv', index=False)

# 2. Tournaments Table
tournaments = []
tournament_names = set()
for i in range(30):
    tid = unique_id('T')
    sponsor = random.choice(sponsorships)
    name = fake.city() + " Open"
    while name in tournament_names:
        name = fake.city() + " Open"
    tournament_names.add(name)
    start = datetime.strptime(random_date(), '%d-%m-%Y')
    end = (start + timedelta(days=random.randint(3, 7))).strftime('%d-%m-%Y')
    tournaments.append({
        'tournament_id': tid,
        'sponsorship_id': sponsor['sponsorship_id'],
        'name': name,
        'start_date': start.strftime('%d-%m-%Y'),
        'end_date': end,
        'location': fake.city(),
        'prize_pool': random.choice([10000, 20000, 50000, 100000]),
        'budget': random.choice([20000, 50000, 120000])
    })
tournament_df = pd.DataFrame(tournaments)
tournament_df.to_csv('Tournaments.csv', index=False)

# 3. Coaches Table
specialisations = ['Smash', 'Rally', 'Net Play', 'Defense', 'Serve', 'Footwork']
countries = [
    'USA', 'UK', 'China', 'Indonesia', 'South Korea', 'Denmark', 
    'Malaysia', 'Japan', 'India', 'France', 'Italy', 'Spain', 
    'Brazil', 'New Zealand'
]

coaches = []
coach_names = set()
for _ in range(50):
    name = fake.name()
    while name in coach_names:
        name = fake.name()
    coach_names.add(name)
    cid = unique_id('C')
    coaches.append({
        'coach_id': cid,
        'name': name,
        'experience_years': random.randint(5, 25),
        'country': random.choice(countries),
        'specialisation': random.choice(specialisations)
    })

coach_df = pd.DataFrame(coaches)
coach_df.to_csv('Coaches.csv', index=False)
# 4. Players Table
countries = [
    'USA', 'UK', 'China', 'Indonesia', 'South Korea', 'Denmark', 
    'Malaysia', 'Japan', 'India', 'France', 'Italy', 'Spain', 
    'Brazil', 'New Zealand'
]

players = []
player_names = set()
for _ in range(80):
    name = fake.name()
    while name in player_names:
        name = fake.name()
    player_names.add(name)
    pid = unique_id('P')
    coach = random.choice(coaches)
    wins = random.randint(0, 100)
    losses = random.randint(0, 100)
    total = wins + losses
    players.append({
        'player_id': pid,
        'name': name,
        'birth_date': random_date(1985, 2005),
        'country': random.choice(countries),
        'ranking': random.randint(1, 100),
        'total_matches': total,
        'wins': wins,
        'losses': losses,
        'career_earnings': random.choice([50000, 100000, 150000]),
        'coach_id': coach['coach_id']
    })

player_df = pd.DataFrame(players)
player_df.to_csv('Players.csv', index=False)

# 5. Officials Table
officials = []
official_names = set()
for i in range(40):
    name = fake.name()
    while name in official_names:
        name = fake.name()
    official_names.add(name)
    officials.append({
        'officials_id': unique_id('OF'),
        'name': name
    })
official_df = pd.DataFrame(officials)
official_df.to_csv('Officials.csv', index=False)

# 6. Matches Table
matches = []
match_ids = []
for i in range(120):
    tid = random.choice(tournaments)['tournament_id']
    p1, p2 = random.sample(players, 2)
    winner = random.choice([p1, p2])
    mid = unique_id('M')
    match_ids.append(mid)
    matches.append({
        'match_id': mid,
        'tournament_id': tid,
        'player1_id': p1['player_id'],
        'player2_id': p2['player_id'],
        'date': random_date(2020, 2025),
        'venue': fake.city(),
        'score': score(),
        'winner_id': winner['player_id']
    })
match_df = pd.DataFrame(matches)
match_df.to_csv('Matches.csv', index=False)

# 7. Match_Officials Table
match_officials = []
for match in match_ids:
    officials_for_match = random.sample(officials, k=random.randint(1, 3))
    for official in officials_for_match:
        match_officials.append({
            'match_id': match,
            'officials_id': official['officials_id']
        })
match_official_df = pd.DataFrame(match_officials)
match_official_df.to_csv('Match_Officials.csv', index=False)

# 8. Player_Stats Table
player_stats = []
for i in range(150):
    player = random.choice(players)
    tournament = random.choice(tournaments)
    matches_played = random.randint(1, 10)
    wins = random.randint(0, matches_played)
    losses = matches_played - wins
    player_stats.append({
        'stat_id': unique_id('ST'),
        'player_id': player['player_id'],
        'tournament_id': tournament['tournament_id'],
        'matches_played': matches_played,
        'wins': wins,
        'losses': losses,
        'aces': random.randint(10, 100),
        'smash_wins': random.randint(5, 50),
        'smash_attempts': random.randint(10, 60),
        'rally_points_won': random.randint(50, 150)
    })
player_stats_df = pd.DataFrame(player_stats)
player_stats_df.to_csv('Player_Stats.csv', index=False)

# 9. Player_Coach_Assignment Table
player_coach_assignment = []
for player in players:
    player_coach_assignment.append({
        'player_id': player['player_id'],
        'coach_id': player['coach_id'],
        'start_date': random_date(2018, 2023),
        'end_date': random_date(2024, 2026)
    })
player_coach_df = pd.DataFrame(player_coach_assignment)
player_coach_df.to_csv('Player_Coach_Assignment.csv', index=False)

# 10. Equipment Table
equipment_types = ['Shoes', 'Racquet', 'Grips']
brands = ['Yonex', 'Li-Ning', 'Decathlon', 'Carlton']
model_prefixes = ['Arcsaber', 'Astrox', 'Nanoflare', 'Imperial']

equipment = []
for player in players:
    eq_id = unique_id('EQP')
    equipment.append({
        'equipment_id': eq_id,
        'equipment_name': random.choice(equipment_types),
        'brand_name': random.choice(brands),
        'model': f"{random.choice(model_prefixes)} {random.randint(40, 100)}",
        'player_id': player['player_id']
    })
equipment_df = pd.DataFrame(equipment)
equipment_df.to_csv('Equipment.csv', index=False)