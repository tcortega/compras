namespace Api.Infrastructure.Search;

public interface IMeiliClient
{
	bool IsConfigured { get; }

	Task<MeiliSearchOutcome> SearchAsync(string q, string kind, int skip, int take, CancellationToken ct);
}

public sealed record MeiliHit
{
	public required Guid EntityId { get; init; }

	public required string Kind { get; init; }

	public required string Text { get; init; }
}

public sealed record MeiliSearchOutcome
{
	public static MeiliSearchOutcome Unset { get; } = new() { Status = MeiliStatus.Unset, Hits = [] };

	public static MeiliSearchOutcome Unavailable { get; } = new() { Status = MeiliStatus.Unavailable, Hits = [] };

	public required MeiliStatus Status { get; init; }

	public required IReadOnlyList<MeiliHit> Hits { get; init; }

	public int EstimatedTotal { get; init; }
}

public enum MeiliStatus
{
	Unset,
	Unavailable,
	Ready,
}
