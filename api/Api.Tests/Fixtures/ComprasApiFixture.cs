using System.Text.Json;
using System.Text.Json.Serialization;
using Api.Client;
using Api.Persistence;
using Api.Persistence.Entities;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using NodaTime.Serialization.SystemTextJson;
using NodaTime.Testing;
using Refit;

namespace Api.Tests.Fixtures;

public sealed class ComprasApiFixture : IAsyncLifetime
{
	public static readonly Instant Start = Instant.FromUtc(2024, 6, 15, 12, 0);

	private static readonly JsonSerializerOptions s_json = CreateJson();

	private readonly Factory _factory = new();

	public FakeClock Clock => _factory.Clock;

	public HttpClient CreateHttpClient() => _factory.CreateClient();

	public IComprasApi GetClient()
	{
		var http = CreateHttpClient();
		return RestService.For<IComprasApi>(
			http,
			new RefitSettings
			{
				ContentSerializer = new SystemTextJsonContentSerializer(s_json),
			});
	}

	public async Task SeedAsync(Func<ApplicationDbContext, Task> seed)
	{
		using var scope = _factory.Services.CreateScope();
		var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
		await seed(db);
		await db.SaveChangesAsync();
	}

	public async Task InitializeAsync()
	{
		_ = _factory.Server;
		using var scope = _factory.Services.CreateScope();
		var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
		_ = await db.Database.EnsureCreatedAsync();
		SeedSlice(db);
		_ = await db.SaveChangesAsync();
	}

	public async Task DisposeAsync() => await _factory.DisposeAsync();

