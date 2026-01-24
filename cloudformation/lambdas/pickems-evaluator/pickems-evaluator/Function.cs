using Amazon.Lambda.Core;
using pickems_evaluator.Data;
using pickems_evaluator.Models.Database;
using pickems_evaluator.Models.RiotApi;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace pickems_evaluator;

public class Function
{

    public const string tournementMatchesQuery = "SELECT * FROM tournament_matches";
    public const string teamQuery = "SELECT team_id from players p join riot_accounts ra on p.id = ra.player_id where account_puuid =";
    public const string profileQuery = "SELECT id FROM profiles";
    public const string pickemsQuery = "SELECT * FROM pickems where user =";

    public async Task<Dictionary<string, string>> FunctionHandler(object input, ILambdaContext context)
    {
        var output = new Dictionary<string, string>();
        Console.WriteLine("Start");
        var DBmatches = await DatabaseHelper.ExecuteQueryAsync<TournementMatch>(tournementMatchesQuery, reader => new TournementMatch
        {
            Id = (int)reader["id"],
            WinnerTeamId = (int)reader["winner_team_id"],
            TournementMatchId = reader["tournament_match_id"].ToString(),
        });

        Console.WriteLine("Collected macthes");

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

        output["MostFirstBloods"] = PickemsAnalyser.GetMostFirstBloods(matches);
        output["HighestKDAPlayer"] = PickemsAnalyser.GetHighestKDAPlayer(matches);
        output["MostDeathsPlayer"] = PickemsAnalyser.GetMostDeathsPlayer(matches);
        output["WorstVisionScorePlayer"] = PickemsAnalyser.GetWorstVisionScorePlayer(matches);
        output["MostCSInSingleGame"] = PickemsAnalyser.GetMostCSInSingleGame(matches);

        output["MostKillsTeam"] = PickemsAnalyser.GetMostKillsTeam(matches);
        output["MostObjectivesTeam"] = PickemsAnalyser.GetMostObjectivesTeam(matches);
        output["MostDeathsTeam"] = PickemsAnalyser.GetMostDeathsTeam(matches);
        output["MostStructureDamageInSingleGame"] = PickemsAnalyser.GetMostStructureDamageInSingleGame(matches);
        output["MostPingsInSingleGame"] = PickemsAnalyser.GetMostPingsInSingleGame(matches);

        output["MostBannedChampion"] = PickemsAnalyser.GetMostBannedChampion(matches);
        output["ChampionTanksMostDamage"] = PickemsAnalyser.GetChampionTanksMostDamage(matches);
        output["ChampionDealtMostDamage"] = PickemsAnalyser.GetChampionDealtMostDamage(matches);
        output["MostDeathsChampion"] = PickemsAnalyser.GetMostDeathsChampion(matches);

        output["GamesLongerThan45Minutes"] = PickemsAnalyser.GetGamesLongerThan45Minutes(matches);
        output["TotalObjectiveSteals"] = PickemsAnalyser.GetTotalObjectiveSteals(matches);
        output["TotalPentakills"] = PickemsAnalyser.GetTotalPentakills(matches);
        output["ShortestGameDuration"] = PickemsAnalyser.GetShortestGameDuration(matches);
        output["BiggestGoldDifference"] = PickemsAnalyser.GetBiggestGoldDifference(matches);

        var profiles = await DatabaseHelper.ExecuteQueryAsync<int>(profileQuery, reader => (int)reader["id"]);

        foreach (var profileId in profiles)
        {
            var pickems = await DatabaseHelper.ExecuteQueryAsync<Pickems>($"{pickemsQuery}{profileId}", reader => new Pickems
            {
                Id = reader["id"].ToString(),
                PickemId = reader["pickem_id"].ToString(),
                Value = reader["value"].ToString(),
            });

            int profileScore = 0;
            foreach (var pickem in pickems)
            {
                if (output.TryGetValue(pickem.PickemId, out var correctAnswer))
                {
                    if (correctAnswer == pickem.Value)
                    {
                        profileScore++;
                    }
                }
            }

            Console.WriteLine($"Profile{profileId} Scored {profileScore}");
        }

        return output;
    }
}
