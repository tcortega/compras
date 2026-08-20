using Api.Features.Contratacoes.Models;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Contratacoes.Endpoints;

[Handler]
[MapGet("/api/contratacoes")]
public static partial class ListContratacoes
{
	public sealed record Command : PageRequest
	{
		[FromQuery]
		public string? Q { get; init; }

		[FromQuery]
		public Guid? OrgaoId { get; init; }

		[FromQuery]
		public int? Ano { get; init; }

		[FromQuery]
		public string? Modalidade { get; init; }

		[FromQuery]
		public string? Uf { get; init; }

		[FromQuery]
		public string? Quarter { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	public sealed record Response
	{
		public required IReadOnlyList<ContratacaoRecord> Items { get; init; }

		public required Coverage Coverage { get; init; }
	}

	private static async ValueTask<Response> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var rows = db.Contratacoes.AsNoTracking().Visible();
		if (command.Q is { Length: > 0 } q)
			rows = rows.Where(c => c.Objeto.Contains(q) || c.PncpId.Contains(q));

		if (command.OrgaoId is { } orgaoId)
			rows = rows.Where(c => c.OrgaoId == orgaoId);
		if (command.Ano is { } ano)
			rows = rows.Where(c => c.Ano == ano);
		if (command.Modalidade is { Length: > 0 } modalidade)
			rows = rows.Where(c => c.Modalidade == modalidade);
		if (command.Uf is { Length: > 0 } uf)
			rows = rows.Where(c => c.Orgao.Uf == uf);
		if (command.MethodologyVersion is { Length: > 0 })
			rows = rows.Where(c => c.MethodologyVersion == methodology);

		var n = await rows.CountAsync(ct);
		var items = await rows
			.OrderByDescending(c => c.PublicadoEm)
			.ThenBy(c => c.Id)
			.SkipTake(command)
			.Select(ContratacaoRecord.Project())
			.ToListAsync(ct);

		return new()
		{
			Items = items,
			Coverage = Slice.Page(n, command.Uf, command.Quarter, methodology),
		};
	}
}
