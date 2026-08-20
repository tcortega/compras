using Api.Features.Items.Models;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Items.Endpoints;

[Handler]
[MapGet("/api/items")]
public static partial class ListItems
{
	public sealed record Command : PageRequest
	{
		[FromQuery]
		public string? Q { get; init; }

		[FromQuery]
		public Guid? ContratacaoId { get; init; }

		[FromQuery]
		public Guid? FornecedorId { get; init; }

		[FromQuery]
		public Guid? OrgaoId { get; init; }

		[FromQuery]
		public string? Catmat { get; init; }

		[FromQuery]
		public string? Uf { get; init; }

		[FromQuery]
		public string? Quarter { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	public sealed record Response
	{
		public required IReadOnlyList<ItemRecord> Items { get; init; }

		public required Coverage Coverage { get; init; }
	}

	private static async ValueTask<Response> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var rows = db.Items.AsNoTracking().Visible();
		if (command.Q is { Length: > 0 } q)
			rows = rows.Where(i => i.Descricao.Contains(q) || (i.Catmat != null && i.Catmat.Contains(q)));

		if (command.ContratacaoId is { } contratacaoId)
			rows = rows.Where(i => i.ContratacaoId == contratacaoId);
		if (command.FornecedorId is { } fornecedorId)
			rows = rows.Where(i => i.FornecedorId == fornecedorId);
		if (command.OrgaoId is { } orgaoId)
			rows = rows.Where(i => i.Contratacao.OrgaoId == orgaoId);
		if (command.Catmat is { Length: > 0 } catmat)
			rows = rows.Where(i => i.Catmat == catmat);
		if (command.Uf is { Length: > 0 } uf)
			rows = rows.Where(i => i.Uf == uf);
		if (command.Quarter is { Length: > 0 } quarter)
			rows = rows.Where(i => i.Quarter == quarter);
		if (command.MethodologyVersion is { Length: > 0 })
			rows = rows.Where(i => i.MethodologyVersion == methodology);

		var n = await rows.CountAsync(ct);
		var items = await rows
			.OrderBy(i => i.Descricao)
			.ThenBy(i => i.Id)
			.SkipTake(command)
			.Select(ItemRecord.Project(rows))
			.ToListAsync(ct);

		return new()
		{
			Items = items,
			Coverage = Slice.Page(n, command.Uf, command.Quarter, methodology),
		};
	}
}
