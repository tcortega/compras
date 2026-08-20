using Api.Features.Orgaos.Models;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Orgaos.Endpoints;

[Handler]
[MapGet("/api/orgaos")]
public static partial class ListOrgaos
{
	public sealed record Command : PageRequest
	{
		[FromQuery]
		public string? Q { get; init; }

		[FromQuery]
		public Entity.Esfera? Esfera { get; init; }

		[FromQuery]
		public string? Uf { get; init; }

		[FromQuery]
		public string? MunicipioIbge { get; init; }

		[FromQuery]
		public string? Quarter { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	private static async ValueTask<PageResult<OrgaoRecord>> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var rows = db.Orgaos.AsNoTracking().Visible();
		if (command.Q is { Length: > 0 } q)
			rows = rows.Where(o => o.RazaoSocial.Contains(q) || o.Cnpj.Contains(q));

		if (command.Esfera is { } esfera)
			rows = rows.Where(o => o.Esfera == esfera);
		if (command.Uf is { Length: > 0 } uf)
			rows = rows.Where(o => o.Uf == uf);
		if (command.MunicipioIbge is { Length: > 0 } ibge)
			rows = rows.Where(o => o.MunicipioIbge == ibge);

		var n = await rows.CountAsync(ct);
		var items = await rows
			.OrderBy(o => o.RazaoSocial)
			.ThenBy(o => o.Id)
			.SkipTake(command)
			.Select(OrgaoRecord.Project(command.Quarter, methodology))
			.ToListAsync(ct);

		return Slice.Result(items, n, command.Uf, command.Quarter, methodology);
	}
}
