using System.Text.Json;
using pickems_evaluator.Models.RiotApi;

namespace pickems_evaluator.Data;

public static class RiotApiHelper
{
    public static async Task<Match> FetchMatchDataAsync(string matchId)
    {
        string region = "europe";
        string apiKey = Environment.GetEnvironmentVariable("RIOT_API_KEY");

        string url = $"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}";

        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-Riot-Token", apiKey);

        var response = await client.GetAsync(url);

        if ((int)response.StatusCode == 429)
            throw new Exception("Rate limited by Riot API");

        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        return ParseMatchData(json);
    }

    private static Match ParseMatchData(string json)
    {
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;
        var info = root.GetProperty("info");
        var teams = info.GetProperty("teams");

        var match = new Match
        {
            GameDuration = info.GetProperty("gameDuration").GetInt32(),
            Participants = ParseParticipants(info.GetProperty("participants")),
            Teams = ParseTeams(teams),
        };

        return match;
    }

    private static List<Participant> ParseParticipants(JsonElement participantsElement)
    {
        var participants = new List<Participant>();

        foreach (var participantElement in participantsElement.EnumerateArray())
        {
            var challenges = participantElement.GetProperty("challenges");
            var participant = new Participant
            {
                ParticipantId = participantElement.GetProperty("puuid").ToString(),
                TeamId = participantElement.GetProperty("teamId").GetInt32(),
                ChampionId = participantElement.GetProperty("championId").GetInt32(),
                FirstBloodKill = participantElement.GetProperty("firstBloodKill").GetBoolean(),
                Kills = participantElement.GetProperty("kills").GetInt32(),
                Deaths = participantElement.GetProperty("deaths").GetInt32(),
                Assists = participantElement.GetProperty("assists").GetInt32(),
                VisionScore = participantElement.GetProperty("visionScore").GetInt32(),
                TotalMinionsKilled = participantElement.GetProperty("totalMinionsKilled").GetInt32(),
                NeutralMinionsKilled = participantElement.GetProperty("neutralMinionsKilled").GetInt32(),
                TotalDamageTaken = participantElement.GetProperty("totalDamageTaken").GetInt32(),
                TotalDamageDealtToChampions = participantElement.GetProperty("totalDamageDealtToChampions").GetInt32(),
                DamageDealtToBuildings = participantElement.GetProperty("damageDealtToBuildings").GetInt32(),
                DamageDealtToTurrets = participantElement.GetProperty("damageDealtToTurrets").GetInt32(),
                DragonKills = participantElement.GetProperty("dragonKills").GetInt32(),
                BaronKills = participantElement.GetProperty("baronKills").GetInt32(),
                RiftHeraldKills = challenges.GetProperty("teamRiftHeraldKills").GetInt32(),
                InhibitorKills = participantElement.GetProperty("inhibitorKills").GetInt32(),
                TurretKills = participantElement.GetProperty("turretKills").GetInt32(),
                ObjectivesStolen = participantElement.GetProperty("objectivesStolen").GetInt32(),
                GoldEarned = participantElement.GetProperty("goldEarned").GetInt32(),
                PentaKills = participantElement.GetProperty("pentaKills").GetInt32(),
                Pings = GetBasicPingsTotal(participantElement)
            };

            participants.Add(participant);
        }

        return participants;
    }

    private static List<Team> ParseTeams(JsonElement teamsElement)
    {
        var teams = new List<Team>();

        foreach (var teamElement in teamsElement.EnumerateArray())
        {
            List<int> bans = new List<int>();
            if (teamElement.TryGetProperty("bans", out var bansElement))
            { 
                foreach (var banElement in bansElement.EnumerateArray())
                {
                    bans.Add(banElement.GetProperty("championId").GetInt32());
                }
            }

            var team = new Team
            {
                TeamId = teamElement.GetProperty("teamId").GetInt32(),
                Bans = bans
            };

            teams.Add(team);
        }

        return teams;
    }

    private static int GetBasicPingsTotal(JsonElement participantElement)
    {
        int total = 0;

        if (participantElement.TryGetProperty("allInPings", out var allInPings))
            total += allInPings.GetInt32();
        if (participantElement.TryGetProperty("assistMePings", out var assistMePings))
            total += assistMePings.GetInt32();
        if (participantElement.TryGetProperty("basicPings", out var basicPings))
            total += basicPings.GetInt32();
        if (participantElement.TryGetProperty("commandPings", out var commandPings))
            total += commandPings.GetInt32();
        if (participantElement.TryGetProperty("dangerPings", out var dangerPings))
            total += dangerPings.GetInt32();
        if (participantElement.TryGetProperty("enemyMissingPings", out var enemyMissingPings))
            total += enemyMissingPings.GetInt32();
        if (participantElement.TryGetProperty("enemyVisionPings", out var enemyVisionPings))
            total += enemyVisionPings.GetInt32();
        if (participantElement.TryGetProperty("getBackPings", out var getBackPings))
            total += getBackPings.GetInt32();
        if (participantElement.TryGetProperty("holdPings", out var holdPings))
            total += holdPings.GetInt32();
        if (participantElement.TryGetProperty("needVisionPings", out var needVisionPings))
            total += needVisionPings.GetInt32();
        if (participantElement.TryGetProperty("onMyWayPings", out var onMyWayPings))
            total += onMyWayPings.GetInt32();
        if (participantElement.TryGetProperty("pushPings", out var pushPings))
            total += pushPings.GetInt32();
        if (participantElement.TryGetProperty("retreatPings", out var retreatPings))
            total += retreatPings.GetInt32();
        if (participantElement.TryGetProperty("visionClearedPings", out var visionClearedPings))
            total += visionClearedPings.GetInt32();

        return total;
    }
}