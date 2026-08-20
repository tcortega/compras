using Api.Features.Publication.Models;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapGet("/api/internal/flags/{id}")]
public static partial class GetFlag
{
	public sealed record Command
	{
		public required Guid Id { get; init; }
	}

	private static async ValueTask<FlagRecord> HandleAsync(
		Command command,
		ApplicationDbContext db,
		CancellationToken ct)
	{
		var flag = await db.Flags.AsNoTracking().FirstOrDefaultAsync(f => f.Id == command.Id, ct);
		if (flag is not null)
			return FlagRecord.FromEntity(flag);
		NotFoundException.ThrowNotFoundException("Flag");
		return default!;
	}
}
