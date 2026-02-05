using Amazon.Lambda.Core;
using System.Text.Json;
using pickems_evaluator.Data;
using pickems_evaluator.Models.Database;
using pickems_evaluator.Models.RiotApi;
using pickems_evaluator.Models;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace pickems_evaluator;

public class Function
{

    const string tournementMatchesQuery = "SELECT * FROM tournament_matches";
    const string teamQuery = "SELECT team_id from players p join riot_accounts ra on p.id = ra.player_id where account_puuid =";
    const string playerQuery = "SELECT p.id, ra.account_puuid AS puuid FROM players p LEFT JOIN riot_accounts ra ON ra.player_id = p.id";
    const string playerPuuidQuery = "SELECT account_puuid from riot_accounts where player_id =";
    const string profileQuery = "SELECT * FROM profiles";
    const string pickemsQuery = "SELECT * FROM pickems where user_id =";

    /// <summary>
    /// A simple function that takes a string and does a ToUpper
    /// </summary>
    /// <param name="input">The event for the Lambda function handler to process.</param>
    /// <param name="context">The ILambdaContext that provides methods for logging and describing the Lambda environment.</param>
    /// <returns></returns>
    public async Task FunctionHandler(object input, ILambdaContext context)
    {
        var DBmatches = await DatabaseHelper.ExecuteQueryAsync<TournementMatch>(tournementMatchesQuery, reader => new TournementMatch
        {
            Id = (int)reader["id"],
            WinnerTeamId = (int)reader["winner_team_id"],
            TournementMatchId = reader["tournament_match_id"].ToString(),
        });

        Console.WriteLine("Collected matches");

        var matches = new List<Match>();
        foreach (var match in DBmatches)
        {
            matches.Add(await RiotApiHelper.FetchMatchDataAsync(match.TournementMatchId));

            var team1Id = await DatabaseHelper.ExecuteQueryAsync<int>($"{teamQuery}'{matches[matches.Count - 1].Participants[0].ParticipantId}'", reader => (int)reader["team_id"]);
            matches[matches.Count - 1].Teams[0].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[0].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[1].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[2].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[3].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[4].TeamId = team1Id[0];

            var team2Id = await DatabaseHelper.ExecuteQueryAsync<int>($"{teamQuery}'{matches[matches.Count - 1].Participants[9].ParticipantId}'", reader => (int)reader["team_id"]);
            matches[matches.Count - 1].Teams[1].TeamId = team2Id[0];
            matches[matches.Count - 1].Participants[5].TeamId = team2Id[0];
            matches[matches.Count - 1].Participants[6].TeamId = team2Id[0];
            matches[matches.Count - 1].Participants[7].TeamId = team2Id[0];
            matches[matches.Count - 1].Participants[8].TeamId = team2Id[0];
            matches[matches.Count - 1].Participants[9].TeamId = team2Id[0];
        }

        Console.WriteLine("API data called");

        var players = await DatabaseHelper.ExecuteQueryAsync<(int, string)>(
            playerQuery,
            reader => ((int)reader["id"], (string)reader["puuid"])
        );

        var profiles = await DatabaseHelper.ExecuteQueryAsync<int>(
            profileQuery,
            reader => (int)reader["id"]);

        var playerIdToPuuid = new Dictionary<string, string>();
        var playerPuuidMappings = await DatabaseHelper.ExecuteQueryAsync<(string, string)>(
            "SELECT p.id, ra.account_puuid FROM players p LEFT JOIN riot_accounts ra ON ra.player_id = p.id",
            reader => ((string)reader["id"].ToString(), (string)reader["account_puuid"])
        );

        foreach (var (playerId, puuid) in playerPuuidMappings)
        {
            if (!string.IsNullOrEmpty(puuid))
            {
                playerIdToPuuid[playerId] = puuid;
            }
        }

        Console.WriteLine("Loaded player ID to PUUID mappings");

        var championIdToName = await RiotApiHelper.FetchChampionDataAsync();
        Console.WriteLine("Loaded champion data");

        var profilePickems = new List<Profile>();
        foreach (var profile in profiles)
        {
            var pickems = await DatabaseHelper.ExecuteQueryAsync<Pickems>($"{pickemsQuery}{profile}", reader => new Pickems
            {
                Id = reader["id"].ToString(),
                PickemId = reader["pickem_id"].ToString(),
                Value = reader["value"].ToString(),
            });
            profilePickems.Add(new Profile
            {
                Id = profile,
                Pickems = pickems,
                Score = 0
            });
        }

        Console.WriteLine("Collected profiles and pickems");

        string answer;

        //most_fb
        answer = PickemsAnalyser.GetMostFirstBloods(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_fb")?.Value;
            if (!string.IsNullOrEmpty(guess) && playerIdToPuuid.TryGetValue(guess, out var puuid) && puuid == answer)
            {
                profile.Score += 1;
            }
        }

        //highest_kda
        answer = PickemsAnalyser.GetHighestKDAPlayer(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "highest_kda")?.Value;
            if (!string.IsNullOrEmpty(guess) && playerIdToPuuid.TryGetValue(guess, out var puuid) && puuid == answer)
            {
                profile.Score += 1;
            }
        }

