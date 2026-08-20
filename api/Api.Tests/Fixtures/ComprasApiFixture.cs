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

		db.Orgaos.AddRange(orgao, hidden, suspendTarget, pageAlfa, pageBeta, niteroi, bauru, caxias, joinville, uberlandia, londrina, feira, caruaru, anapolis, vilaVelha, campinaGrande, caucaia, imperatriz, arapiraca, dourados, maraba, varzeaGrande, jiParana, parnamirim, cruzeiroDoSul, santana, rorainopolis);
		db.Fornecedores.AddRange(fornecedor, fornecedorExtra);
		db.Contratacoes.AddRange(contratacao, contratacaoNiteroi, contratacaoBauru, contratacaoCaxias, contratacaoJoinville, contratacaoUberlandia, contratacaoLondrina, contratacaoFeira, contratacaoCaruaru, contratacaoAnapolis, contratacaoVilaVelha, contratacaoCampinaGrande, contratacaoCaucaia, contratacaoImperatriz, contratacaoArapiraca, contratacaoDourados, contratacaoMaraba, contratacaoVarzeaGrande, contratacaoJiParana, contratacaoParnamirim, contratacaoCruzeiroDoSul, contratacaoSantana, contratacaoRorainopolis);
		db.Items.AddRange(item1, item2, itemNiteroi, itemBauru, itemCaxias, itemJoinville, itemUberlandia, itemLondrina, itemFeira, itemCaruaru, itemAnapolis, itemVilaVelha, itemCampinaGrande, itemCaucaia, itemImperatriz, itemArapiraca, itemDourados, itemMaraba, itemVarzeaGrande, itemJiParana, itemParnamirim, itemCruzeiroDoSul, itemSantana, itemRorainopolis);
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
