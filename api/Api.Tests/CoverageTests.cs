using System.Text.Json;
using Api.Client;
using Api.Tests.Fixtures;

namespace Api.Tests;

public sealed class CoverageTests(ComprasApiFixture fixture) : IClassFixture<ComprasApiFixture>
{
	private static readonly Instant s_comprasGovUpdate = Instant.FromUtc(2024, 3, 10, 14, 0);

	private static readonly CoberturaMunicipio[] s_municipios =
	[
		new() { Nome = "Anapolis", Uf = "GO", Ibge = "5201108" },
		new() { Nome = "Arapiraca", Uf = "AL", Ibge = "2700300" },
		new() { Nome = "Ariquemes", Uf = "RO", Ibge = "1100023" },
		new() { Nome = "Balneario Camboriu", Uf = "SC", Ibge = "4202008" },
		new() { Nome = "Bauru", Uf = "SP", Ibge = "3506003" },
		new() { Nome = "Campina Grande", Uf = "PB", Ibge = "2504009" },
		new() { Nome = "Canoas", Uf = "RS", Ibge = "4304606" },
		new() { Nome = "Caruaru", Uf = "PE", Ibge = "2604106" },
		new() { Nome = "Cascavel", Uf = "PR", Ibge = "4104808" },
		new() { Nome = "Castanhal", Uf = "PA", Ibge = "1502400" },
		new() { Nome = "Caucaia", Uf = "CE", Ibge = "2303709" },
		new() { Nome = "Caxias do Sul", Uf = "RS", Ibge = "4305108" },
		new() { Nome = "Colatina", Uf = "ES", Ibge = "3201506" },
		new() { Nome = "Cotia", Uf = "SP", Ibge = "3513009" },
		new() { Nome = "Crato", Uf = "CE", Ibge = "2304202" },
		new() { Nome = "Cruzeiro do Sul", Uf = "AC", Ibge = "1200203" },
		new() { Nome = "Divinopolis", Uf = "MG", Ibge = "3122306" },
		new() { Nome = "Dourados", Uf = "MS", Ibge = "5003702" },
		new() { Nome = "Feira de Santana", Uf = "BA", Ibge = "2910800" },
		new() { Nome = "Foz do Iguacu", Uf = "PR", Ibge = "4108304" },
		new() { Nome = "Governador Valadares", Uf = "MG", Ibge = "3127701" },
		new() { Nome = "Guaruja", Uf = "SP", Ibge = "3518701" },
		new() { Nome = "Imperatriz", Uf = "MA", Ibge = "2105302" },
		new() { Nome = "Ipatinga", Uf = "MG", Ibge = "3131307" },
		new() { Nome = "Itaborai", Uf = "RJ", Ibge = "3301900" },
		new() { Nome = "Itaquaquecetuba", Uf = "SP", Ibge = "3523107" },
		new() { Nome = "Jacarei", Uf = "SP", Ibge = "3524402" },
		new() { Nome = "Ji-Parana", Uf = "RO", Ibge = "1100122" },
		new() { Nome = "Joinville", Uf = "SC", Ibge = "4209102" },
		new() { Nome = "Juiz de Fora", Uf = "MG", Ibge = "3136702" },
		new() { Nome = "Lages", Uf = "SC", Ibge = "4209300" },
		new() { Nome = "Londrina", Uf = "PR", Ibge = "4113700" },
		new() { Nome = "Macae", Uf = "RJ", Ibge = "3302403" },
		new() { Nome = "Maraba", Uf = "PA", Ibge = "1504208" },
		new() { Nome = "Marica", Uf = "RJ", Ibge = "3302700" },
		new() { Nome = "Marilia", Uf = "SP", Ibge = "3529005" },
		new() { Nome = "Maringa", Uf = "PR", Ibge = "4115200" },
		new() { Nome = "Montes Claros", Uf = "MG", Ibge = "3143302" },
		new() { Nome = "Niteroi", Uf = "RJ", Ibge = "3303302" },
		new() { Nome = "Nova Friburgo", Uf = "RJ", Ibge = "3303401" },
		new() { Nome = "Parauapebas", Uf = "PA", Ibge = "1505536" },
		new() { Nome = "Parnamirim", Uf = "RN", Ibge = "2403251" },
		new() { Nome = "Paulo Afonso", Uf = "BA", Ibge = "2924009" },
		new() { Nome = "Petropolis", Uf = "RJ", Ibge = "3303906" },
		new() { Nome = "Praia Grande", Uf = "SP", Ibge = "3541000" },
		new() { Nome = "Rio Verde", Uf = "GO", Ibge = "5218805" },
		new() { Nome = "Rorainopolis", Uf = "RR", Ibge = "1400472" },
		new() { Nome = "Santa Luzia", Uf = "MG", Ibge = "3157807" },
		new() { Nome = "Santa Maria", Uf = "RS", Ibge = "4316907" },
		new() { Nome = "Santana", Uf = "AP", Ibge = "1600600" },
		new() { Nome = "Santarem", Uf = "PA", Ibge = "1506807" },
		new() { Nome = "Sao Jose dos Pinhais", Uf = "PR", Ibge = "4125506" },
		new() { Nome = "Sao Lourenco da Mata", Uf = "PE", Ibge = "2613701" },
		new() { Nome = "Suzano", Uf = "SP", Ibge = "3552502" },
		new() { Nome = "Taubate", Uf = "SP", Ibge = "3554102" },
		new() { Nome = "Uberlandia", Uf = "MG", Ibge = "3170206" },
		new() { Nome = "Varzea Grande", Uf = "MT", Ibge = "5108402" },
		new() { Nome = "Vila Velha", Uf = "ES", Ibge = "3205200" },
		new() { Nome = "Volta Redonda", Uf = "RJ", Ibge = "3306305" },
	];

