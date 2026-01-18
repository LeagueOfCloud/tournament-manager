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

    /// <summary>
    /// A simple function that takes a string and does a ToUpper
    /// </summary>
    /// <param name="input">The event for the Lambda function handler to process.</param>
    /// <param name="context">The ILambdaContext that provides methods for logging and describing the Lambda environment.</param>
    /// <returns></returns>
    public async void FunctionHandler(string input, ILambdaContext context)
    {
        var DBmatches = await DatabaseHelper.ExecuteQueryAsync<TournementMatch>(tournementMatchesQuery, reader => new TournementMatch
        {
            Id = (int)reader["id"],
            WinnerTeamId = (int)reader["winner_team_id"],
            TournementMatchId = reader["tournament_match_id"].ToString(),
        });

        Console.WriteLine($"Retrieved {DBmatches.Count} tournament matches");

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
            matches[matches.Count - 1].Participants[5].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[6].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[7].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[8].TeamId = team1Id[0];
            matches[matches.Count - 1].Participants[9].TeamId = team1Id[0];
        }


        Console.WriteLine($"Fetched {matches.Count} matches from Riot API\n");

        Console.WriteLine("=== Pickem's Output ===");

        Console.WriteLine("PLAYER STATS:");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostFirstBloods(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetHighestKDAPlayer(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostDeathsPlayer(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetWorstVisionScorePlayer(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostCSInSingleGame(matches)}");

        Console.WriteLine("\nTEAM STATS:");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostKillsTeam(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostObjectivesTeam(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostDeathsTeam(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostStructureDamageInSingleGame(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostPingsInSingleGame(matches)}");

        Console.WriteLine("\nCHAMPION STATS:");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostBannedChampion(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetChampionTanksMostDamage(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetChampionDealtMostDamage(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetMostDeathsChampion(matches)}");

        Console.WriteLine("\nGAME STATS:");
        Console.WriteLine($"  {PickemsAnalyzer.GetGamesLongerThan45Minutes(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetTotalObjectiveSteals(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetTotalPentakills(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetShortestGameDuration(matches)}");
        Console.WriteLine($"  {PickemsAnalyzer.GetBiggestGoldDifference(matches)}");

    }
}
