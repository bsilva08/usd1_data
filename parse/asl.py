# Process Golden Age ASL scores.

import datetime
import os
import re

from utils import get_id

from usd1_data.settings import ROOT_DIR

games_filename = os.path.join(ROOT_DIR, 'usd1_data/data/games/league/jose/asl')
stats_filename = os.path.join(ROOT_DIR, 'usd1_data/data/stats/asl')


# Pull this out into lift.py

def get_full_name_stats(team, season):
    nseason = season.replace("Playoffs", '').strip()

    TEAM_HISTORY_TUPLES = [
        #Uniques
        ('B. Hakoah', [], 'Hakoah All-Stars'),
        ('B/Newark', [], 'Bridgeport Hungaria/Newark'), # Need to fix this one.
        ('Fleischer', [], 'Fleisher Yarn'), # I misspelled Fleisher in Excel.
        ('Harrison', [], 'Harrison Soccer Club'),
        ('Hartford', [], 'Hartford Americans'),
        ('Holyoke', [], 'Holyoke Falcons'),
        ('NY Americans', [], 'New York Americans'),
        ('NY Giants', [], 'New York Giants'),
        ('NY Nationals', [], 'New York Nationals'),
        ('NY Yankees', [], 'New York Yankees'),
        ('New York', [], 'New York Field Club'), # Different teams?
        ('New York FC', [], 'New York Field Club'), # Different teams?
        ('New York SC', [], 'New York Soccer Club'),
        ('Todd', [], 'Todd Shipyards F.C.'),
        ]
    

    
    team_matches = [e for e in TEAM_HISTORY_TUPLES if e[0] == team]

    if len(team_matches) == 0:
        #print("Fail: %s" % team)
        return team
    elif len(team_matches) == 1:
        assert team_matches[0][1] == []
        return team_matches[0][2]
    else:
        for t, seasons, full_name in team_matches:
            if nseason in seasons:
                return full_name

    import pdb; pdb.set_trace()
    x = 5
    


# These should be merged into get_team
team_map = {
    'J&P Coats': 'J & P Coats',
    'NY Giants': 'New York Giants',
    'New York National Giants': 'New York Giants',
    'Fleischer': 'Fleisher Yarn',
    'Fleischer Yarn': 'Fleisher Yarn',

    'Philadelphia 1928-1929': 'Philadelphia Field Club',
    'NY Nationals': 'New York Nationals',
    'Abbot W.': 'Abbot Worsted',
    'Holley C.': 'Holley Carburetor',
    'Yonkers Th.': 'Yonkers Thistle',
    'Scullin St.': 'Scullin Steels',
    'Hispano': 'Brooklyn Hispano',
    'Bricklayers': 'Bricklayers FC',
    'NY Yankees': 'New York Yankees',
    'NY Americans': 'New York Americans',
    'Prospect H.': 'Prospect Hill FC',
    'Bethlehem': 'Bethlehem Steel',

    # These are just so the build script doesn't report an error.
    # Move these to a different object.
    'Brooklyn FC': 'Brooklyn FC',
    'Ben Millers': 'Ben Millers',
    'Pawtucket Rangers': 'Pawtucket Rangers',
    'Fall River Marksmen': 'Fall River Marksmen',
    'Providence Gold Bugs': 'Providence Gold Bugs',
    'Bridgeport Hungaria': 'Bridgeport Hungaria',
    'New York SC': 'New York SC',
    'New York Giants': 'New York Giants',
    'Boston Wonder Workers': 'Boston Wonder Workers',
    'Boston Bears': 'Boston Bears',
    'Brooklyn Wanderers': 'Brooklyn Wanderers',
    'Brooklyn Hakoah': 'Brooklyn Hakoah',
    'New York Nationals': 'New York Nationals',
    'New Bedford Whalers': 'New Bedford Whalers',
    'Bridgeport Bears': 'Bridgeport Bears',
    'Philadelphia 1929 Fall': 'Philadelphia 1929 Fall',
    'Bridgeport Bears': 'Bridgeport Bears',
    
}

competition_map = {
    'ASL': 'American Soccer League (1921-1933)',
    'ASA Cup': 'AFA Cup',
    'AFA Cup': 'AFA Cup',
    }

LEWIS_CUP_YEARS = set([
    '1924-1925',
    '1925-1926',
    '1926-1927',
    '1927-1928',
    '1928-1929',
    '1930 Spring',
    ])


def process_stats():
    f = open(stats_filename)
    l = []
    for line in f:
        if not line.startswith('*'):
            lx = load_stat(line)
        l.append(lx)

    return [e for e in l if e]


