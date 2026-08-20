using Api.Features.Fornecedores.Models;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Fornecedores.Endpoints;

[Handler]
[MapGet("/api/fornecedores")]
public static partial class ListFornecedores
{
	public sealed record Command : PageRequest
	{
		[FromQuery]
		public string? Q { get; init; }

		[FromQuery]
		public string? Cnae { get; init; }

		[FromQuery]
		public string? Uf { get; init; }

		[FromQuery]
		public string? Quarter { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	private static async ValueTask<PageResult<FornecedorRecord>> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var rows = db.Fornecedores.AsNoTracking().Visible();
		if (command.Q is { Length: > 0 } q)
			rows = rows.Where(f => f.RazaoSocial.Contains(q) || f.Cnpj.Contains(q));

		if (command.Cnae is { Length: > 0 } cnae)
			rows = rows.Where(f => f.Cnae == cnae);

		var n = await rows.CountAsync(ct);
		var items = await rows
			.OrderBy(f => f.RazaoSocial)
			.ThenBy(f => f.Id)
			.SkipTake(command)
			.Select(FornecedorRecord.Project(command.Uf, command.Quarter, methodology))
			.ToListAsync(ct);

		return Slice.Result(items, n, command.Uf, command.Quarter, methodology);
	}
}
