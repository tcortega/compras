using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/flags/{id}/publish")]
public static partial class PublishFlag
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
		var flag = await db.Flags
			.Include(f => f.Item)
			.ThenInclude(i => i.Contratacao)
			.ThenInclude(c => c.Orgao)
			.FirstOrDefaultAsync(f => f.Id == command.Id, ct);
		if (flag is null)
			NotFoundException.ThrowNotFoundException("Flag");
		if (flag.Item.Suspended || flag.Item.Contratacao.Suspended || flag.Item.Contratacao.Orgao.Suspended)
			ConflictException.ThrowConflictException("Entity is suspended.");
		flag.Publish(clock.GetCurrentInstant());
		await db.SaveChangesAsync(ct);
		return FlagRecord.FromEntity(flag);
	}
}