def load_stat(line):
    fields = line.split("\t")
    name, team, season = fields[:3]

    def convert(n):
        if n.strip():
            try:
                return int(n)
            except:
                import pdb; pdb.set_trace()
                x = 5
        return 0

    stats = [convert(e) for e in fields[3:]]

    season_games, cup_games, other_cup_games, season_goals, cup_goals, other_cup_goals = stats



    if "-" in season:
        start, end = season.split("-")
        season = "19%s-19%s" % (start, end)

    #if season == '1929-1930':
    #    season = '1930 Spring'


    team_name = get_full_name_stats(team, season)

    competition = 'American Soccer League (1921-1933)'
    return [{
            'name': name,
            'team': team_name,
            'season': season,
            'competition': competition,
            'games_played': season_games,
            'goals': season_goals,
            'source': 'American Soccer League (1921-1931)',
            }]
        
    return l


def process_asl_games():
    return process_games()[0]

def process_asl_goals():
    return process_games()[1]
    

def process_games():
    f = open(games_filename)
    game_list = []
    goal_list = []
    gp = GameProcessor()
    for line in f:
        g = gp.consume_row(line)
        if g:
            game_data, goals = g
            game_list.append(game_data)
            goal_list.extend(goals)

    return game_list, goal_list


class GameProcessor(object):
    """
    Process the games text.
    Returns a list of dicts representing game results.
    """

    def __init__(self):
        self.year = None
        self.month = None
        self.day = None
        

    def consume_row(self, row):
        if not row.strip():
            return {}

        fields = row.strip().split('\t')

        # What is field # 10?
        if len(fields) == 10:
            print("Ten fields for some reason?")
            print(row)
            fields = fields[:9]

        if len(fields) == 9:
            team, season, competition, month, day, opponent, location, score, goals = fields
        elif len(fields) == 8:
            team, season, competition, month, day, opponent, location, score = fields
            goals = ''

        else:
            # A couple of games without scores (forfeits). (len = 7)
            print(fields)
            return {}

        
        # Figure out what year a game was played in. (dates are only partially entered for convenience)
        sx = season # Clean up the season a bit; 
        for e in 'Fall', 'Spring', 'Playoffs', 'First Half', 'Second Half':
            sx = sx.replace(e, '')

        if '-' in season:
            try:
                start_year, end_year = [int(e) for e in sx.split('-')]
            except:
                import pdb; pdb.set_trace()
        else:
            start_year = end_year = int(re.match('^(\d+).*$', sx).groups()[0])

        round = ''
        if 'Half' in season:
            season, round = season.split(' ', 1)

        # Skipping minigames for now.
        if day in ('M', 'SO', 'OT', 'SO-M'):
            return {}

        # Not played.
        if score == 'np':
            return {}

        
        # Process day before month. (huh? why?)
        if day.strip():
            self.day = int(day)

        if month.strip():
            self.month = int(month)

            if self.month >= 8:
                self.year = start_year
            else:
                self.year = end_year

        d = datetime.datetime(self.year, self.month, self.day)

        if score in ('forfeit loss', 'forfeit win', 'awarded', ''):
            return {}

        try:
            team_score,  opponent_score = [int(e) for e in score.split(',')]
        except:
            import pdb; pdb.set_trace()

        competition = competition_map.get(competition, competition)


        if 'Playoffs' in season:
            season = season.replace('Playoffs', '').strip()
            #competition = "%s Playoffs" % competition
            stage = 'playoffs'
        else:
            stage = ''


        if competition in ('US Open Cup', 'AFA Cup', 'American Cup'):
            return {}

        team = get_full_name_stats(team, season)
        opponent = get_full_name_stats(opponent, season)
            
        if location == 'h':
            home_team = team
            home_score = team_score
            away_team = opponent
            away_score = opponent_score
        else:
            home_team = opponent
            home_score = opponent_score
            away_team = team
            away_score = team_score

        gid = get_id()

        game_data =  {
            'gid': gid,
            'competition': competition,
            'season': season,
            'date': d,
            'team1': home_team,
            'team2': away_team,
            'team1_score': home_score,
            'team2_score': away_score,
            'home_team': home_team,
            'sources': ['American Soccer League (1921-1931)',],
            'round': round,
            'stage': stage,
            }

        goal_list = []


        for goal in goals.split(','):
            m = re.match("(.*?) (\d)", goal)
            if m:
                goal, count = m.groups()
                count = int(count)
            elif goal.strip():
                count = 1
            else:
                # Empty results.
                count = 0


            for e in range(count):
                goal_list.append({
                        'gid': gid,
                        'team': team,
                        'season': season,
                        'competition': competition,
                        'date': d,
                        'goal': goal,
                        'minute': None,
                        'assists': []
                        })

        return game_data, goal_list
    

def get_bios():
    '/data/people/asl'
    return []


if __name__ == "__main__":
    print(process_stats())
    #print(process_bios())


