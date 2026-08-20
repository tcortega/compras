using Api.Features.Publication.Models;
using Api.Infrastructure.Startup;
using Api.Persistence.Entities;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapGet("/api/internal/flags")]
public static partial class ListFlags
{
	public sealed record Command : PageRequest
	{
		[FromQuery]
		public string? Kind { get; init; }

		[FromQuery]
		public string? State { get; init; }

		[FromQuery]
		public Guid? ItemId { get; init; }
	}

	private static async ValueTask<PageResult<FlagRecord>> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(requested: null, options);
		var rows = db.Flags.AsNoTracking();
		if (command.Kind is { Length: > 0 } kind)
			rows = rows.Where(f => f.Kind == kind);
		if (ParseState(command.State) is { } state)
			rows = rows.Where(f => f.State == state);
		if (command.ItemId is { } itemId)
			rows = rows.Where(f => f.ItemId == itemId);

		var n = await rows.CountAsync(ct);
		var items = await rows
			.OrderBy(f => f.Kind)
			.ThenBy(f => f.ItemId)
			.ThenBy(f => f.Id)
			.SkipTake(command)
			.Select(FlagRecord.Project())
			.ToListAsync(ct);

		return Slice.Result(items, n, uf: null, quarter: null, methodology);
	}

	private static FlagState? ParseState(string? raw)
	{
		if (raw is not { Length: > 0 })
			return null;

		foreach (var member in Enum.GetValues<FlagState>())
		{
			if (string.Equals(ClosedSet.Format(member), raw, StringComparison.Ordinal)
				|| string.Equals(member.ToString(), raw, StringComparison.OrdinalIgnoreCase))
				return member;
		}

		BadRequestException.ThrowBadRequestException("Request is invalid");
		return null;
	}
}
