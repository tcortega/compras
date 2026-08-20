using Api.Persistence.Entities;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapPost("/api/internal/suspend")]
public static partial class SuspendEntity
{
	public sealed record Command
	{
		public required SuspendKind Kind { get; init; }

		public required Guid Id { get; init; }
	}

	public sealed record Response
	{
		public required SuspendKind Kind { get; init; }

		public required Guid Id { get; init; }

		public required bool Suspended { get; init; }
	}

	private static async ValueTask<Response> HandleAsync(
		Command command,
		ApplicationDbContext db,
		CancellationToken ct)
	{
		var found = command.Kind switch
		{
			SuspendKind.Orgao => await SuspendAsync(db, db.Orgaos, command.Id, ct),
			SuspendKind.Fornecedor => await SuspendAsync(db, db.Fornecedores, command.Id, ct),
			SuspendKind.Contratacao => await SuspendAsync(db, db.Contratacoes, command.Id, ct),
			SuspendKind.Item => await SuspendAsync(db, db.Items, command.Id, ct),
			SuspendKind.Flag => await SuspendAsync(db, db.Flags, command.Id, ct),
			_ => false,
		};
		if (!found)
			NotFoundException.ThrowNotFoundException(command.Kind.ToString());

		return new()
		{
			Kind = command.Kind,
			Id = command.Id,
			Suspended = true,
		};
	}

	private static async Task<bool> SuspendAsync<T>(
		ApplicationDbContext db,
		DbSet<T> set,
		Guid id,
		CancellationToken ct)
		where T : class, ISuspendable
	{
		var row = await set.FindAsync([id], ct);
		if (row is null)
			return false;
		row.Suspended = true;
		await db.SaveChangesAsync(ct);
		return true;
	}
}
