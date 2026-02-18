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

    const string tournamentMatchesQuery = "SELECT * FROM tournament_matches";
    const string tournamentConfigQuery = "SELECT * FROM config where name = 'pickem_categories' ";
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
        var DBmatches = await DatabaseHelper.ExecuteQueryAsync<TournementMatch>(tournamentMatchesQuery, reader => new TournementMatch
        {
            Id = (int)reader["id"],
            WinnerTeamId = (int)reader["winner_team_id"],
            TournementMatchId = reader["tournament_match_id"].ToString(),
        });

        var dbTournementConfig = (await DatabaseHelper.ExecuteQueryAsync<string>(tournamentConfigQuery, reader => reader["value"].ToString()))[0];
        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        var tournamentConfig = JsonSerializer.Deserialize<List<PickemAnswers>>(dbTournementConfig, options);
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
            var pickems = await DatabaseHelper.ExecuteQueryAsync<PickemsGuess>($"{pickemsQuery}{profile}", reader => new PickemsGuess
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

        if(tournamentConfig is null || tournamentConfig.Count == 0)
        {
            Console.WriteLine("Pickems Config is null or empty please check its correctly set up in the DB");
            return;
        }

        if (profilePickems is null || profilePickems.Count == 0)
        {
            Console.WriteLine("No pickems guess to use skipping evaluation");
            return;
        }

        if (playerIdToPuuid is null || playerIdToPuuid.Count == 0)
        {
            Console.WriteLine("Error collecting playerIds check RiotAPi config");
            return;
        }

        PickemAnswerHelper pickemsAnswerHelper = new PickemAnswerHelper(tournamentConfig, profilePickems, playerIdToPuuid);

        pickemsAnswerHelper.ScorePlayerPickem("most_fb", PickemsAnalyser.GetMostFirstBloods(matches));

        pickemsAnswerHelper.ScorePlayerPickem("highest_kda", PickemsAnalyser.GetHighestKDAPlayer(matches));

        pickemsAnswerHelper.ScorePlayerPickem("most_deaths_player", PickemsAnalyser.GetMostDeathsPlayer(matches));

        pickemsAnswerHelper.ScorePlayerPickem("tunnel_vision", PickemsAnalyser.GetWorstVisionScorePlayer(matches));

        pickemsAnswerHelper.ScorePlayerPickem("most_cs", PickemsAnalyser.GetMostCSInSingleGame(matches));

        pickemsAnswerHelper.ScoreSimplePickem("most_kills_team", PickemsAnalyser.GetMostKillsTeam(matches));

        pickemsAnswerHelper.ScoreSimplePickem("most_objs_team", PickemsAnalyser.GetMostObjectivesTeam(matches));

        pickemsAnswerHelper.ScoreSimplePickem("most_deaths_team", PickemsAnalyser.GetMostDeathsTeam(matches));

        pickemsAnswerHelper.ScoreSimplePickem("demolish_team", PickemsAnalyser.GetMostStructureDamageInSingleGame(matches));

        pickemsAnswerHelper.ScoreSimplePickem("team_pings", PickemsAnalyser.GetMostPingsInSingleGame(matches));

        pickemsAnswerHelper.ScoreSimplePickem("most_banned", championIdToName[PickemsAnalyser.GetMostBannedChampion(matches)]);

        pickemsAnswerHelper.ScoreSimplePickem("tankiest_champ", PickemsAnalyser.GetChampionTanksMostDamage(matches));

        pickemsAnswerHelper.ScoreSimplePickem("deadliest_champ", PickemsAnalyser.GetChampionDealtMostDamage(matches));

        pickemsAnswerHelper.ScoreSimplePickem("long_games", PickemsAnalyser.GetGamesLongerThan45Minutes(matches));

        pickemsAnswerHelper.ScoreSimplePickem("obj_steals_ovr", PickemsAnalyser.GetTotalObjectiveSteals(matches));

        pickemsAnswerHelper.ScoreSimplePickem("pentakill_count", PickemsAnalyser.GetTotalPentakills(matches));

        var shortestDuration = PickemsAnalyser.GetShortestGameDuration(matches);
        string shortGameAnswer;
        if (shortestDuration < 20)
        {
            shortGameAnswer = "15-20";
        }
        else if (shortestDuration < 30)
        {
            shortGameAnswer = "21-30";
        }
        else if (shortestDuration < 40)
        {
            shortGameAnswer = "31-40";
        }
        else
        {
            shortGameAnswer = "41-50";
        }
        pickemsAnswerHelper.ScoreSimplePickem("short_game", shortGameAnswer);

        pickemsAnswerHelper.ScoreSimplePickem("gold_diff", PickemsAnalyser.GetBiggestGoldDifference(matches));

        foreach (var cfg in tournamentConfig.ToList())
        {
            pickemsAnswerHelper.ScorePickemFromConfigAnswer(cfg.Id);
        }

        string scores = "";
        foreach (var profile in profilePickems)
        {
            scores += $"UPDATE profiles SET pickems_score = {profile.Score} where id = {profile.Id};";
        }

        string pickemsAnswers = "";
        foreach (var answer in PickemAnswerHelper.PickemAnswers)
        {
            pickemsAnswers += $"INSERT INTO pickems_answers (id, answer) VALUES ('{answer.Key}', '{answer.Value}');";
        }

        await DatabaseHelper.ExecuteUpdateAsync(scores);
        if (!string.IsNullOrEmpty(pickemsAnswers))
        {
            await DatabaseHelper.ExecuteUpdateAsync(pickemsAnswers);
        }
        Console.WriteLine("Scores updated in database");
    }
}