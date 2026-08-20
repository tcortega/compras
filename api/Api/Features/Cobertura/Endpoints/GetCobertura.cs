using System.Globalization;
using Api.Infrastructure.Startup;
using Api.Persistence.Entities;

namespace Api.Features.Cobertura.Endpoints;

[Handler]
[MapGet("/api/cobertura")]
public static partial class GetCobertura
{
	private static readonly string[] s_sources =
	[
		"compras_gov",
		"receita_cnpj",
		"ocds",
		"pncp_consulta",
		"tce_sp",
		"tce_rs",
		"cgu_ceis_cnep",
	];

	public sealed record Command;

	public sealed record Municipio
	{
		public required string Nome { get; init; }

		public required string Uf { get; init; }

		public required string Ibge { get; init; }
	}

	public sealed record Municipios
	{
		public required int N { get; init; }

		public required IReadOnlyList<Municipio> Items { get; init; }
	}

	public sealed record YearCount
	{
		public required int Year { get; init; }

		public required int Compras { get; init; }

		public required int Items { get; init; }
	}

	public sealed record RowCounts
	{
		public required int Compras { get; init; }

		public required int Items { get; init; }

		public required IReadOnlyList<YearCount> PerYear { get; init; }
	}

	public sealed record SourceFreshness
	{
		public required string Name { get; init; }

		public Instant? LastUpdate { get; init; }

		public required int N { get; init; }
	}

	public sealed record Response
	{
		public required Municipios Municipios { get; init; }

		public required IReadOnlyList<int> Years { get; init; }

		public required RowCounts Rows { get; init; }

		public required decimal CatmatCoveragePercent { get; init; }

		public required int NCoded { get; init; }

		public required int NItems { get; init; }

		public required IReadOnlyList<SourceFreshness> Sources { get; init; }

		public required Coverage Coverage { get; init; }
	}

	private static async ValueTask<Response> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		_ = command;
		var methodology = Slice.Methodology(requested: null, options);
		var municipioRows = await db.Contratacoes.AsNoTracking()
			.Visible()
			.Select(c => new { c.Orgao.MunicipioNome, c.Orgao.Uf, c.Orgao.MunicipioIbge })
			.Distinct()
			.OrderBy(m => m.MunicipioNome)
			.ThenBy(m => m.MunicipioIbge)
			.ToListAsync(ct);
		var municipios = municipioRows
			.Select(m => new Municipio { Nome = m.MunicipioNome, Uf = m.Uf, Ibge = m.MunicipioIbge })
			.ToList();
		var years = await db.Contratacoes.AsNoTracking()
			.Visible()
			.Select(c => c.Ano)
			.Distinct()
			.OrderBy(y => y)
			.ToListAsync(ct);
		var comprasN = await db.Contratacoes.AsNoTracking().Visible().CountAsync(ct);
		var comprasYearRows = await db.Contratacoes.AsNoTracking()
			.Visible()
			.GroupBy(c => c.Ano)
			.Select(g => new { Year = g.Key, N = g.Count() })
			.ToListAsync(ct);
		var comprasByYear = comprasYearRows.ToDictionary(r => r.Year, r => r.N);
		var itemRows = await db.Items.AsNoTracking()
			.Visible()
			.Select(i => new { i.Catmat, i.Catser, i.Uf, i.Quarter, i.Contratacao.Ano })
			.ToListAsync(ct);
		var itemsN = itemRows.Count;
		var perYear = years
			.Select(year => new YearCount
			{
				Year = year,
				Compras = comprasByYear.GetValueOrDefault(year),
				Items = itemRows.Count(i => i.Ano == year),
			})
			.ToList();
		var catalog = await db.CatalogCodes.AsNoTracking()
			.Select(c => new { c.Codigo, c.Kind })
			.ToListAsync(ct);
		var catmat = catalog
			.Where(c => c.Kind == CatalogKind.Catmat)
			.Select(c => c.Codigo)
			.ToHashSet(StringComparer.Ordinal);
		var catser = catalog
			.Where(c => c.Kind == CatalogKind.Catser)
			.Select(c => c.Codigo)
			.ToHashSet(StringComparer.Ordinal);
		var nCoded = itemRows.Count(i =>
			Matches(i.Catmat, catmat) || Matches(i.Catser, catser));
		var percent = itemsN == 0
			? 0m
			: decimal.Round(100m * nCoded / itemsN, 2, MidpointRounding.AwayFromZero);
		var stored = await db.LandingSources.AsNoTracking().ToListAsync(ct);
		var byName = stored.ToDictionary(s => s.Name, StringComparer.Ordinal);
		var sources = s_sources
			.Select(name => Freshness(name, byName))
			.ToList();
		var ufs = itemRows.Select(i => i.Uf).Where(u => u.Length > 0).Distinct(StringComparer.Ordinal).ToList();
		var quarters = itemRows.Select(i => i.Quarter).Where(q => q.Length > 0).Distinct(StringComparer.Ordinal).ToList();
		return new()
		{
			Municipios = new() { N = municipios.Count, Items = municipios },
			Years = years,
			Rows = new() { Compras = comprasN, Items = itemsN, PerYear = perYear },
			CatmatCoveragePercent = percent,
			NCoded = nCoded,
			NItems = itemsN,
			Sources = sources,
			Coverage = Slice.Page(
				itemsN,
				ufs.Count == 1 ? ufs[0] : "",
				quarters.Count == 1 ? quarters[0] : "",
				methodology),
		};
	}

	private static SourceFreshness Freshness(string name, Dictionary<string, LandingSource> byName)
	{
		if (byName.TryGetValue(name, out var row) && row.N > 0)
			return new() { Name = name, LastUpdate = row.LastUpdate, N = row.N };
		return new() { Name = name, LastUpdate = null, N = 0 };
	}

	private static bool Matches(string? raw, HashSet<string> catalog)
	{
		var code = CatalogInt(raw);
		return code is { Length: > 0 } && catalog.Contains(code);
	}

	private static string? CatalogInt(string? raw)
	{
		if (string.IsNullOrWhiteSpace(raw))
			return null;
		var text = raw.Trim();
		if (text.Equals("nan", StringComparison.OrdinalIgnoreCase)
			|| text.Equals("none", StringComparison.OrdinalIgnoreCase)
			|| text.Equals("null", StringComparison.OrdinalIgnoreCase)
			|| string.Equals(text, "-", StringComparison.Ordinal))
			return null;
		if (!decimal.TryParse(text, NumberStyles.Number, CultureInfo.InvariantCulture, out var n))
			return null;
		if (n <= 0)
			return null;
		return decimal.Truncate(n).ToString(CultureInfo.InvariantCulture);
	}
}
