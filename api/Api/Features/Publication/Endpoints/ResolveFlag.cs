using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags/{id}/resolve")]
public static partial class ResolveFlag
{
	public sealed record Command
	{
		[FromRoute]
		public required Guid Id { get; init; }
	}

	private static async ValueTask<FlagRecord> HandleAsync(
		[AsParameters] Command command,
		ApplicationDbContext db,
		CancellationToken ct)
	{
		var flag = await db.Flags.FirstOrDefaultAsync(f => f.Id == command.Id, ct);
		if (flag is null)
			NotFoundException.ThrowNotFoundException("Flag");
		flag.Resolve();
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