	private static readonly int[] s_years = [2024];

	private static readonly CoberturaYearCount[] s_perYear =
	[
		new() { Year = 2024, Compras = 59, Items = 60 },
	];

	private static readonly CoberturaSource[] s_sources =
	[
		new() { Name = "compras_gov", LastUpdate = s_comprasGovUpdate, N = 59 },
		new() { Name = "receita_cnpj", LastUpdate = null, N = 0 },
		new() { Name = "ocds", LastUpdate = null, N = 0 },
		new() { Name = "pncp_consulta", LastUpdate = null, N = 0 },
		new() { Name = "tce_sp", LastUpdate = null, N = 0 },
		new() { Name = "tce_rs", LastUpdate = null, N = 0 },
		new() { Name = "cgu_ceis_cnep", LastUpdate = null, N = 0 },
	];

	[Fact]
	public async Task FullCycle_WarehouseSliceCoverage()
	{
		var client = fixture.GetClient();
		var got = await client.GetCobertura();

		Assert.Equal(59, got.Municipios.N);
		Assert.Equal(s_municipios, got.Municipios.Items);
		Assert.Equal(s_years, got.Years);
		Assert.Equal(59, got.Rows.Compras);
		Assert.Equal(60, got.Rows.Items);
		Assert.Equal(s_perYear, got.Rows.PerYear);
		Assert.Equal(4, got.NCoded);
		Assert.Equal(60, got.NItems);
		Assert.Equal(6.67m, got.CatmatCoveragePercent);
		Assert.Equal(
			new Coverage
			{
				N = 60,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			got.Coverage);
		Assert.Equal(s_sources, got.Sources);

		var http = fixture.CreateHttpClient();
		var json = await http.GetStringAsync(new Uri(http.BaseAddress!, "/api/cobertura"));
		using var doc = JsonDocument.Parse(json);
		AssertNoFlagProperty(doc.RootElement);
	}

	private static void AssertNoFlagProperty(JsonElement element)
	{
		if (element.ValueKind is JsonValueKind.Object)
		{
			foreach (var property in element.EnumerateObject())
			{
				if (property.Name.Contains("flag", StringComparison.OrdinalIgnoreCase))
					Assert.Fail($"Explorer JSON must not carry {property.Name}.");

				AssertNoFlagProperty(property.Value);
			}

			return;
		}

		if (element.ValueKind is not JsonValueKind.Array)
			return;

		foreach (var item in element.EnumerateArray())
			AssertNoFlagProperty(item);
	}
}
