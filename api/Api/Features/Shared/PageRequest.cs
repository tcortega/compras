using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Shared;

public record PageRequest
{
	public const int DefaultTake = 50;

	public const int MaxTake = 500;

	[FromQuery]
	public int? Skip { get; init; }

	[FromQuery]
	public int? Take { get; init; }
}

public sealed record PageResult<T>
{
	public required IReadOnlyList<T> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public int Total => Coverage.N;
}
