using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags/{id}/notify")]
public static partial class NotifyFlag
{
	public sealed record Command
	{
		[FromRoute]
		public required Guid Id { get; init; }
	}

	private static async ValueTask<FlagRecord> HandleAsync(
		[AsParameters] Command command,
		ApplicationDbContext db,
		IClock clock,
		CancellationToken ct)
	{
		var flag = await db.Flags.FirstOrDefaultAsync(f => f.Id == command.Id, ct);
		if (flag is null)
			NotFoundException.ThrowNotFoundException("Flag");
		flag.Notify(clock.GetCurrentInstant());
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
