using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags/{id}/retract")]
public static partial class RetractFlag
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
		flag.Retract();
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
