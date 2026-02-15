using pickems_evaluator.Models;
using pickems_evaluator.Models.Database;

namespace pickems_evaluator;

public class PickemAnswerHelper
{
    List<PickemAnswers> TournamentConfig;

    List<Profile> ProfilePickems;

    Dictionary<string, string> PlayerIdToPuuid;

    public PickemAnswerHelper(List<PickemAnswers> tournamentConfig, List<Profile> profilePickems, Dictionary<string, string> playerIdToPuuid)
    {
        TournamentConfig = tournamentConfig;
        ProfilePickems = profilePickems;
        PlayerIdToPuuid = playerIdToPuuid;
    }

    public void ScorePlayerPickem(string id, string answer)
    {
        var cfg = TournamentConfig.First(x => x.Id == id);
        var score = cfg.Score;

        foreach (var profile in ProfilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == id)?.Value;

            if (!string.IsNullOrEmpty(guess) &&
                PlayerIdToPuuid.TryGetValue(guess, out var puuid) &&
                puuid == answer)
            {
                profile.Score += score;
            }
        }

        TournamentConfig.RemoveAll(x => x.Id == id);
    }

    public void ScoreSimplePickem(string id, string answer)
    {
        var cfg = TournamentConfig.FirstOrDefault(x => x.Id == id);
        if (cfg is null)
        {
            return;
        }
        var score = cfg.Score;

        foreach (var profile in ProfilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == id)?.Value;
            if (!string.IsNullOrWhiteSpace(guess) && guess.ToLower() == answer.ToLower())
            {
                profile.Score += score;
            }
        }

        TournamentConfig.RemoveAll(x => x.Id == id);
    }


    public void ScorePickemFromConfigAnswer(string id)
    {
        var cfg = TournamentConfig.First(x => x.Id == id);
        if (cfg == null || string.IsNullOrWhiteSpace(cfg.Answer))
        {
            TournamentConfig.RemoveAll(x => x.Id == id); return;
        }
        var score = cfg.Score;
        var answers = cfg.Answer.Split(',');

        foreach (var profile in ProfilePickems)
        {
            var guess = profile.Pickems.FirstOrDefault(p => p.PickemId == id)?.Value;
            if (!string.IsNullOrWhiteSpace(guess) && answers.Contains(guess.ToLower()))
            {
                profile.Score += score;
            }
        }

        TournamentConfig.RemoveAll(x => x.Id == id);
    }
}