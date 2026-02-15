namespace pickems_evaluator.Models.RiotApi;

public class Team
{
    public int TeamId { get; set; }
    public List<int> Bans { get; set; } = new();
}