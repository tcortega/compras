using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags/{id}/reply")]
public static partial class ReplyFlag
{
	public sealed record Command
	{
		[FromRoute]
		public required Guid Id { get; init; }

		[FromBody]
		public required ReplyBody Body { get; init; }

		public sealed record ReplyBody
		{
			public required string ReplyText { get; init; }
		}
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
		flag.Reply(command.Body.ReplyText, clock.GetCurrentInstant());
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
