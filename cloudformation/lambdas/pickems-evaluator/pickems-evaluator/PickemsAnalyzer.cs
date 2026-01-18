using pickems_evaluator.Models.RiotApi;

namespace pickems_evaluator;

public static class PickemsAnalyzer
{
    // Which Player will have the most first bloods?
    public static string GetMostFirstBloods(List<Match> matches)
    {
        var firstBloodCounts = new Dictionary<string, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (participant.FirstBloodKill)
                {
                    if (!firstBloodCounts.ContainsKey(participant.ParticipantId))
                        firstBloodCounts[participant.ParticipantId] = 0;

                    firstBloodCounts[participant.ParticipantId]++;
                }
            }
        }

        if (firstBloodCounts.Count == 0)
            return "No first bloods recorded";

        var maxValue = firstBloodCounts.Max(x => x.Value);

        var topParticipants = firstBloodCounts
            .Where(x => x.Value == maxValue)
            .Select(x => x.Key)
            .ToList();

        return $"Participants {string.Join(", ", topParticipants)} with {maxValue} first bloods";
    }

    // Which Player will have the highest KDA overall?
    public static string GetHighestKDAPlayer(List<Match> matches)
    {
        var participantStats = new Dictionary<string, (int kills, int deaths, int assists)>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!participantStats.ContainsKey(participant.ParticipantId))
                    participantStats[participant.ParticipantId] = (0, 0, 0);

                var current = participantStats[participant.ParticipantId];
                participantStats[participant.ParticipantId] = (
                    current.kills + participant.Kills,
                    current.deaths + participant.Deaths,
                    current.assists + participant.Assists
                );
            }
        }

        var bestKDA = participantStats.OrderByDescending(x =>
        {
            var deaths = x.Value.deaths > 0 ? x.Value.deaths : 1;
            return (x.Value.kills + x.Value.assists) / (double)deaths;
        }).FirstOrDefault();

        var kdaRatio = bestKDA.Value.deaths > 0
            ? ((bestKDA.Value.kills + bestKDA.Value.assists) / (double)bestKDA.Value.deaths)
            : (bestKDA.Value.kills + bestKDA.Value.assists);

        return $"Participant {bestKDA.Key} with KDA {kdaRatio:F2} ({bestKDA.Value.kills}/{bestKDA.Value.deaths}/{bestKDA.Value.assists})";
    }

    // Which player will die the most?
    public static string GetMostDeathsPlayer(List<Match> matches)
    {
        var participantDeaths = new Dictionary<string, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!participantDeaths.ContainsKey(participant.ParticipantId))
                    participantDeaths[participant.ParticipantId] = 0;

                participantDeaths[participant.ParticipantId] += participant.Deaths;
            }
        }

        var result = participantDeaths.OrderByDescending(x => x.Value).FirstOrDefault();
        return $"Participant {result.Key} with {result.Value} deaths";
    }

    // Which player will have the worst vision score overall?
    public static string GetWorstVisionScorePlayer(List<Match> matches)
    {
        var participantVision = new Dictionary<string, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!participantVision.ContainsKey(participant.ParticipantId))
                    participantVision[participant.ParticipantId] = 0;

                participantVision[participant.ParticipantId] += participant.VisionScore;
            }
        }

        var result = participantVision.OrderBy(x => x.Value).FirstOrDefault();
        return $"Participant {result.Key} with {result.Value} vision score";
    }

    // Which player will have the most CS in a single game?
    public static string GetMostCSInSingleGame(List<Match> matches)
    {
        int maxCS = 0;
        string participantId = "";

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                int cs = participant.TotalMinionsKilled + participant.NeutralMinionsKilled;
                if (cs > maxCS)
                {
                    maxCS = cs;
                    participantId = participant.ParticipantId;
                }
            }
        }

        return $"Participant {participantId} with {maxCS} CS";
    }

    // Which team will have the most kills overall?
    public static string GetMostKillsTeam(List<Match> matches)
    {
        var teamKills = new Dictionary<int, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!teamKills.ContainsKey(participant.TeamId))
                    teamKills[participant.TeamId] = 0;

                teamKills[participant.TeamId] += participant.Kills;
            }
        }

        var result = teamKills.OrderByDescending(x => x.Value).FirstOrDefault();
        return $"Team {result.Key} with {result.Value} kills";
    }

    // Which team will slay the most objectives overall?
    public static string GetMostObjectivesTeam(List<Match> matches)
    {
        var teamObjectives = new Dictionary<int, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!teamObjectives.ContainsKey(participant.TeamId))
                    teamObjectives[participant.TeamId] = 0;

                int objectives = participant.DragonKills + participant.BaronKills + 
                                participant.RiftHeraldKills + participant.InhibitorKills + 
                                participant.TurretKills;
                teamObjectives[participant.TeamId] += objectives;
            }
        }

        var result = teamObjectives.OrderByDescending(x => x.Value).FirstOrDefault();
        return $"Team {result.Key} with {result.Value} objectives";
    }

    // Which team will have the most deaths overall?
    public static string GetMostDeathsTeam(List<Match> matches)
    {
        var teamDeaths = new Dictionary<int, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!teamDeaths.ContainsKey(participant.TeamId))
                    teamDeaths[participant.TeamId] = 0;

                teamDeaths[participant.TeamId] += participant.Deaths;
            }
        }

        var result = teamDeaths.OrderByDescending(x => x.Value).FirstOrDefault();
        return $"Team {result.Key} with {result.Value} deaths";
    }

    // Which team will deal the most damage to structures in a single game?
    public static string GetMostStructureDamageInSingleGame(List<Match> matches)
    {
        int maxDamage = 0;
        int teamId = 0;

        foreach (var match in matches)
        {
            var teamStructureDamage = new Dictionary<int, int>();

            foreach (var participant in match.Participants)
            {
                if (!teamStructureDamage.ContainsKey(participant.TeamId))
                    teamStructureDamage[participant.TeamId] = 0;

                teamStructureDamage[participant.TeamId] += participant.DamageDealtToBuildings + participant.DamageDealtToTurrets;
            }

            var maxInGame = teamStructureDamage.OrderByDescending(x => x.Value).FirstOrDefault();
            if (maxInGame.Value > maxDamage)
            {
                maxDamage = maxInGame.Value;
                teamId = maxInGame.Key;
            }
        }

        return $"Team {teamId} with {maxDamage} structure damage in a single game";
    }

    // Which team will have the most pings in a single game?
    public static string GetMostPingsInSingleGame(List<Match> matches)
    {
        int maxPings = 0;
        int teamId = 0;

        foreach (var match in matches)
        {
            var teamPings = new Dictionary<int, int>();

            foreach (var participant in match.Participants)
            {
                if (!teamPings.ContainsKey(participant.TeamId))
                    teamPings[participant.TeamId] = 0;

                teamPings[participant.TeamId] += participant.Pings;
            }

            var maxInGame = teamPings.OrderByDescending(x => x.Value).FirstOrDefault();
            if (maxInGame.Value > maxPings)
            {
                maxPings = maxInGame.Value;
                teamId = maxInGame.Key;
            }
        }

        return $"Team {teamId} with {maxPings} pings in a single game";
    }

    // Who will be the most banned champion?
    public static string GetMostBannedChampion(List<Match> matches)
    {
        var championBans = new Dictionary<int, int>();

        foreach (var match in matches)
        {
            foreach (var team in match.Teams)
            {
                foreach (var ban in team.Bans)
                {
                    if (ban > 0)
                    {
                        if (!championBans.ContainsKey(ban))
                            championBans[ban] = 0;

                        championBans[ban]++;
                    }
                }
            }
        }

        var result = championBans.OrderByDescending(x => x.Value).FirstOrDefault();
        return $"Champion {result.Key} with {result.Value} bans";
    }

    // Which champion will tank the most damage in a single game?
    public static string GetChampionTanksMostDamage(List<Match> matches)
    {
        int maxDamage = 0;
        int championId = 0;

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (participant.TotalDamageTaken > maxDamage)
                {
                    maxDamage = participant.TotalDamageTaken;
                    championId = participant.ChampionId;
                }
            }
        }

        return $"Champion {championId} tanked {maxDamage} damage in a single game";
    }

    // Which champion will deal the most damage in a single game?
    public static string GetChampionDealtMostDamage(List<Match> matches)
    {
        int maxDamage = 0;
        int championId = 0;

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (participant.TotalDamageDealtToChampions > maxDamage)
                {
                    maxDamage = participant.TotalDamageDealtToChampions;
                    championId = participant.ChampionId;
                }
            }
        }

        return $"Champion {championId} dealt {maxDamage} damage in a single game";
    }

    // What's a champion that will be revived? (has most deaths)
    public static string GetMostDeathsChampion(List<Match> matches)
    {
        var championDeaths = new Dictionary<int, int>();

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                if (!championDeaths.ContainsKey(participant.ChampionId))
                    championDeaths[participant.ChampionId] = 0;

                championDeaths[participant.ChampionId] += participant.Deaths;
            }
        }

        var result = championDeaths.OrderByDescending(x => x.Value).FirstOrDefault();
        return $"Champion {result.Key} with {result.Value} deaths overall";
    }

    // How many games will last longer than 45 minutes?
    public static string GetGamesLongerThan45Minutes(List<Match> matches)
    {
        int count = 0;

        foreach (var match in matches)
        {
            if (match.GameDuration > 2700) // 45 minutes = 2700 seconds
                count++;
        }

        return $"{count} games last longer than 45 minutes";
    }

    // How many objective steals will there be overall?
    public static string GetTotalObjectiveSteals(List<Match> matches)
    {
        int totalSteals = 0;

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                totalSteals += participant.ObjectivesStolen;
            }
        }

        return $"{totalSteals} objective steals overall";
    }

    // How many total pentakills will there be?
    public static string GetTotalPentakills(List<Match> matches)
    {
        int totalPentas = 0;

        foreach (var match in matches)
        {
            foreach (var participant in match.Participants)
            {
                totalPentas += participant.PentaKills;
            }
        }

        return $"{totalPentas} pentakills overall";
    }

    // How long will the shortest game be in minutes?
    public static string GetShortestGameDuration(List<Match> matches)
    {
        if (matches.Count == 0)
            return "No games available";

        int shortestDuration = matches.Min(m => m.GameDuration);
        int minutes = shortestDuration / 60;

        return $"Shortest game: {minutes} minutes ({shortestDuration} seconds)";
    }

    // What will be the biggest gold difference between teams in a game?
    public static string GetBiggestGoldDifference(List<Match> matches)
    {
        int maxGoldDifference = 0;

        foreach (var match in matches)
        {
            var teamGold = new Dictionary<int, int>();

            foreach (var participant in match.Participants)
            {
                if (!teamGold.ContainsKey(participant.TeamId))
                    teamGold[participant.TeamId] = 0;

                teamGold[participant.TeamId] += participant.GoldEarned;
            }

            if (teamGold.Count >= 2)
            {
                var goldValues = teamGold.Values.OrderByDescending(x => x).ToList();
                int difference = goldValues[0] - goldValues[1];

                if (difference > maxGoldDifference)
                    maxGoldDifference = difference;
            }
        }

        return $"Biggest gold difference: {maxGoldDifference} gold";
    }
}