        //most_deaths_player
        answer = PickemsAnalyser.GetMostDeathsPlayer(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_deaths_player")?.Value;
            if (!string.IsNullOrEmpty(guess) && playerIdToPuuid.TryGetValue(guess, out var puuid) && puuid == answer)
            {
                profile.Score += 1;
            }
        }

        //tunnel_vision
        answer = PickemsAnalyser.GetWorstVisionScorePlayer(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "tunnel_vision")?.Value;
            if (!string.IsNullOrEmpty(guess) && playerIdToPuuid.TryGetValue(guess, out var puuid) && puuid == answer)
            {
                profile.Score += 1;
            }
        }

        //most_cs
        answer = PickemsAnalyser.GetMostCSInSingleGame(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_cs")?.Value;
            if (!string.IsNullOrEmpty(guess) && playerIdToPuuid.TryGetValue(guess, out var puuid) && puuid == answer)
            {
                profile.Score += 1;
            }
        }

        //most_kills_team
        answer = PickemsAnalyser.GetMostKillsTeam(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_kills_team")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //most_objs_team
        answer = PickemsAnalyser.GetMostObjectivesTeam(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_objs_team")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //most_deaths_team
        answer = PickemsAnalyser.GetMostDeathsTeam(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_deaths_team")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //demolish_team
        answer = PickemsAnalyser.GetMostStructureDamageInSingleGame(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "demolish_team")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //team_pings
        answer = PickemsAnalyser.GetMostPingsInSingleGame(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "team_pings")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //most_banned
        answer = PickemsAnalyser.GetMostBannedChampion(matches);
        answer = championIdToName[answer];
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_banned")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //tankiest_champ
        answer = PickemsAnalyser.GetChampionTanksMostDamage(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "tankiest_champ")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //deadliest_champ
        answer = PickemsAnalyser.GetChampionDealtMostDamage(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "deadliest_champ")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //MostDeathsChampion
        answer = PickemsAnalyser.GetMostDeathsChampion(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "MostDeathsChampion")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //long_games
        answer = PickemsAnalyser.GetGamesLongerThan45Minutes(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "long_games")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //obj_steals_ovr
        answer = PickemsAnalyser.GetTotalObjectiveSteals(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "obj_steals_ovr")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //pentakill_count
        answer = PickemsAnalyser.GetTotalPentakills(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "pentakill_count")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //short_game

        var startAnswer = PickemsAnalyser.GetShortestGameDuration(matches);
        if (startAnswer < 20)
        {
            answer = "15-20";
        }
        else if (startAnswer < 30)
        {
            answer = "21-30";
        }
        else if (startAnswer < 40)
        {
            answer = "31-40";
        }
        else if (startAnswer < 50)
        {
            answer = "41-50";
        }
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "short_game")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //gold_diff
        answer = PickemsAnalyser.GetBiggestGoldDifference(matches);
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "gold_diff")?.Value;
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //finals_champ
        var raw = Environment.GetEnvironmentVariable("finals_champ");
        if (!string.IsNullOrWhiteSpace(raw))
        {
            var champlist = JsonSerializer.Deserialize<string[]>(raw);
            foreach (var profile in profilePickems)
            {
                var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "finals_champ")?.Value;
                if (champlist.Contains(guess))
                {
                    profile.Score += 1;
                }
            }
        }

        //finals_winner
        answer = Environment.GetEnvironmentVariable("finals_winner");
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "finals_winner")?.Value;
            if (string.IsNullOrWhiteSpace(guess))
            {
                continue;
            }
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //most_mvps
        answer = Environment.GetEnvironmentVariable("most_mvps");
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "most_mvps")?.Value;
            if (string.IsNullOrWhiteSpace(guess))
            {
                continue;
            }
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //nemi_flashes
        answer = Environment.GetEnvironmentVariable("nemi_flashes");
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "nemi_flashes")?.Value;
            if (string.IsNullOrWhiteSpace(guess))
            {
                continue;
            }
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //bard_lane
        answer = Environment.GetEnvironmentVariable("bard_lane");
        foreach (var profile in profilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "bard_lane")?.Value;
            if (string.IsNullOrWhiteSpace(guess))
            {
                continue;
            }
            if (guess == answer)
            {
                profile.Score += 1;
            }
        }

        //finals_champ
        var reviveRaw = Environment.GetEnvironmentVariable("finals_champ");
        if (!string.IsNullOrWhiteSpace(raw))
        {
            var revivelist = JsonSerializer.Deserialize<string[]>(reviveRaw);
            foreach (var profile in profilePickems)
            {
                var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == "revived_champ")?.Value;
                if (revivelist.Contains(guess))
                {
                    profile.Score += 1;
                }
            }
        }

        string scores = "";
        foreach (var profile in profilePickems)
        {
            scores += $"UPDATE profiles SET pickems_score = {profile.Score} where id = {profile.Id};";
        }

        await DatabaseHelper.ExecuteUpdateAsync(scores);
        Console.WriteLine("Scores updated in database");
    }
}
