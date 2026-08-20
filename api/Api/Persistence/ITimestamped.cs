namespace Api.Persistence;

public interface ITimestamped
{
	Instant CreatedAt { get; }

	Instant UpdatedAt { get; set; }
}
