using Api.Features.Publication.Models;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Publication.Endpoints;

[Handler]
[MapGet("/api/internal/flags/{id}/audit")]
public static partial class ListFlagAudit
{
	public sealed record Command
	{
		[FromRoute]
		public required Guid Id { get; init; }
	}

	private static async ValueTask<FlagAuditPage> HandleAsync(
		[AsParameters] Command command,
		ApplicationDbContext db,
		CancellationToken ct)
	{
		var exists = await db.Flags.AsNoTracking().AnyAsync(f => f.Id == command.Id, ct);
		if (!exists)
			NotFoundException.ThrowNotFoundException("Flag");

		var sql = db.Database.IsSqlite()
			? """
			  SELECT CAST(id AS TEXT) AS Id,
			         CAST("flagId" AS TEXT) AS FlagId,
			         "fromState" AS FromState,
			         "toState" AS ToState,
			         CAST(at AS TEXT) AS At,
			         actor AS Actor,
			         reason AS Reason,
			         delta AS Delta
			  FROM flag_audit
			  WHERE "flagId" = {0}
			  ORDER BY at, id
			  """
			: """
			  SELECT id::text AS Id,
			         "flagId"::text AS FlagId,
			         "fromState" AS FromState,
			         "toState" AS ToState,
			         to_char(at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS At,
			         actor AS Actor,
			         reason AS Reason,
			         delta AS Delta
			  FROM flag_audit
			  WHERE "flagId" = {0}
			  ORDER BY at, id
			  """;

		var rows = await db.Database
			.SqlQueryRaw<FlagAuditSqlRow>(sql, command.Id)
			.ToListAsync(ct);

		return new()
		{
			Items = [.. rows.Select(r => r.ToRecord())],
		};
	}
}
