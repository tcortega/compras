namespace Api.Features.Shared;

public sealed record Coverage
{
	public required int N { get; init; }

	public required string Uf { get; init; }

	public required string Quarter { get; init; }

	public required string MethodologyVersion { get; init; }
}
