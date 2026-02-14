using pickems_evaluator.Models.Database;

namespace pickems_evaluator.Models
{
    public class Profile
    {
        public int Id { get; set; }
        public List<PickemsGuess> Pickems { get; set; } = new();
        public int Score { get; set; }
    }
}