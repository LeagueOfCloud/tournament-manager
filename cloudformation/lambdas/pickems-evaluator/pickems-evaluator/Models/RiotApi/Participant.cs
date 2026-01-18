namespace pickems_evaluator.Models.RiotApi;

public class Participant
{
    public string ParticipantId { get; set; }
    public int TeamId { get; set; }
    public int ChampionId { get; set; }
    public int Kills { get; set; }
    public int Deaths { get; set; }
    public int Assists { get; set; }
    public bool FirstBloodKill { get; set; }
    public int VisionScore { get; set; }
    public int TotalMinionsKilled { get; set; }
    public int NeutralMinionsKilled { get; set; }
    public int TotalDamageTaken { get; set; }
    public int TotalDamageDealtToChampions { get; set; }
    public int DamageDealtToBuildings { get; set; }
    public int DamageDealtToTurrets { get; set; }
    public int DragonKills { get; set; }
    public int BaronKills { get; set; }
    public int RiftHeraldKills { get; set; }
    public int InhibitorKills { get; set; }
    public int TurretKills { get; set; }
    public int VoidMonsterKill { get; set; }
    public int ObjectivesStolen { get; set; }
    public int GoldEarned { get; set; }
    public int PentaKills { get; set; }
    public int Pings { get; set; }
}