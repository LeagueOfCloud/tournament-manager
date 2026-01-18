namespace pickems_evaluator.Models.RiotApi;

public class Match
{
    public int Id { get; set; }
    public int GameDuration { get; set; }
    public List<Participant> Participants { get; set; } = new();
    public List<Team> Teams { get; set; } = new();
    public int MvpParticipantId { get; set; }
}