using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags/{id}/notify")]
public static partial class NotifyFlag
{
	public sealed record Command
	{
		[FromRoute]
		public required Guid Id { get; init; }

		[FromBody(EmptyBodyBehavior = EmptyBodyBehavior.Allow)]
		public NotifyBody? Body { get; init; }

		public sealed record NotifyBody
		{
			public string? Artifact { get; init; }
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
		flag.Notify(clock.GetCurrentInstant(), command.Body?.Artifact);
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
