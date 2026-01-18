using Amazon.Lambda.Core;
using pickems_evaluator.Data;
using pickems_evaluator.Models.Database;
using pickems_evaluator.Models.RiotApi;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace pickems_evaluator;

public class PickemsOutput
{
    public Dictionary<string, object> PlayerStats { get; set; } = new();
    public Dictionary<string, object> TeamStats { get; set; } = new();
    public Dictionary<string, object> ChampionStats { get; set; } = new();
    public Dictionary<string, object> GameStats { get; set; } = new();
}

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
    public async Task<PickemsOutput> FunctionHandler(string input, ILambdaContext context)
    {
        var output = new PickemsOutput();

        var DBmatches = await DatabaseHelper.ExecuteQueryAsync<TournementMatch>(tournementMatchesQuery, reader => new TournementMatch
        {
            Id = (int)reader["id"],
            WinnerTeamId = (int)reader["winner_team_id"],
            TournementMatchId = reader["tournament_match_id"].ToString(),
        });

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

        output.PlayerStats["MostFirstBloods"] = PickemsAnalyzer.GetMostFirstBloods(matches);
        output.PlayerStats["HighestKDAPlayer"] = PickemsAnalyzer.GetHighestKDAPlayer(matches);
        output.PlayerStats["MostDeathsPlayer"] = PickemsAnalyzer.GetMostDeathsPlayer(matches);
        output.PlayerStats["WorstVisionScorePlayer"] = PickemsAnalyzer.GetWorstVisionScorePlayer(matches);
        output.PlayerStats["MostCSInSingleGame"] = PickemsAnalyzer.GetMostCSInSingleGame(matches);

        output.TeamStats["MostKillsTeam"] = PickemsAnalyzer.GetMostKillsTeam(matches);
        output.TeamStats["MostObjectivesTeam"] = PickemsAnalyzer.GetMostObjectivesTeam(matches);
        output.TeamStats["MostDeathsTeam"] = PickemsAnalyzer.GetMostDeathsTeam(matches);
        output.TeamStats["MostStructureDamageInSingleGame"] = PickemsAnalyzer.GetMostStructureDamageInSingleGame(matches);
        output.TeamStats["MostPingsInSingleGame"] = PickemsAnalyzer.GetMostPingsInSingleGame(matches);

        output.ChampionStats["MostBannedChampion"] = PickemsAnalyzer.GetMostBannedChampion(matches);
        output.ChampionStats["ChampionTanksMostDamage"] = PickemsAnalyzer.GetChampionTanksMostDamage(matches);
        output.ChampionStats["ChampionDealtMostDamage"] = PickemsAnalyzer.GetChampionDealtMostDamage(matches);
        output.ChampionStats["MostDeathsChampion"] = PickemsAnalyzer.GetMostDeathsChampion(matches);

        output.GameStats["GamesLongerThan45Minutes"] = PickemsAnalyzer.GetGamesLongerThan45Minutes(matches);
        output.GameStats["TotalObjectiveSteals"] = PickemsAnalyzer.GetTotalObjectiveSteals(matches);
        output.GameStats["TotalPentakills"] = PickemsAnalyzer.GetTotalPentakills(matches);
        output.GameStats["ShortestGameDuration"] = PickemsAnalyzer.GetShortestGameDuration(matches);
        output.GameStats["BiggestGoldDifference"] = PickemsAnalyzer.GetBiggestGoldDifference(matches);

        return output;
    }
}
