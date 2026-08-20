using Api.Features.Orgaos.Models;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Orgaos.Endpoints;

[Handler]
[MapGet("/api/orgaos/{id}")]
public static partial class GetOrgao
{
	public sealed record Command
	{
		public required Guid Id { get; init; }

		[FromQuery]
		public string? Quarter { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	private static async ValueTask<OrgaoRecord> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var row = await db.Orgaos.AsNoTracking()
			.Visible()
			.Where(o => o.Id == command.Id)
			.Select(OrgaoRecord.Project(command.Quarter, methodology))
			.FirstOrDefaultAsync(ct);
		if (row is not null)
			return row;
		NotFoundException.ThrowNotFoundException("Orgao");
		return default!;
	}
}
