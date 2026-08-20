using Api.Features.Busca.Models;
using Api.Features.Fornecedores.Models;
using Api.Features.Items.Models;
using Api.Features.Orgaos.Models;
using Api.Infrastructure.Search;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Busca.Endpoints;

[Handler]
[MapGet("/api/busca")]
public static partial class Search
{
	public sealed record Command : PageRequest
	{
		[FromQuery]
		public string? Q { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	private static async ValueTask<SearchPage> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IMeiliClient meili,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var sliceN = await db.Items.AsNoTracking().Visible().CountAsync(ct);
		var slice = Slice.Page(sliceN, uf: null, quarter: null, methodology);
		var empty = Empty(slice, meili.IsConfigured ? SearchPage.SourceMeilisearch : SearchPage.SourceUnset);
		if (command.Q is not { Length: > 0 } q)
			return empty with { Coverage = slice };

		if (!meili.IsConfigured)
			return Empty(slice, SearchPage.SourceUnset);

		var skip = command.Skip ?? 0;
		var take = command.Take ?? 5;
		var orgaoHits = await meili.SearchAsync(q, "orgao", skip, take, ct);
		var fornecedorHits = await meili.SearchAsync(q, "fornecedor", skip, take, ct);
		var itemHits = await meili.SearchAsync(q, "item", skip, take, ct);
		if (orgaoHits.Status == MeiliStatus.Unavailable
			|| fornecedorHits.Status == MeiliStatus.Unavailable
			|| itemHits.Status == MeiliStatus.Unavailable)
			return Empty(slice, SearchPage.SourceUnavailable);

		var orgaos = await HydrateOrgaos(db, orgaoHits, methodology, ct);
		var fornecedores = await HydrateFornecedores(db, fornecedorHits, methodology, ct);
		var items = await HydrateItems(db, itemHits, methodology, ct);
		return new()
		{
			Orgaos = orgaos,
			Fornecedores = fornecedores,
			Items = items,
			Coverage = Slice.Page(items.Coverage.N, uf: null, quarter: null, methodology),
			Source = SearchPage.SourceMeilisearch,
		};
	}

	private static SearchPage Empty(Coverage slice, string source) =>
		new()
		{
			Orgaos = Slice.Result<OrgaoRecord>([], 0, uf: null, quarter: null, slice.MethodologyVersion),
			Fornecedores = Slice.Result<FornecedorRecord>([], 0, uf: null, quarter: null, slice.MethodologyVersion),
			Items = Slice.Result<ItemRecord>([], 0, uf: null, quarter: null, slice.MethodologyVersion),
			Coverage = slice,
			Source = source,
		};

	private static async Task<PageResult<OrgaoRecord>> HydrateOrgaos(
		ApplicationDbContext db,
		MeiliSearchOutcome outcome,
		string methodology,
		CancellationToken ct)
	{
		var ids = outcome.Hits.Select(h => h.EntityId).ToList();
		var rows = ids.Count == 0
			? []
			: await db.Orgaos.AsNoTracking().Visible()
				.Where(o => ids.Contains(o.Id))
				.Select(OrgaoRecord.Project(null, methodology))
				.ToListAsync(ct);
		var byId = rows.ToDictionary(r => r.Id);
		var ordered = ids.Where(byId.ContainsKey).Select(id => byId[id]).ToList();
		return Slice.Result(ordered, outcome.EstimatedTotal, uf: null, quarter: null, methodology);
	}

	private static async Task<PageResult<FornecedorRecord>> HydrateFornecedores(
		ApplicationDbContext db,
		MeiliSearchOutcome outcome,
		string methodology,
		CancellationToken ct)
	{
		var ids = outcome.Hits.Select(h => h.EntityId).ToList();
		var rows = ids.Count == 0
			? []
			: await db.Fornecedores.AsNoTracking().Visible()
				.Where(f => ids.Contains(f.Id))
				.Select(FornecedorRecord.Project(null, null, methodology))
				.ToListAsync(ct);
		var byId = rows.ToDictionary(r => r.Id);
		var ordered = ids.Where(byId.ContainsKey).Select(id => byId[id]).ToList();
		return Slice.Result(ordered, outcome.EstimatedTotal, uf: null, quarter: null, methodology);
	}

	private static async Task<PageResult<ItemRecord>> HydrateItems(
		ApplicationDbContext db,
		MeiliSearchOutcome outcome,
		string methodology,
		CancellationToken ct)
	{
		var ids = outcome.Hits.Select(h => h.EntityId).ToList();
		var visible = db.Items.AsNoTracking().Visible();
		var rows = ids.Count == 0
			? []
			: await visible
				.Where(i => ids.Contains(i.Id))
				.Select(ItemRecord.Project(visible))
				.ToListAsync(ct);
		var byId = rows.ToDictionary(r => r.Id);
		var ordered = ids.Where(byId.ContainsKey).Select(id => byId[id]).ToList();
		return Slice.Result(ordered, outcome.EstimatedTotal, uf: null, quarter: null, methodology);
	}
}