	private static void SeedSlice(ApplicationDbContext db)
	{
		var orgao = new Orgao
		{
			Id = SliceIds.Orgao,
			Cnpj = "28747223000191",
			RazaoSocial = "Municipio de Volta Redonda",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = SliceIds.Uf,
			MunicipioIbge = "3306305",
			MunicipioNome = "Volta Redonda",
		};
		var hidden = new Orgao
		{
			Id = SliceIds.HiddenOrgao,
			Cnpj = "00000000000191",
			RazaoSocial = "Orgao suspenso",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3550308",
			MunicipioNome = "Sao Paulo",
			Suspended = true,
		};
		var suspendTarget = new Orgao
		{
			Id = SliceIds.SuspendTarget,
			Cnpj = "11111111000191",
			RazaoSocial = "Orgao a suspender",
			Esfera = Api.Persistence.Entities.Esfera.Estadual,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3106200",
			MunicipioNome = "Belo Horizonte",
		};
		var pageAlfa = new Orgao
		{
			Id = SliceIds.PageOrgaoAlfa,
			Cnpj = "22222222000191",
			RazaoSocial = "Paginacao Alfa",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "TO",
			MunicipioIbge = "1721000",
			MunicipioNome = "Palmas",
		};
		var pageBeta = new Orgao
		{
			Id = SliceIds.PageOrgaoBeta,
			Cnpj = "33333333000191",
			RazaoSocial = "Paginacao Beta",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "TO",
			MunicipioIbge = "1721000",
			MunicipioNome = "Palmas",
		};
		var niteroi = new Orgao
		{
			Id = SliceIds.OrgaoNiteroi,
			Cnpj = "28521748000159",
			RazaoSocial = "Municipio de Niteroi",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = SliceIds.Uf,
			MunicipioIbge = "3303302",
			MunicipioNome = "Niteroi",
		};
		var bauru = new Orgao
		{
			Id = SliceIds.OrgaoBauru,
			Cnpj = "46137410000180",
			RazaoSocial = "Municipio de Bauru",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3506003",
			MunicipioNome = "Bauru",
		};
		var caxias = new Orgao
		{
			Id = SliceIds.OrgaoCaxias,
			Cnpj = "88830609000139",
			RazaoSocial = "Municipio de Caxias do Sul",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RS",
			MunicipioIbge = "4305108",
			MunicipioNome = "Caxias do Sul",
		};
		var joinville = new Orgao
		{
			Id = SliceIds.OrgaoJoinville,
			Cnpj = "83169623000110",
			RazaoSocial = "Municipio de Joinville",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SC",
			MunicipioIbge = "4209102",
			MunicipioNome = "Joinville",
		};
		var uberlandia = new Orgao
		{
			Id = SliceIds.OrgaoUberlandia,
			Cnpj = "18431312000115",
			RazaoSocial = "Municipio de Uberlandia",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3170206",
			MunicipioNome = "Uberlandia",
		};
		var londrina = new Orgao
		{
			Id = SliceIds.OrgaoLondrina,
			Cnpj = "75771477000170",
			RazaoSocial = "Municipio de Londrina",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PR",
			MunicipioIbge = "4113700",
			MunicipioNome = "Londrina",
		};
		var feira = new Orgao
		{
			Id = SliceIds.OrgaoFeira,
			Cnpj = "14043574000151",
			RazaoSocial = "Municipio de Feira de Santana",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "BA",
			MunicipioIbge = "2910800",
			MunicipioNome = "Feira de Santana",
		};
		var caruaru = new Orgao
		{
			Id = SliceIds.OrgaoCaruaru,
			Cnpj = "10091536000113",
			RazaoSocial = "Municipio de Caruaru",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PE",
			MunicipioIbge = "2604106",
			MunicipioNome = "Caruaru",
		};
		var anapolis = new Orgao
		{
			Id = SliceIds.OrgaoAnapolis,
			Cnpj = "01067479000146",
			RazaoSocial = "Municipio de Anapolis",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "GO",
			MunicipioIbge = "5201108",
			MunicipioNome = "Anapolis",
		};
		var vilaVelha = new Orgao
		{
			Id = SliceIds.OrgaoVilaVelha,
			Cnpj = "27165554000103",
			RazaoSocial = "Municipio de Vila Velha",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "ES",
			MunicipioIbge = "3205200",
			MunicipioNome = "Vila Velha",
		};
		var campinaGrande = new Orgao
		{
			Id = SliceIds.OrgaoCampinaGrande,
			Cnpj = "08993917000146",
			RazaoSocial = "Municipio de Campina Grande",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PB",
			MunicipioIbge = "2504009",
			MunicipioNome = "Campina Grande",
		};
		var caucaia = new Orgao
		{
			Id = SliceIds.OrgaoCaucaia,
			Cnpj = "07616162000106",
			RazaoSocial = "Municipio de Caucaia",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "CE",
			MunicipioIbge = "2303709",
			MunicipioNome = "Caucaia",
		};
		var imperatriz = new Orgao
		{
			Id = SliceIds.OrgaoImperatriz,
			Cnpj = "06158455000116",
			RazaoSocial = "Municipio de Imperatriz",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MA",
			MunicipioIbge = "2105302",
			MunicipioNome = "Imperatriz",
		};
		var arapiraca = new Orgao
		{
			Id = SliceIds.OrgaoArapiraca,
			Cnpj = "12198693000158",
			RazaoSocial = "Municipio de Arapiraca",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "AL",
			MunicipioIbge = "2700300",
			MunicipioNome = "Arapiraca",
		};
		var dourados = new Orgao
		{
			Id = SliceIds.OrgaoDourados,
			Cnpj = "20267427000168",
			RazaoSocial = "Municipio de Dourados",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MS",
			MunicipioIbge = "5003702",
			MunicipioNome = "Dourados",
		};
		var maraba = new Orgao
		{
			Id = SliceIds.OrgaoMaraba,
			Cnpj = "05853163000130",
			RazaoSocial = "Municipio de Maraba",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PA",
			MunicipioIbge = "1504208",
			MunicipioNome = "Maraba",
		};
		var varzeaGrande = new Orgao
		{
			Id = SliceIds.OrgaoVarzeaGrande,
			Cnpj = "03507548000110",
			RazaoSocial = "Municipio de Varzea Grande",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MT",
			MunicipioIbge = "5108402",
			MunicipioNome = "Varzea Grande",
		};
		var jiParana = new Orgao
		{
			Id = SliceIds.OrgaoJiParana,
			Cnpj = "04092672000125",
			RazaoSocial = "Municipio de Ji-Parana",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RO",
			MunicipioIbge = "1100122",
			MunicipioNome = "Ji-Parana",
		};
		var parnamirim = new Orgao
		{
			Id = SliceIds.OrgaoParnamirim,
			Cnpj = "08170862000174",
			RazaoSocial = "Municipio de Parnamirim",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RN",
			MunicipioIbge = "2403251",
			MunicipioNome = "Parnamirim",
		};
		var cruzeiroDoSul = new Orgao
		{
			Id = SliceIds.OrgaoCruzeiroDoSul,
			Cnpj = "04012548000102",
			RazaoSocial = "Municipio de Cruzeiro do Sul",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "AC",
			MunicipioIbge = "1200203",
			MunicipioNome = "Cruzeiro do Sul",
		};
		var santana = new Orgao
		{
			Id = SliceIds.OrgaoSantana,
			Cnpj = "23066640000108",
			RazaoSocial = "Municipio de Santana",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "AP",
			MunicipioIbge = "1600600",
			MunicipioNome = "Santana",
		};
		var rorainopolis = new Orgao
		{
			Id = SliceIds.OrgaoRorainopolis,
			Cnpj = "01613031000180",
			RazaoSocial = "Municipio de Rorainopolis",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RR",
			MunicipioIbge = "1400472",
			MunicipioNome = "Rorainopolis",
		};
		var maringa = new Orgao
		{
			Id = SliceIds.OrgaoMaringa,
			Cnpj = "76282656000106",
			RazaoSocial = "Municipio de Maringa",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PR",
			MunicipioIbge = "4115200",
			MunicipioNome = "Maringa",
		};
		var taubate = new Orgao
		{
			Id = SliceIds.OrgaoTaubate,
			Cnpj = "45176005000108",
			RazaoSocial = "Municipio de Taubate",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3554102",
			MunicipioNome = "Taubate",
		};
		var cascavel = new Orgao
		{
			Id = SliceIds.OrgaoCascavel,
			Cnpj = "76208867000107",
			RazaoSocial = "Municipio de Cascavel",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PR",
			MunicipioIbge = "4104808",
			MunicipioNome = "Cascavel",
		};
		var juizDeFora = new Orgao
		{
			Id = SliceIds.OrgaoJuizDeFora,
			Cnpj = "18338178000102",
			RazaoSocial = "Municipio de Juiz de Fora",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3136702",
			MunicipioNome = "Juiz de Fora",
		};
		var foz = new Orgao
		{
			Id = SliceIds.OrgaoFoz,
			Cnpj = "76206606000140",
			RazaoSocial = "Municipio de Foz do Iguacu",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PR",
			MunicipioIbge = "4108304",
			MunicipioNome = "Foz do Iguacu",
		};
		var santaMaria = new Orgao
		{
			Id = SliceIds.OrgaoSantaMaria,
			Cnpj = "88488366000100",
			RazaoSocial = "Municipio de Santa Maria",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RS",
			MunicipioIbge = "4316907",
			MunicipioNome = "Santa Maria",
		};
		var montesClaros = new Orgao
		{
			Id = SliceIds.OrgaoMontesClaros,
			Cnpj = "22678874000135",
			RazaoSocial = "Municipio de Montes Claros",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3143302",
			MunicipioNome = "Montes Claros",
		};
		var governadorValadares = new Orgao
		{
			Id = SliceIds.OrgaoGovernadorValadares,
			Cnpj = "20622890000180",
			RazaoSocial = "Municipio de Governador Valadares",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3127701",
			MunicipioNome = "Governador Valadares",
		};
		var canoas = new Orgao
		{
			Id = SliceIds.OrgaoCanoas,
			Cnpj = "88577416000118",
			RazaoSocial = "Municipio de Canoas",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RS",
			MunicipioIbge = "4304606",
			MunicipioNome = "Canoas",
		};
		var lages = new Orgao
		{
			Id = SliceIds.OrgaoLages,
			Cnpj = "82777301000190",
			RazaoSocial = "Municipio de Lages",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SC",
			MunicipioIbge = "4209300",
			MunicipioNome = "Lages",
		};
		var santarem = new Orgao
		{
			Id = SliceIds.OrgaoSantarem,
			Cnpj = "05182233000761",
			RazaoSocial = "Municipio de Santarem",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PA",
			MunicipioIbge = "1506807",
			MunicipioNome = "Santarem",
		};
		var rioVerde = new Orgao
		{
			Id = SliceIds.OrgaoRioVerde,
			Cnpj = "02056729000105",
			RazaoSocial = "Municipio de Rio Verde",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "GO",
			MunicipioIbge = "5218805",
			MunicipioNome = "Rio Verde",
		};
		var pauloAfonso = new Orgao
		{
			Id = SliceIds.OrgaoPauloAfonso,
			Cnpj = "14217327000124",
			RazaoSocial = "Municipio de Paulo Afonso",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "BA",
			MunicipioIbge = "2924009",
			MunicipioNome = "Paulo Afonso",
		};
		var saoLourenco = new Orgao
		{
			Id = SliceIds.OrgaoSaoLourenco,
			Cnpj = "11251832000105",
			RazaoSocial = "Municipio de Sao Lourenco da Mata",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PE",
			MunicipioIbge = "2613701",
			MunicipioNome = "Sao Lourenco da Mata",
		};
		var crato = new Orgao
		{
			Id = SliceIds.OrgaoCrato,
			Cnpj = "07587975000107",
			RazaoSocial = "Municipio de Crato",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "CE",
			MunicipioIbge = "2304202",
			MunicipioNome = "Crato",
		};
		var ariquemes = new Orgao
		{
			Id = SliceIds.OrgaoAriquemes,
			Cnpj = "04104816000116",
			RazaoSocial = "Municipio de Ariquemes",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RO",
			MunicipioIbge = "1100023",
			MunicipioNome = "Ariquemes",
		};
		var colatina = new Orgao
		{
			Id = SliceIds.OrgaoColatina,
			Cnpj = "27165729000174",
			RazaoSocial = "Municipio de Colatina",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "ES",
			MunicipioIbge = "3201506",
			MunicipioNome = "Colatina",
		};
		var castanhal = new Orgao
		{
			Id = SliceIds.OrgaoCastanhal,
			Cnpj = "05121991000184",
			RazaoSocial = "Municipio de Castanhal",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PA",
			MunicipioIbge = "1502400",
			MunicipioNome = "Castanhal",
		};
		var divinopolis = new Orgao
		{
			Id = SliceIds.OrgaoDivinopolis,
			Cnpj = "18291351000164",
			RazaoSocial = "Municipio de Divinopolis",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3122306",
			MunicipioNome = "Divinopolis",
		};
		var petropolis = new Orgao
		{
			Id = SliceIds.OrgaoPetropolis,
			Cnpj = "29138344000143",
			RazaoSocial = "Municipio de Petropolis",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RJ",
			MunicipioIbge = "3303906",
			MunicipioNome = "Petropolis",
		};
		var ipatinga = new Orgao
		{
			Id = SliceIds.OrgaoIpatinga,
			Cnpj = "19876424000142",
			RazaoSocial = "Municipio de Ipatinga",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3131307",
			MunicipioNome = "Ipatinga",
		};
		var macae = new Orgao
		{
			Id = SliceIds.OrgaoMacae,
			Cnpj = "29115474000160",
			RazaoSocial = "Municipio de Macae",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RJ",
			MunicipioIbge = "3302403",
			MunicipioNome = "Macae",
		};
		var santaLuzia = new Orgao
		{
			Id = SliceIds.OrgaoSantaLuzia,
			Cnpj = "18715409000150",
			RazaoSocial = "Municipio de Santa Luzia",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "MG",
			MunicipioIbge = "3157807",
			MunicipioNome = "Santa Luzia",
		};
		var novaFriburgo = new Orgao
		{
			Id = SliceIds.OrgaoNovaFriburgo,
			Cnpj = "28606630000123",
			RazaoSocial = "Municipio de Nova Friburgo",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RJ",
			MunicipioIbge = "3303401",
			MunicipioNome = "Nova Friburgo",
		};
		var marilia = new Orgao
		{
			Id = SliceIds.OrgaoMarilia,
			Cnpj = "44477909000100",
			RazaoSocial = "Municipio de Marilia",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3529005",
			MunicipioNome = "Marilia",
		};
		var balneario = new Orgao
		{
			Id = SliceIds.OrgaoBalneario,
			Cnpj = "83102285000107",
			RazaoSocial = "Municipio de Balneario Camboriu",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SC",
			MunicipioIbge = "4202008",
			MunicipioNome = "Balneario Camboriu",
		};
		var itaqua = new Orgao
		{
			Id = SliceIds.OrgaoItaqua,
			Cnpj = "46316600000164",
			RazaoSocial = "Municipio de Itaquaquecetuba",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3523107",
			MunicipioNome = "Itaquaquecetuba",
		};
		var praiaGrande = new Orgao
		{
			Id = SliceIds.OrgaoPraiaGrande,
			Cnpj = "46177531000155",
			RazaoSocial = "Municipio de Praia Grande",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3541000",
			MunicipioNome = "Praia Grande",
		};
		var saoJoseDosPinhais = new Orgao
		{
			Id = SliceIds.OrgaoSaoJoseDosPinhais,
			Cnpj = "76105543000135",
			RazaoSocial = "Municipio de Sao Jose dos Pinhais",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PR",
			MunicipioIbge = "4125506",
			MunicipioNome = "Sao Jose dos Pinhais",
		};
		var suzano = new Orgao
		{
			Id = SliceIds.OrgaoSuzano,
			Cnpj = "46523056000121",
			RazaoSocial = "Municipio de Suzano",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3552502",
			MunicipioNome = "Suzano",
		};
		var guaruja = new Orgao
		{
			Id = SliceIds.OrgaoGuaruja,
			Cnpj = "44959021000104",
			RazaoSocial = "Municipio de Guaruja",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3518701",
			MunicipioNome = "Guaruja",
		};
		var cotia = new Orgao
		{
			Id = SliceIds.OrgaoCotia,
			Cnpj = "46523049000120",
			RazaoSocial = "Municipio de Cotia",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3513009",
			MunicipioNome = "Cotia",
		};
		var parauapebas = new Orgao
		{
			Id = SliceIds.OrgaoParauapebas,
			Cnpj = "22980999000115",
			RazaoSocial = "Municipio de Parauapebas",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "PA",
			MunicipioIbge = "1505536",
			MunicipioNome = "Parauapebas",
		};
		var jacarei = new Orgao
		{
			Id = SliceIds.OrgaoJacarei,
			Cnpj = "46694139000183",
			RazaoSocial = "Municipio de Jacarei",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "SP",
			MunicipioIbge = "3524402",
			MunicipioNome = "Jacarei",
		};
		var itaborai = new Orgao
		{
			Id = SliceIds.OrgaoItaborai,
			Cnpj = "28741080000155",
			RazaoSocial = "Municipio de Itaborai",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RJ",
			MunicipioIbge = "3301900",
			MunicipioNome = "Itaborai",
		};
		var marica = new Orgao
		{
			Id = SliceIds.OrgaoMarica,
			Cnpj = "29131075000193",
			RazaoSocial = "Municipio de Marica",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "RJ",
			MunicipioIbge = "3302700",
			MunicipioNome = "Marica",
		};
		var fornecedor = new Fornecedor
		{
			Id = SliceIds.Fornecedor,
			Cnpj = "12345678000195",
			RazaoSocial = "Papelaria Central Ltda",
			OpenedOn = new LocalDate(2023, 1, 15),
			Cnae = "4761-0/01",
		};
		var contratacao = new Contratacao
		{
			Id = SliceIds.Contratacao,
			PncpId = "3306305-1-000001/2024",
			OrgaoId = SliceIds.Orgao,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de material de expediente",
			Ano = 2024,
			ValorHomologado = 1200m,
			PublicadoEm = Instant.FromUtc(2024, 3, 10, 14, 0),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var item1 = new Item
		{
			Id = SliceIds.Item1,
			ContratacaoId = SliceIds.Contratacao,
			FornecedorId = SliceIds.Fornecedor,
			Descricao = "Resma papel A4",
			Catmat = "123456",
			Quantidade = 100m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 8m,
			ValorTotal = 800m,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var item2 = new Item
		{
			Id = SliceIds.Item2,
			ContratacaoId = SliceIds.Contratacao,
			FornecedorId = SliceIds.Fornecedor,
			Descricao = "Caneta esferografica azul",
			Catmat = "123456",
			Quantidade = 200m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 2m,
			ValorTotal = 400m,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var fornecedorExtra = new Fornecedor
		{
			Id = SliceIds.FornecedorExtra,
			Cnpj = "55667788000191",
			RazaoSocial = "Comercio de Limpeza Baixada Ltda",
			OpenedOn = new LocalDate(2018, 4, 2),
			Cnae = "4761-0/01",
		};
		var contratacaoNiteroi = new Contratacao
		{
			Id = SliceIds.ContratacaoNiteroi,
			PncpId = "3303302-1-000001/2024",
			OrgaoId = SliceIds.OrgaoNiteroi,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de material de limpeza",
			Ano = 2024,
			ValorHomologado = 120m,
			PublicadoEm = Instant.FromUtc(2024, 3, 20, 14, 0),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoBauru = new Contratacao
		{
			Id = SliceIds.ContratacaoBauru,
			PncpId = "3506003-1-000001/2024",
			OrgaoId = SliceIds.OrgaoBauru,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de material de expediente",
			Ano = 2024,
			ValorHomologado = 80m,
			PublicadoEm = Instant.FromUtc(2024, 4, 12, 11, 0),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCaxias = new Contratacao
		{
			Id = SliceIds.ContratacaoCaxias,
			PncpId = "88830609000139-1-000888/2024",
			OrgaoId = SliceIds.OrgaoCaxias,
			Modalidade = "pregao eletronico",
			Objeto = "Fornecimento de suporte para monitor",
			Ano = 2024,
			ValorHomologado = 11000m,
			PublicadoEm = Instant.FromUtc(2024, 11, 4, 7, 17),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoJoinville = new Contratacao
		{
			Id = SliceIds.ContratacaoJoinville,
			PncpId = "83169623000110-1-000301/2024",
			OrgaoId = SliceIds.OrgaoJoinville,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de leitores de codigo de barras a laser fixo",
			Ano = 2024,
			ValorHomologado = 33180m,
			PublicadoEm = Instant.FromUtc(2024, 8, 9, 7, 1),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoUberlandia = new Contratacao
		{
			Id = SliceIds.ContratacaoUberlandia,
			PncpId = "18431312000115-1-000095/2024",
			OrgaoId = SliceIds.OrgaoUberlandia,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de coturnos, calcado de seguranca tatico",
			Ano = 2024,
			ValorHomologado = 35052m,
			PublicadoEm = Instant.FromUtc(2024, 3, 26, 7, 10),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoLondrina = new Contratacao
		{
			Id = SliceIds.ContratacaoLondrina,
			PncpId = "75771477000170-1-000026/2024",
			OrgaoId = SliceIds.OrgaoLondrina,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de precos para eventual fornecimento de medicamentos constantes na REMUME",
			Ano = 2024,
			ValorHomologado = 10259546.3707m,
			PublicadoEm = Instant.FromUtc(2024, 1, 12, 7, 3),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoFeira = new Contratacao
		{
			Id = SliceIds.ContratacaoFeira,
			PncpId = "14043574000151-1-000544/2024",
			OrgaoId = SliceIds.OrgaoFeira,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao agua mineral natural, sem gas",
			Ano = 2024,
			ValorHomologado = 74100m,
			PublicadoEm = Instant.FromUtc(2024, 10, 2, 7, 35),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCaruaru = new Contratacao
		{
			Id = SliceIds.ContratacaoCaruaru,
			PncpId = "10091536000113-1-000124/2024",
			OrgaoId = SliceIds.OrgaoCaruaru,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de precos para eventual e futura aquisicao de placas toponimicas",
			Ano = 2024,
			ValorHomologado = 39500m,
			PublicadoEm = Instant.FromUtc(2024, 9, 25, 7, 8),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoAnapolis = new Contratacao
		{
			Id = SliceIds.ContratacaoAnapolis,
			PncpId = "01067479000146-1-000086/2024",
			OrgaoId = SliceIds.OrgaoAnapolis,
			Modalidade = "dispensa",
			Objeto = "Dispensa de licitacao para aquisicao de scanners de mesa",
			Ano = 2024,
			ValorHomologado = 13140.88m,
			PublicadoEm = Instant.FromUtc(2024, 10, 23, 15, 24),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoVilaVelha = new Contratacao
		{
			Id = SliceIds.ContratacaoVilaVelha,
			PncpId = "27165554000103-1-000429/2024",
			OrgaoId = SliceIds.OrgaoVilaVelha,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de precos para aquisicao de material de consumo odontologico",
			Ano = 2024,
			ValorHomologado = 5610m,
			PublicadoEm = Instant.FromUtc(2024, 11, 11, 7, 2),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCampinaGrande = new Contratacao
		{
			Id = SliceIds.ContratacaoCampinaGrande,
			PncpId = "08993917000146-1-000180/2024",
			OrgaoId = SliceIds.OrgaoCampinaGrande,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de modulos de memoria adicionais",
			Ano = 2024,
			ValorHomologado = 839.96m,
			PublicadoEm = Instant.FromUtc(2024, 12, 3, 14, 36),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCaucaia = new Contratacao
		{
			Id = SliceIds.ContratacaoCaucaia,
			PncpId = "07616162000106-1-000076/2024",
			OrgaoId = SliceIds.OrgaoCaucaia,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de receituario b azul",
			Ano = 2024,
			ValorHomologado = 8550m,
			PublicadoEm = Instant.FromUtc(2024, 9, 30, 15, 44),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoImperatriz = new Contratacao
		{
			Id = SliceIds.ContratacaoImperatriz,
			PncpId = "06158455000116-1-000002/2024",
			OrgaoId = SliceIds.OrgaoImperatriz,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de projetos literarios",
			Ano = 2024,
			ValorHomologado = 28380165.45m,
			PublicadoEm = Instant.FromUtc(2024, 7, 12, 7, 7),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoArapiraca = new Contratacao
		{
			Id = SliceIds.ContratacaoArapiraca,
			PncpId = "12198693000158-1-000088/2024",
			OrgaoId = SliceIds.OrgaoArapiraca,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de medicamento lamotrigina",
			Ano = 2024,
			ValorHomologado = 288m,
			PublicadoEm = Instant.FromUtc(2024, 10, 2, 10, 49),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoDourados = new Contratacao
		{
			Id = SliceIds.ContratacaoDourados,
			PncpId = "20267427000168-1-000043/2024",
			OrgaoId = SliceIds.OrgaoDourados,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de reagentes para diagnostico clinico",
			Ano = 2024,
			ValorHomologado = 4908m,
			PublicadoEm = Instant.FromUtc(2024, 11, 7, 17, 13),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoMaraba = new Contratacao
		{
			Id = SliceIds.ContratacaoMaraba,
			PncpId = "05853163000130-1-000142/2024",
			OrgaoId = SliceIds.OrgaoMaraba,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de fogao 4 bocas",
			Ano = 2024,
			ValorHomologado = 3399.96m,
			PublicadoEm = Instant.FromUtc(2024, 10, 15, 14, 9),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoVarzeaGrande = new Contratacao
		{
			Id = SliceIds.ContratacaoVarzeaGrande,
			PncpId = "03507548000110-1-000073/2024",
			OrgaoId = SliceIds.OrgaoVarzeaGrande,
			Modalidade = "dispensa",
			Objeto = "Fornecimento de equipamentos permanentes de informatica",
			Ano = 2024,
			ValorHomologado = 52042m,
			PublicadoEm = Instant.FromUtc(2024, 11, 27, 9, 10),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoJiParana = new Contratacao
		{
			Id = SliceIds.ContratacaoJiParana,
			PncpId = "04092672000125-1-000139/2024",
			OrgaoId = SliceIds.OrgaoJiParana,
			Modalidade = "inexigibilidade",
			Objeto = "Fornecimento de assinatura anual de banco de dados",
			Ano = 2024,
			ValorHomologado = 38540m,
			PublicadoEm = Instant.FromUtc(2024, 10, 18, 9, 52),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoParnamirim = new Contratacao
		{
			Id = SliceIds.ContratacaoParnamirim,
			PncpId = "08170862000174-1-000034/2024",
			OrgaoId = SliceIds.OrgaoParnamirim,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de veiculo automotor",
			Ano = 2024,
			ValorHomologado = 78500m,
			PublicadoEm = Instant.FromUtc(2024, 9, 20, 7, 7),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCruzeiroDoSul = new Contratacao
		{
			Id = SliceIds.ContratacaoCruzeiroDoSul,
			PncpId = "04012548000102-1-000033/2024",
			OrgaoId = SliceIds.OrgaoCruzeiroDoSul,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de maquinas e equipamentos agricolas",
			Ano = 2024,
			ValorHomologado = 371798.45m,
			PublicadoEm = Instant.FromUtc(2024, 7, 19, 7, 14),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSantana = new Contratacao
		{
			Id = SliceIds.ContratacaoSantana,
			PncpId = "23066640000108-1-000002/2024",
			OrgaoId = SliceIds.OrgaoSantana,
			Modalidade = "pregao presencial",
			Objeto = "Contratacao de instituicao financeira",
			Ano = 2024,
			ValorHomologado = 1m,
			PublicadoEm = Instant.FromUtc(2024, 11, 8, 14, 1),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoRorainopolis = new Contratacao
		{
			Id = SliceIds.ContratacaoRorainopolis,
			PncpId = "01613031000180-1-000001/2024",
			OrgaoId = SliceIds.OrgaoRorainopolis,
			Modalidade = "pregao presencial",
			Objeto = "Aquisicao de veiculos Ambulancias",
			Ano = 2024,
			ValorHomologado = 1404000m,
			PublicadoEm = Instant.FromUtc(2024, 10, 31, 13, 53),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoMaringa = new Contratacao
		{
			Id = SliceIds.ContratacaoMaringa,
			PncpId = "76282656000106-1-000691/2024",
			OrgaoId = SliceIds.OrgaoMaringa,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de precos para aquisicao de medicamentos",
			Ano = 2024,
			ValorHomologado = 5373878.65m,
			PublicadoEm = Instant.FromUtc(2024, 10, 8, 7, 6),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoTaubate = new Contratacao
		{
			Id = SliceIds.ContratacaoTaubate,
			PncpId = "45176005000108-1-000706/2024",
			OrgaoId = SliceIds.OrgaoTaubate,
			Modalidade = "inexigibilidade",
			Objeto = "Aquisicao de eletrodos para eletroencefalograma",
			Ano = 2024,
			ValorHomologado = 8250m,
			PublicadoEm = Instant.FromUtc(2024, 9, 10, 15, 0),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCascavel = new Contratacao
		{
			Id = SliceIds.ContratacaoCascavel,
			PncpId = "76208867000107-1-000325/2024",
			OrgaoId = SliceIds.OrgaoCascavel,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de tres motocicletas para a Guarda Municipal de Cascavel",
			Ano = 2024,
			ValorHomologado = 196110m,
			PublicadoEm = Instant.FromUtc(2024, 11, 5, 7, 25),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoJuizDeFora = new Contratacao
		{
			Id = SliceIds.ContratacaoJuizDeFora,
			PncpId = "18338178000102-1-000200/2024",
			OrgaoId = SliceIds.OrgaoJuizDeFora,
			Modalidade = "dispensa",
			Objeto = "Keytruda 100mg/4ml solucao injetavel",
			Ano = 2024,
			ValorHomologado = 160214m,
			PublicadoEm = Instant.FromUtc(2024, 9, 13, 14, 21),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoFoz = new Contratacao
		{
			Id = SliceIds.ContratacaoFoz,
			PncpId = "76206606000140-1-000362/2024",
			OrgaoId = SliceIds.OrgaoFoz,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de fermento biologico",
			Ano = 2024,
			ValorHomologado = 41175m,
			PublicadoEm = Instant.FromUtc(2024, 9, 10, 9, 39),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSantaMaria = new Contratacao
		{
			Id = SliceIds.ContratacaoSantaMaria,
			PncpId = "88488366000100-1-000435/2024",
			OrgaoId = SliceIds.OrgaoSantaMaria,
			Modalidade = "pregao eletronico",
			Objeto = "RP - Medicamentos",
			Ano = 2024,
			ValorHomologado = 28182m,
			PublicadoEm = Instant.FromUtc(2024, 10, 15, 7, 6),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoMontesClaros = new Contratacao
		{
			Id = SliceIds.ContratacaoMontesClaros,
			PncpId = "22678874000135-1-000430/2024",
			OrgaoId = SliceIds.OrgaoMontesClaros,
			Modalidade = "concorrencia eletronica",
			Objeto = "Reforma dos sistemas de seguranca contra incendio",
			Ano = 2024,
			ValorHomologado = 330811.34m,
			PublicadoEm = Instant.FromUtc(2024, 7, 30, 7, 9),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoGovernadorValadares = new Contratacao
		{
			Id = SliceIds.ContratacaoGovernadorValadares,
			PncpId = "20622890000180-1-000098/2024",
			OrgaoId = SliceIds.OrgaoGovernadorValadares,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de material grafico cartao do idoso",
			Ano = 2024,
			ValorHomologado = 43500m,
			PublicadoEm = Instant.FromUtc(2024, 10, 30, 8, 39),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCanoas = new Contratacao
		{
			Id = SliceIds.ContratacaoCanoas,
			PncpId = "88577416000118-1-000156/2024",
			OrgaoId = SliceIds.OrgaoCanoas,
			Modalidade = "pregao eletronico",
			Objeto = "Fornecimento de clorimetro digital portatil e reagentes DPD para cloro livre",
			Ano = 2024,
			ValorHomologado = 3305.99m,
			PublicadoEm = Instant.FromUtc(2024, 10, 16, 7, 1),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoLages = new Contratacao
		{
			Id = SliceIds.ContratacaoLages,
			PncpId = "82777301000190-1-000260/2024",
			OrgaoId = SliceIds.OrgaoLages,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de Bolsas de Trabalho personalizadas para a equipe de fiscalizacao da Vigilancia Sanitaria",
			Ano = 2024,
			ValorHomologado = 2910m,
			PublicadoEm = Instant.FromUtc(2024, 9, 4, 7, 15),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSantarem = new Contratacao
		{
			Id = SliceIds.ContratacaoSantarem,
			PncpId = "05182233000761-1-000020/2024",
			OrgaoId = SliceIds.OrgaoSantarem,
			Modalidade = "pregao eletronico",
			Objeto = "Construcao de unidade Basica de Saude (UBS) Tapara Grande - Modelo Municipal",
			Ano = 2024,
			ValorHomologado = 326424.56m,
			PublicadoEm = Instant.FromUtc(2024, 8, 29, 7, 18),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoRioVerde = new Contratacao
		{
			Id = SliceIds.ContratacaoRioVerde,
			PncpId = "02056729000105-1-001376/2024",
			OrgaoId = SliceIds.OrgaoRioVerde,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de 10 Lampada de LED tubular T8 minimo 40W bivolt luz branca 240 cm",
			Ano = 2024,
			ValorHomologado = 450m,
			PublicadoEm = Instant.FromUtc(2024, 11, 6, 17, 3),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoPauloAfonso = new Contratacao
		{
			Id = SliceIds.ContratacaoPauloAfonso,
			PncpId = "14217327000124-1-000121/2024",
			OrgaoId = SliceIds.OrgaoPauloAfonso,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de cafe em po e acucar para as necessidades da secretaria de educacao.",
			Ano = 2024,
			ValorHomologado = 8840m,
			PublicadoEm = Instant.FromUtc(2024, 10, 17, 7, 7),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSaoLourenco = new Contratacao
		{
			Id = SliceIds.ContratacaoSaoLourenco,
			PncpId = "11251832000105-1-000065/2024",
			OrgaoId = SliceIds.OrgaoSaoLourenco,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de Ventiladores Tipo Parede, para atender as necessidades da Secretaria de Educacao do Municipio de Sao Lourenco da Mata - PE.",
			Ano = 2024,
			ValorHomologado = 97000m,
			PublicadoEm = Instant.FromUtc(2024, 10, 15, 7, 9),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCrato = new Contratacao
		{
			Id = SliceIds.ContratacaoCrato,
			PncpId = "07587975000107-1-000020/2024",
			OrgaoId = SliceIds.OrgaoCrato,
			Modalidade = "dispensa",
			Objeto = "Aquisicao do tradicional bolo com tematica alusiva ao aniversario de 260 anos do municipio, em alusao ao aniversario do municipio FestCrato 2024.",
			Ano = 2024,
			ValorHomologado = 9612m,
			PublicadoEm = Instant.FromUtc(2024, 7, 2, 17, 38),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoAriquemes = new Contratacao
		{
			Id = SliceIds.ContratacaoAriquemes,
			PncpId = "04104816000116-1-000206/2024",
			OrgaoId = SliceIds.OrgaoAriquemes,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de Preco para eventual aquisicao de material de limpeza e higiene, material de consumo para atender as Secretarias Municipais da Prefeitura Municipal de Ariquemes/RO, por um periodo de 12 meses.",
			Ano = 2024,
			ValorHomologado = 68280.36m,
			PublicadoEm = Instant.FromUtc(2024, 9, 16, 9, 20),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoColatina = new Contratacao
		{
			Id = SliceIds.ContratacaoColatina,
			PncpId = "27165729000174-1-000253/2024",
			OrgaoId = SliceIds.OrgaoColatina,
			Modalidade = "dispensa",
			Objeto = "Contratacao de empresa especializada na prestacao de servico de fornecimento de licenca de uso de ferramenta de pesquisa e comparacao de precos.",
			Ano = 2024,
			ValorHomologado = 19500m,
			PublicadoEm = Instant.FromUtc(2024, 11, 14, 14, 43),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCastanhal = new Contratacao
		{
			Id = SliceIds.ContratacaoCastanhal,
			PncpId = "05121991000184-1-000017/2024",
			OrgaoId = SliceIds.OrgaoCastanhal,
			Modalidade = "pregao eletronico",
			Objeto = "Contratacao de empresa especializada para fornecimento de agua mineral em embalagem de 200ml, destinado a atender as necessidades das diversas Secretarias/Fundos Municipais e o Instituto de Previdencia deste municipio de Castanhal/PA por um periodo de 12 (doze) meses.",
			Ano = 2024,
			ValorHomologado = 32930m,
			PublicadoEm = Instant.FromUtc(2024, 8, 22, 7, 5),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoDivinopolis = new Contratacao
		{
			Id = SliceIds.ContratacaoDivinopolis,
			PncpId = "18291351000164-1-000236/2024",
			OrgaoId = SliceIds.OrgaoDivinopolis,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de 01 (uma) cadeira digitador, conforme termo de referencia, para Secretaria Municipal de Fazenda.",
			Ano = 2024,
			ValorHomologado = 1819.55m,
			PublicadoEm = Instant.FromUtc(2024, 8, 28, 17, 18),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoPetropolis = new Contratacao
		{
			Id = SliceIds.ContratacaoPetropolis,
			PncpId = "29138344000143-1-000165/2024",
			OrgaoId = SliceIds.OrgaoPetropolis,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de Papel para Plotter HP Design Jet T830",
			Ano = 2024,
			ValorHomologado = 2099.96m,
			PublicadoEm = Instant.FromUtc(2024, 6, 12, 18, 42),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoIpatinga = new Contratacao
		{
			Id = SliceIds.ContratacaoIpatinga,
			PncpId = "19876424000142-1-000142/2024",
			OrgaoId = SliceIds.OrgaoIpatinga,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de 1 (uma) betoneira para atender as necessidades da Secretaria Municipal de Obras Publicas, conforme termo de referencias.",
			Ano = 2024,
			ValorHomologado = 3890m,
			PublicadoEm = Instant.FromUtc(2024, 12, 3, 7, 3),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoMacae = new Contratacao
		{
			Id = SliceIds.ContratacaoMacae,
			PncpId = "29115474000160-1-000119/2024",
			OrgaoId = SliceIds.OrgaoMacae,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de coletes em brim, para identificacao dos servidores da Secretaria Municipal de Politicas para as Mulheres.",
			Ano = 2024,
			ValorHomologado = 2087.64m,
			PublicadoEm = Instant.FromUtc(2024, 10, 31, 11, 46),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSantaLuzia = new Contratacao
		{
			Id = SliceIds.ContratacaoSantaLuzia,
			PncpId = "18715409000150-1-000027/2024",
			OrgaoId = SliceIds.OrgaoSantaLuzia,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de cadeira giratoria escritorio para obeso",
			Ano = 2024,
			ValorHomologado = 1647.01m,
			PublicadoEm = Instant.FromUtc(2024, 7, 3, 17, 1),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoNovaFriburgo = new Contratacao
		{
			Id = SliceIds.ContratacaoNovaFriburgo,
			PncpId = "28606630000123-1-000093/2024",
			OrgaoId = SliceIds.OrgaoNovaFriburgo,
			Modalidade = "dispensa",
			Objeto = "Contratacao de empresa especializada para o fornecimento de papel toalha interfolhado, para atender as necessidades das Secretarias Municipais.",
			Ano = 2024,
			ValorHomologado = 8000m,
			PublicadoEm = Instant.FromUtc(2024, 10, 8, 11, 7),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoMarilia = new Contratacao
		{
			Id = SliceIds.ContratacaoMarilia,
			PncpId = "44477909000100-1-000487/2024",
			OrgaoId = SliceIds.OrgaoMarilia,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de Precos visando a eventual aquisicao de cestas de alimentos destinadas aos servidores ativos da Prefeitura Municipal de Marilia e AMAE.",
			Ano = 2024,
			ValorHomologado = 401.3m,
			PublicadoEm = Instant.FromUtc(2024, 10, 8, 7, 11),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoBalneario = new Contratacao
		{
			Id = SliceIds.ContratacaoBalneario,
			PncpId = "83102285000107-1-000442/2024",
			OrgaoId = SliceIds.OrgaoBalneario,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de aparelho/sistema de ergometria para realizacao de exames de diagnostico em cardiologia.",
			Ano = 2024,
			ValorHomologado = 18500m,
			PublicadoEm = Instant.FromUtc(2024, 9, 19, 7, 9),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoItaqua = new Contratacao
		{
			Id = SliceIds.ContratacaoItaqua,
			PncpId = "46316600000164-1-000239/2024",
			OrgaoId = SliceIds.OrgaoItaqua,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de kits congelados para distribuicao entre os servidores efetivos, estagiarios e comissionados da Prefeitura Municipal de Itaquaquecetuba.",
			Ano = 2024,
			ValorHomologado = 609.49m,
			PublicadoEm = Instant.FromUtc(2024, 11, 26, 7, 9),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoPraiaGrande = new Contratacao
		{
			Id = SliceIds.ContratacaoPraiaGrande,
			PncpId = "46177531000155-1-000109/2024",
			OrgaoId = SliceIds.OrgaoPraiaGrande,
			Modalidade = "dispensa",
			Objeto = "Aquisicao de armarinhos e tecidos para o fundo social de solidariedade",
			Ano = 2024,
			ValorHomologado = 31339.03m,
			PublicadoEm = Instant.FromUtc(2024, 10, 31, 15, 54),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSaoJoseDosPinhais = new Contratacao
		{
			Id = SliceIds.ContratacaoSaoJoseDosPinhais,
			PncpId = "76105543000135-1-000085/2024",
			OrgaoId = SliceIds.OrgaoSaoJoseDosPinhais,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de Precos para aquisicao de material consumiveis - descartaveis destinados a realizacao de exames.",
			Ano = 2024,
			ValorHomologado = 275195.1m,
			PublicadoEm = Instant.FromUtc(2024, 7, 15, 7, 0),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoSuzano = new Contratacao
		{
			Id = SliceIds.ContratacaoSuzano,
			PncpId = "46523056000121-1-000058/2024",
			OrgaoId = SliceIds.OrgaoSuzano,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de cesta basica",
			Ano = 2024,
			ValorHomologado = 256010m,
			PublicadoEm = Instant.FromUtc(2024, 7, 17, 7, 11),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoGuaruja = new Contratacao
		{
			Id = SliceIds.ContratacaoGuaruja,
			PncpId = "44959021000104-1-000305/2024",
			OrgaoId = SliceIds.OrgaoGuaruja,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de preco para aquisicao de materiais hidraulicos para atender as Secretarias do Municipio de Guaruja.",
			Ano = 2024,
			ValorHomologado = 50077028.25m,
			PublicadoEm = Instant.FromUtc(2024, 10, 2, 7, 30),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoCotia = new Contratacao
		{
			Id = SliceIds.ContratacaoCotia,
			PncpId = "46523049000120-1-000203/2024",
			OrgaoId = SliceIds.OrgaoCotia,
			Modalidade = "pregao eletronico",
			Objeto = "Contratacao de empresa especializada para prestacao de servico de Transporte Escolar Gratuito - TEG",
			Ano = 2024,
			ValorHomologado = 104235750m,
			PublicadoEm = Instant.FromUtc(2024, 8, 14, 7, 17),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoParauapebas = new Contratacao
		{
			Id = SliceIds.ContratacaoParauapebas,
			PncpId = "22980999000115-1-000150/2024",
			OrgaoId = SliceIds.OrgaoParauapebas,
			Modalidade = "pregao eletronico",
			Objeto = "Aquisicao de forma continuada de gas liquefeito de petroleo GLP (Gas de cozinha).",
			Ano = 2024,
			ValorHomologado = 79800m,
			PublicadoEm = Instant.FromUtc(2024, 11, 29, 7, 22),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoJacarei = new Contratacao
		{
			Id = SliceIds.ContratacaoJacarei,
			PncpId = "46694139000183-1-001263/2024",
			OrgaoId = SliceIds.OrgaoJacarei,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de Precos para fornecimento de EPI's",
			Ano = 2024,
			ValorHomologado = 421978.9m,
			PublicadoEm = Instant.FromUtc(2024, 10, 8, 7, 15),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoItaborai = new Contratacao
		{
			Id = SliceIds.ContratacaoItaborai,
			PncpId = "28741080000155-1-000038/2024",
			OrgaoId = SliceIds.OrgaoItaborai,
			Modalidade = "pregao eletronico",
			Objeto = "Registro de precos para aquisicao de material ludico pedagogico",
			Ano = 2024,
			ValorHomologado = 243131.11m,
			PublicadoEm = Instant.FromUtc(2024, 9, 19, 7, 22),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var contratacaoMarica = new Contratacao
		{
			Id = SliceIds.ContratacaoMarica,
			PncpId = "29131075000193-1-000135/2024",
			OrgaoId = SliceIds.OrgaoMarica,
			Modalidade = "dispensa",
			Objeto = "Fornecimento de bombas d'agua e chaves-boias sensor de nivel para atender as necessidades do Arquivo Publico Municipal.",
			Ano = 2024,
			ValorHomologado = 764.9m,
			PublicadoEm = Instant.FromUtc(2024, 9, 27, 16, 43),
			Source = "compras.gov.br",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemNiteroi = new Item
		{
			Id = SliceIds.ItemNiteroi,
			ContratacaoId = SliceIds.ContratacaoNiteroi,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Detergente neutro 5L",
			Catmat = "654321",
			Quantidade = 8m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 15m,
			ValorTotal = 120m,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemBauru = new Item
		{
			Id = SliceIds.ItemBauru,
			ContratacaoId = SliceIds.ContratacaoBauru,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Resma papel A4 Bauru",
			Catmat = "654321",
			Quantidade = 16m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 5m,
			ValorTotal = 80m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCaxias = new Item
		{
			Id = SliceIds.ItemCaxias,
			ContratacaoId = SliceIds.ContratacaoCaxias,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Suporte para monitor LCD",
			Catmat = "601992",
			Quantidade = 100m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 110m,
			ValorTotal = 11000m,
			Uf = "RS",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemJoinville = new Item
		{
			Id = SliceIds.ItemJoinville,
			ContratacaoId = SliceIds.ContratacaoJoinville,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Leitora codigo de barras",
			Catmat = "617529",
			Quantidade = 35m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 948m,
			ValorTotal = 33180m,
			Uf = "SC",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemUberlandia = new Item
		{
			Id = SliceIds.ItemUberlandia,
			ContratacaoId = SliceIds.ContratacaoUberlandia,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Coturno",
			Catmat = "446381",
			Quantidade = 127m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 276m,
			ValorTotal = 35052m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemLondrina = new Item
		{
			Id = SliceIds.ItemLondrina,
			ContratacaoId = SliceIds.ContratacaoLondrina,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Clindamicina",
			Catmat = "268436",
			Quantidade = 10000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1.0999m,
			ValorTotal = 10999m,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemFeira = new Item
		{
			Id = SliceIds.ItemFeira,
			ContratacaoId = SliceIds.ContratacaoFeira,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Agua mineral natural",
			Catmat = "445484",
			Quantidade = 2000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 33.6m,
			ValorTotal = 67200m,
			Uf = "BA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCaruaru = new Item
		{
			Id = SliceIds.ItemCaruaru,
			ContratacaoId = SliceIds.ContratacaoCaruaru,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Placa sinalizadora",
			Catmat = "383339",
			Quantidade = 375m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 79m,
			ValorTotal = 29625m,
			Uf = "PE",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemAnapolis = new Item
		{
			Id = SliceIds.ItemAnapolis,
			ContratacaoId = SliceIds.ContratacaoAnapolis,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Scanner",
			Catmat = "611695",
			Quantidade = 8m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1642.61m,
			ValorTotal = 13140.88m,
			Uf = "GO",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemVilaVelha = new Item
		{
			Id = SliceIds.ItemVilaVelha,
			ContratacaoId = SliceIds.ContratacaoVilaVelha,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Revelador radiologico",
			Catmat = "405620",
			Quantidade = 420m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 7.48m,
			ValorTotal = 3141.6m,
			Uf = "ES",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCampinaGrande = new Item
		{
			Id = SliceIds.ItemCampinaGrande,
			ContratacaoId = SliceIds.ContratacaoCampinaGrande,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Memoria Ram",
			Catmat = "618288",
			Quantidade = 4m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 209.99m,
			ValorTotal = 839.96m,
			Uf = "PB",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCaucaia = new Item
		{
			Id = SliceIds.ItemCaucaia,
			ContratacaoId = SliceIds.ContratacaoCaucaia,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Bloco receituario medico",
			Catmat = "485443",
			Quantidade = 1000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 8.55m,
			ValorTotal = 8550m,
			Uf = "CE",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemImperatriz = new Item
		{
			Id = SliceIds.ItemImperatriz,
			ContratacaoId = SliceIds.ContratacaoImperatriz,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Livro didatico",
			Catmat = "464257",
			Quantidade = 100m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 525.3m,
			ValorTotal = 52530m,
			Uf = "MA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemArapiraca = new Item
		{
			Id = SliceIds.ItemArapiraca,
			ContratacaoId = SliceIds.ContratacaoArapiraca,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Lamotrigina",
			Catmat = "602451",
			Quantidade = 18m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 16m,
			ValorTotal = 288m,
			Uf = "AL",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemDourados = new Item
		{
			Id = SliceIds.ItemDourados,
			ContratacaoId = SliceIds.ContratacaoDourados,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Reagente para diagnostico clinico",
			Catmat = "333587",
			Quantidade = 12m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 126m,
			ValorTotal = 1512m,
			Uf = "MS",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemMaraba = new Item
		{
			Id = SliceIds.ItemMaraba,
			ContratacaoId = SliceIds.ContratacaoMaraba,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Fogao gas",
			Catmat = "425200",
			Quantidade = 4m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 849.99m,
			ValorTotal = 3399.96m,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemVarzeaGrande = new Item
		{
			Id = SliceIds.ItemVarzeaGrande,
			ContratacaoId = SliceIds.ContratacaoVarzeaGrande,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Microcomputador",
			Catmat = "606229",
			Quantidade = 2m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 26021m,
			ValorTotal = 52042m,
			Uf = "MT",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemJiParana = new Item
		{
			Id = SliceIds.ItemJiParana,
			ContratacaoId = SliceIds.ContratacaoJiParana,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Assinatura de banco de imagens",
			Catmat = "30130",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 38540m,
			ValorTotal = 38540m,
			Uf = "RO",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemParnamirim = new Item
		{
			Id = SliceIds.ItemParnamirim,
			ContratacaoId = SliceIds.ContratacaoParnamirim,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Automovel",
			Catmat = "430273",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 78500m,
			ValorTotal = 78500m,
			Uf = "RN",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCruzeiroDoSul = new Item
		{
			Id = SliceIds.ItemCruzeiroDoSul,
			ContratacaoId = SliceIds.ContratacaoCruzeiroDoSul,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Grade niveladora",
			Catmat = "463162",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 26784.45m,
			ValorTotal = 26784.45m,
			Uf = "AC",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSantana = new Item
		{
			Id = SliceIds.ItemSantana,
			ContratacaoId = SliceIds.ContratacaoSantana,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Prestacao de servicos bancarios",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1m,
			ValorTotal = 1m,
			Uf = "AP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemRorainopolis = new Item
		{
			Id = SliceIds.ItemRorainopolis,
			ContratacaoId = SliceIds.ContratacaoRorainopolis,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Ambulancia",
			Catmat = "621643",
			Quantidade = 3m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 324000m,
			ValorTotal = 972000m,
			Uf = "RR",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemMaringa = new Item
		{
			Id = SliceIds.ItemMaringa,
			ContratacaoId = SliceIds.ContratacaoMaringa,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Enalapril maleato",
			Catmat = "267652",
			Quantidade = 2505672m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 0.045m,
			ValorTotal = 112755.24m,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemTaubate = new Item
		{
			Id = SliceIds.ItemTaubate,
			ContratacaoId = SliceIds.ContratacaoTaubate,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Eletrodos para eletroencefalograma",
			Catmat = "7021",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 8250m,
			ValorTotal = 8250m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCascavel = new Item
		{
			Id = SliceIds.ItemCascavel,
			ContratacaoId = SliceIds.ContratacaoCascavel,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Motocicleta",
			Catmat = "318890",
			Quantidade = 3m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 65370m,
			ValorTotal = 196110m,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemJuizDeFora = new Item
		{
			Id = SliceIds.ItemJuizDeFora,
			ContratacaoId = SliceIds.ContratacaoJuizDeFora,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Pembrolizumabe",
			Catmat = "440269",
			Quantidade = 10m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 16021.4m,
			ValorTotal = 160214m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemFoz = new Item
		{
			Id = SliceIds.ItemFoz,
			ContratacaoId = SliceIds.ContratacaoFoz,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Fermento",
			Catmat = "459596",
			Quantidade = 2500m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 16.47m,
			ValorTotal = 41175m,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSantaMaria = new Item
		{
			Id = SliceIds.ItemSantaMaria,
			ContratacaoId = SliceIds.ContratacaoSantaMaria,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Risperidona",
			Catmat = "272839",
			Quantidade = 200000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 0.141m,
			ValorTotal = 28182m,
			Uf = "RS",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemMontesClaros = new Item
		{
			Id = SliceIds.ItemMontesClaros,
			ContratacaoId = SliceIds.ContratacaoMontesClaros,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Manutencao prevencao combate incendio",
			Catmat = "21822",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 330811.34m,
			ValorTotal = 330811.34m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemGovernadorValadares = new Item
		{
			Id = SliceIds.ItemGovernadorValadares,
			ContratacaoId = SliceIds.ContratacaoGovernadorValadares,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Cartao controle acesso",
			Catmat = "618284",
			Quantidade = 30000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1.45m,
			ValorTotal = 43500m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCanoas = new Item
		{
			Id = SliceIds.ItemCanoas,
			ContratacaoId = SliceIds.ContratacaoCanoas,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Clorimetro",
			Catmat = "247827",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1667.07m,
			ValorTotal = 1667.07m,
			Uf = "RS",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemLages = new Item
		{
			Id = SliceIds.ItemLages,
			ContratacaoId = SliceIds.ContratacaoLages,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Sacola",
			Catmat = "229690",
			Quantidade = 30m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 97m,
			ValorTotal = 2910m,
			Uf = "SC",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSantarem = new Item
		{
			Id = SliceIds.ItemSantarem,
			ContratacaoId = SliceIds.ContratacaoSantarem,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Obras civis publicas",
			Catmat = "5622",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 326424.56m,
			ValorTotal = 326424.56m,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemRioVerde = new Item
		{
			Id = SliceIds.ItemRioVerde,
			ContratacaoId = SliceIds.ContratacaoRioVerde,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Lampada refletora",
			Catmat = "485659",
			Quantidade = 10m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 45m,
			ValorTotal = 450m,
			Uf = "GO",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemPauloAfonso = new Item
		{
			Id = SliceIds.ItemPauloAfonso,
			ContratacaoId = SliceIds.ContratacaoPauloAfonso,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Acucar",
			Catmat = "603269",
			Quantidade = 2000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 4.42m,
			ValorTotal = 8840m,
			Uf = "BA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSaoLourenco = new Item
		{
			Id = SliceIds.ItemSaoLourenco,
			ContratacaoId = SliceIds.ContratacaoSaoLourenco,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Ventilador",
			Catmat = "461897",
			Quantidade = 375m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 194m,
			ValorTotal = 72750m,
			Uf = "PE",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCrato = new Item
		{
			Id = SliceIds.ItemCrato,
			ContratacaoId = SliceIds.ContratacaoCrato,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Bolo Alimenticio",
			Catmat = "308385",
			Quantidade = 200m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 48.06m,
			ValorTotal = 9612m,
			Uf = "CE",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemAriquemes = new Item
		{
			Id = SliceIds.ItemAriquemes,
			ContratacaoId = SliceIds.ContratacaoAriquemes,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Alcool Etilico",
			Catmat = "269941",
			Quantidade = 6909m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 6.88m,
			ValorTotal = 47533.92m,
			Uf = "RO",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemColatina = new Item
		{
			Id = SliceIds.ItemColatina,
			ContratacaoId = SliceIds.ContratacaoColatina,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Assinatura - Publicacao Informatizada",
			Catmat = "21040",
			Quantidade = 5m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 3900m,
			ValorTotal = 19500m,
			Uf = "ES",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCastanhal = new Item
		{
			Id = SliceIds.ItemCastanhal,
			ContratacaoId = SliceIds.ContratacaoCastanhal,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Agua Mineral Natural",
			Catmat = "613476",
			Quantidade = 89000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 0.37m,
			ValorTotal = 32930m,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemDivinopolis = new Item
		{
			Id = SliceIds.ItemDivinopolis,
			ContratacaoId = SliceIds.ContratacaoDivinopolis,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Cadeira digitador",
			Catmat = "246097",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1819.55m,
			ValorTotal = 1819.55m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemPetropolis = new Item
		{
			Id = SliceIds.ItemPetropolis,
			ContratacaoId = SliceIds.ContratacaoPetropolis,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Bobina Papel Impressora aplicacao: impressora plotter, comprimento: 50, gramatura: 75, largura: 914, tipo papel: sulfite Papel para Plotter (Bobina) 75 GR 610x50",
			Catmat = "275143",
			Quantidade = 12m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 133.33m,
			ValorTotal = 1599.96m,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemIpatinga = new Item
		{
			Id = SliceIds.ItemIpatinga,
			ContratacaoId = SliceIds.ContratacaoIpatinga,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Betoneira",
			Catmat = "487731",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 3890m,
			ValorTotal = 3890m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemMacae = new Item
		{
			Id = SliceIds.ItemMacae,
			ContratacaoId = SliceIds.ContratacaoMacae,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Colete Identificacao",
			Catmat = "482286",
			Quantidade = 36m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 57.99m,
			ValorTotal = 2087.64m,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSantaLuzia = new Item
		{
			Id = SliceIds.ItemSantaLuzia,
			ContratacaoId = SliceIds.ContratacaoSantaLuzia,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Cadeira escritorio",
			Catmat = "613647",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1647.01m,
			ValorTotal = 1647.01m,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemNovaFriburgo = new Item
		{
			Id = SliceIds.ItemNovaFriburgo,
			ContratacaoId = SliceIds.ContratacaoNovaFriburgo,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Toalha De Papel",
			Catmat = "436328",
			Quantidade = 1000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 8m,
			ValorTotal = 8000m,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemMarilia = new Item
		{
			Id = SliceIds.ItemMarilia,
			ContratacaoId = SliceIds.ContratacaoMarilia,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Macarrao",
			Catmat = "480420",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 401.3m,
			ValorTotal = 401.3m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemBalneario = new Item
		{
			Id = SliceIds.ItemBalneario,
			ContratacaoId = SliceIds.ContratacaoBalneario,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Cardiologia - Teste Ergometrico",
			Catmat = "6505",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 18500m,
			ValorTotal = 18500m,
			Uf = "SC",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemItaqua = new Item
		{
			Id = SliceIds.ItemItaqua,
			ContratacaoId = SliceIds.ContratacaoItaqua,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Pao",
			Catmat = "460400",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 14.04m,
			ValorTotal = 14.04m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemPraiaGrande = new Item
		{
			Id = SliceIds.ItemPraiaGrande,
			ContratacaoId = SliceIds.ContratacaoPraiaGrande,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Tnt",
			Catmat = "300805",
			Quantidade = 3m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 249.99m,
			ValorTotal = 749.97m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSaoJoseDosPinhais = new Item
		{
			Id = SliceIds.ItemSaoJoseDosPinhais,
			ContratacaoId = SliceIds.ContratacaoSaoJoseDosPinhais,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Swab",
			Catmat = "480902",
			Quantidade = 32000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 0.13m,
			ValorTotal = 4160m,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemSuzano = new Item
		{
			Id = SliceIds.ItemSuzano,
			ContratacaoId = SliceIds.ContratacaoSuzano,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Sal",
			Catmat = "291893",
			Quantidade = 1000m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 2.56m,
			ValorTotal = 2560m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemGuaruja = new Item
		{
			Id = SliceIds.ItemGuaruja,
			ContratacaoId = SliceIds.ContratacaoGuaruja,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Pia",
			Catmat = "481480",
			Quantidade = 204m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 3934.6m,
			ValorTotal = 802658.4m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemCotia = new Item
		{
			Id = SliceIds.ItemCotia,
			ContratacaoId = SliceIds.ContratacaoCotia,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Transporte Rodoviario - Pessoal por Automoveis",
			Catmat = "3239",
			Quantidade = 1680m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 28650m,
			ValorTotal = 48132000m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemParauapebas = new Item
		{
			Id = SliceIds.ItemParauapebas,
			ContratacaoId = SliceIds.ContratacaoParauapebas,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Botijao Para Gas",
			Catmat = null,
			Quantidade = 4m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 1486m,
			ValorTotal = 5944m,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemJacarei = new Item
		{
			Id = SliceIds.ItemJacarei,
			ContratacaoId = SliceIds.ContratacaoJacarei,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Macacao",
			Catmat = "221026",
			Quantidade = 132m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 349.51m,
			ValorTotal = 46135.32m,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemItaborai = new Item
		{
			Id = SliceIds.ItemItaborai,
			ContratacaoId = SliceIds.ContratacaoItaborai,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Cola",
			Catmat = "619622",
			Quantidade = 400m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 11.16m,
			ValorTotal = 4464m,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};
		var itemMarica = new Item
		{
			Id = SliceIds.ItemMarica,
			ContratacaoId = SliceIds.ContratacaoMarica,
			FornecedorId = SliceIds.FornecedorExtra,
			Descricao = "Bomba",
			Catmat = "607508",
			Quantidade = 1m,
			UnidadeMedida = "UN",
			UnidadeCanonica = "un",
			ValorUnitario = 198.4m,
			ValorTotal = 198.4m,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		};

		db.Orgaos.AddRange(orgao, hidden, suspendTarget, pageAlfa, pageBeta, niteroi, bauru, caxias, joinville, uberlandia, londrina, feira, caruaru, anapolis, vilaVelha, campinaGrande, caucaia, imperatriz, arapiraca, dourados, maraba, varzeaGrande, jiParana, parnamirim, cruzeiroDoSul, santana, rorainopolis, maringa, taubate, cascavel, juizDeFora, foz, santaMaria, montesClaros, governadorValadares, canoas, lages, santarem, rioVerde, pauloAfonso, saoLourenco, crato, ariquemes, colatina, castanhal, divinopolis, petropolis, ipatinga, macae, santaLuzia, novaFriburgo, marilia, balneario, itaqua, praiaGrande, saoJoseDosPinhais, suzano, guaruja, cotia, parauapebas, jacarei, itaborai, marica);
		db.Fornecedores.AddRange(fornecedor, fornecedorExtra);
		db.Contratacoes.AddRange(contratacao, contratacaoNiteroi, contratacaoBauru, contratacaoCaxias, contratacaoJoinville, contratacaoUberlandia, contratacaoLondrina, contratacaoFeira, contratacaoCaruaru, contratacaoAnapolis, contratacaoVilaVelha, contratacaoCampinaGrande, contratacaoCaucaia, contratacaoImperatriz, contratacaoArapiraca, contratacaoDourados, contratacaoMaraba, contratacaoVarzeaGrande, contratacaoJiParana, contratacaoParnamirim, contratacaoCruzeiroDoSul, contratacaoSantana, contratacaoRorainopolis, contratacaoMaringa, contratacaoTaubate, contratacaoCascavel, contratacaoJuizDeFora, contratacaoFoz, contratacaoSantaMaria, contratacaoMontesClaros, contratacaoGovernadorValadares, contratacaoCanoas, contratacaoLages, contratacaoSantarem, contratacaoRioVerde, contratacaoPauloAfonso, contratacaoSaoLourenco, contratacaoCrato, contratacaoAriquemes, contratacaoColatina, contratacaoCastanhal, contratacaoDivinopolis, contratacaoPetropolis, contratacaoIpatinga, contratacaoMacae, contratacaoSantaLuzia, contratacaoNovaFriburgo, contratacaoMarilia, contratacaoBalneario, contratacaoItaqua, contratacaoPraiaGrande, contratacaoSaoJoseDosPinhais, contratacaoSuzano, contratacaoGuaruja, contratacaoCotia, contratacaoParauapebas, contratacaoJacarei, contratacaoItaborai, contratacaoMarica);
		db.Items.AddRange(item1, item2, itemNiteroi, itemBauru, itemCaxias, itemJoinville, itemUberlandia, itemLondrina, itemFeira, itemCaruaru, itemAnapolis, itemVilaVelha, itemCampinaGrande, itemCaucaia, itemImperatriz, itemArapiraca, itemDourados, itemMaraba, itemVarzeaGrande, itemJiParana, itemParnamirim, itemCruzeiroDoSul, itemSantana, itemRorainopolis, itemMaringa, itemTaubate, itemCascavel, itemJuizDeFora, itemFoz, itemSantaMaria, itemMontesClaros, itemGovernadorValadares, itemCanoas, itemLages, itemSantarem, itemRioVerde, itemPauloAfonso, itemSaoLourenco, itemCrato, itemAriquemes, itemColatina, itemCastanhal, itemDivinopolis, itemPetropolis, itemIpatinga, itemMacae, itemSantaLuzia, itemNovaFriburgo, itemMarilia, itemBalneario, itemItaqua, itemPraiaGrande, itemSaoJoseDosPinhais, itemSuzano, itemGuaruja, itemCotia, itemParauapebas, itemJacarei, itemItaborai, itemMarica);
	}

	private static JsonSerializerOptions CreateJson()
	{
		var options = new JsonSerializerOptions
		{
			PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
			PropertyNameCaseInsensitive = true,
			Converters = { new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower) },
		};
		options.ConfigureForNodaTime(DateTimeZoneProviders.Tzdb);
		return options;
	}

	private sealed class Factory : WebApplicationFactory<Program>
	{
		private readonly string _dbPath = Path.Combine(
			Path.GetTempPath(),
			$"compras-it-{Guid.NewGuid():N}.db");

		public FakeClock Clock { get; } = new(Start);

		protected override void ConfigureWebHost(IWebHostBuilder builder)
		{
			builder.UseEnvironment("Testing");
			builder.UseSetting("App:MethodologyVersion", "0.1");
			builder.UseSetting("App:Host", "127.0.0.1");
			builder.UseSetting("App:Port", "5080");
			builder.ConfigureServices(services =>
			{
				foreach (var descriptor in services.Where(d => d.ServiceType == typeof(IClock)).ToList())
					_ = services.Remove(descriptor);
				services.AddSingleton<IClock>(Clock);

				var existing = services
					.Where(descriptor =>
						descriptor.ServiceType == typeof(ApplicationDbContext)
						|| descriptor.ServiceType == typeof(DbContextOptions<ApplicationDbContext>)
						|| descriptor.ServiceType == typeof(DbContextOptions)
						|| descriptor.ServiceType.IsGenericType
							&& descriptor.ServiceType.GetGenericTypeDefinition() == typeof(DbContextOptions<>))
					.ToList();
				foreach (var descriptor in existing)
					_ = services.Remove(descriptor);

				services.AddDbContext<ApplicationDbContext>((sp, options) =>
					options.UseSqlite($"Data Source={_dbPath}")
						.AddInterceptors(
							new TimestampInterceptor(sp.GetRequiredService<IClock>()),
							new CpfGuardInterceptor()));
			});
		}

		protected override void Dispose(bool disposing)
		{
			base.Dispose(disposing);
			TryDelete(_dbPath);
			TryDelete(_dbPath + "-wal");
			TryDelete(_dbPath + "-shm");
		}

		private static void TryDelete(string path)
		{
			try
			{
				if (File.Exists(path))
					File.Delete(path);
			}
			catch (IOException)
			{
			}
		}
	}
}
