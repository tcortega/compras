using Api.Features.Publication.Models;
using Api.Persistence.Entities;
using Microsoft.AspNetCore.Http.HttpResults;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags")]
public static partial class CreateFlag
{
	internal static Created<FlagRecord> TransformResult(FlagRecord response) =>
		TypedResults.Created($"/api/internal/flags/{response.Id}", response);

	public sealed record Command
	{
		public required Guid ItemId { get; init; }

		public required string Kind { get; init; }

		public required string Delta { get; init; }

		public required string SourceUrl { get; init; }

		public required string SnapshotId { get; init; }

		public required string MethodologyVersion { get; init; }
	}

	private static async ValueTask<FlagRecord> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IClock clock,
		CancellationToken ct)
	{
		if (command.Kind is not { Length: > 0 }
			|| command.Delta is not { Length: > 0 }
			|| command.SourceUrl is not { Length: > 0 }
			|| command.SnapshotId is not { Length: > 0 }
			|| command.MethodologyVersion is not { Length: > 0 })
			BadRequestException.ThrowBadRequestException("Request is invalid");

		var item = await db.Items.FirstOrDefaultAsync(i => i.Id == command.ItemId, ct);
		if (item is null)
			NotFoundException.ThrowNotFoundException("Item");

		var now = clock.GetCurrentInstant();
		var flag = new Flag
		{
			Id = Guid.NewGuid(),
			ItemId = command.ItemId,
			Kind = command.Kind,
			State = FlagState.Detected,
			DetectedAt = now,
			Delta = command.Delta,
			SourceUrl = command.SourceUrl,
			SnapshotId = command.SnapshotId,
			MethodologyVersion = command.MethodologyVersion,
		};
		db.Flags.Add(flag);
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
