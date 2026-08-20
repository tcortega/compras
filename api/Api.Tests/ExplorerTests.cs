using System.Net;
using System.Text.Json;
using Api.Client;
using Api.Tests.Fixtures;

namespace Api.Tests;

public sealed class ExplorerTests(ComprasApiFixture fixture) : IClassFixture<ComprasApiFixture>
{
	private static readonly Coverage s_orgaoCoverage = new()
	{
		N = 2,
		Uf = SliceIds.Uf,
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_orgao = new()
	{
		Id = SliceIds.Orgao,
		Cnpj = "28747223000191",
		RazaoSocial = "Municipio de Volta Redonda",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = SliceIds.Uf,
		MunicipioIbge = "3306305",
		MunicipioNome = "Volta Redonda",
		Coverage = s_orgaoCoverage,
	};

	private static readonly FornecedorRecord s_fornecedor = new()
	{
		Id = SliceIds.Fornecedor,
		Cnpj = "12345678000195",
		RazaoSocial = "Papelaria Central Ltda",
		OpenedOn = new LocalDate(2023, 1, 15),
		Cnae = "4761-0/01",
		Coverage = new()
		{
			N = 2,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_itemSlice = new()
	{
		N = 2,
		Uf = SliceIds.Uf,
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly ItemRecord s_item1 = new()
	{
		Id = SliceIds.Item1,
		ContratacaoId = SliceIds.Contratacao,
		FornecedorId = SliceIds.Fornecedor,
		Descricao = "Resma papel A4",
		Catmat = "123456",
		Catser = null,
		Quantidade = 100m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 8m,
		ValorTotal = 800m,
		Uf = SliceIds.Uf,
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = s_itemSlice,
	};

	private static readonly ItemRecord s_item2 = new()
	{
		Id = SliceIds.Item2,
		ContratacaoId = SliceIds.Contratacao,
		FornecedorId = SliceIds.Fornecedor,
		Descricao = "Caneta esferografica azul",
		Catmat = "123456",
		Catser = null,
		Quantidade = 200m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 2m,
		ValorTotal = 400m,
		Uf = SliceIds.Uf,
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = s_itemSlice,
	};

	private static readonly Coverage s_pageOrgaoRecord = new()
	{
		N = 0,
		Uf = "TO",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_pageOrgaoAlfa = new()
	{
		Id = SliceIds.PageOrgaoAlfa,
		Cnpj = "22222222000191",
		RazaoSocial = "Paginacao Alfa",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "TO",
		MunicipioIbge = "1721000",
		MunicipioNome = "Palmas",
		Coverage = s_pageOrgaoRecord,
	};

	private static readonly OrgaoRecord s_pageOrgaoBeta = new()
	{
		Id = SliceIds.PageOrgaoBeta,
		Cnpj = "33333333000191",
		RazaoSocial = "Paginacao Beta",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "TO",
		MunicipioIbge = "1721000",
		MunicipioNome = "Palmas",
		Coverage = s_pageOrgaoRecord,
	};

	private static readonly ContratacaoRecord s_contratacao = new()
	{
		Id = SliceIds.Contratacao,
		PncpId = "3306305-1-000001/2024",
		OrgaoId = SliceIds.Orgao,
		OrgaoRazaoSocial = "Municipio de Volta Redonda",
		Modalidade = "dispensa",
		Objeto = "Aquisicao de material de expediente",
		Ano = 2024,
		ValorHomologado = 1200m,
		PublicadoEm = Instant.FromUtc(2024, 3, 10, 14, 0),
		Source = "compras.gov.br",
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 2,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	[Fact]
	public async Task FullCycle_SearchBrowseDrillSuspend()
	{
		var client = fixture.GetClient();

		var orgaos = await client.ListOrgaos(q: "Volta", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			orgaos.Coverage);
		Assert.Equal(new[] { s_orgao }, orgaos.Items);
		await ValidateOrgao(client, s_orgao);

		var contratacoes = await client.ListContratacoes(orgaoId: SliceIds.Orgao, ano: 2024);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = "",
				MethodologyVersion = SliceIds.Methodology,
			},
			contratacoes.Coverage);
		Assert.Equal(new[] { s_contratacao }, contratacoes.Items);
		await ValidateContratacao(client, new()
		{
			Contratacao = s_contratacao,
			Items = [s_item2, s_item1],
		});

		var items = await client.ListItems(
			contratacaoId: SliceIds.Contratacao,
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = SliceIds.Uf,
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			items.Coverage);
		Assert.Equal(new[] { s_item2, s_item1 }, items.Items);
		await ValidateItem(client, new()
		{
			Item = s_item1,
			OrgaoId = SliceIds.Orgao,
			OrgaoRazaoSocial = "Municipio de Volta Redonda",
			FornecedorRazaoSocial = "Papelaria Central Ltda",
			ContratacaoPncpId = "3306305-1-000001/2024",
		});

		var fornecedores = await client.ListFornecedores(
			q: "Papelaria",
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = SliceIds.Uf,
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			fornecedores.Coverage);
		Assert.Equal(new[] { s_fornecedor }, fornecedores.Items);
		await ValidateFornecedor(client, s_fornecedor);

		var byFornecedor = await client.ListContratacoes(fornecedorId: SliceIds.Fornecedor);
		Assert.Equal(new[] { s_contratacao }, byFornecedor.Items);
		Assert.Equal(1, byFornecedor.Total);

		var hidden = await client.GetOrgao(SliceIds.HiddenOrgao);
		Assert.Equal(HttpStatusCode.NotFound, hidden.StatusCode);

		var suspended = await client.Suspend(new()
		{
			Kind = SuspendKind.Orgao,
			Id = SliceIds.SuspendTarget,
		});
		Assert.Equal(
			new SuspendResponse
			{
				Kind = SuspendKind.Orgao,
				Id = SliceIds.SuspendTarget,
				Suspended = true,
			},
			suspended.Content);

		var after = await client.ListOrgaos(q: "suspender");
		Assert.Equal(
			new Coverage
			{
				N = 0,
				Uf = "",
				Quarter = "",
				MethodologyVersion = SliceIds.Methodology,
			},
			after.Coverage);
		Assert.Empty(after.Items);
	}

	[Fact]
	public async Task GetUnknownOrgao_NotFound()
	{
		var response = await fixture.GetClient().GetOrgao(Guid.NewGuid());
		Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
	}

	[Fact]
	public async Task GetUnknownItem_NotFound()
	{
		var response = await fixture.GetClient().GetItem(Guid.NewGuid());
		Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
	}

	[Fact]
	public async Task GetUnknownContratacao_NotFound()
	{
		var response = await fixture.GetClient().GetContratacao(Guid.NewGuid());
		Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
	}

	[Fact]
	public async Task GetUnknownFornecedor_NotFound()
	{
		var response = await fixture.GetClient().GetFornecedor(Guid.NewGuid());
		Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
	}

	[Fact]
	public async Task FullCycle_TakeThenSkipPages()
	{
		var client = fixture.GetClient();
		var itemCoverage = new Coverage
		{
			N = 2,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		};
		var firstItems = await client.ListItems(
			contratacaoId: SliceIds.Contratacao,
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter,
			take: 1);
		Assert.Equal(new[] { s_item2 }, firstItems.Items);
		Assert.Equal(itemCoverage, firstItems.Coverage);
		Assert.Equal(2, firstItems.Total);

		var secondItems = await client.ListItems(
			contratacaoId: SliceIds.Contratacao,
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter,
			skip: 1,
			take: 1);
		Assert.Equal(new[] { s_item1 }, secondItems.Items);
		Assert.Equal(itemCoverage, secondItems.Coverage);
		Assert.Equal(2, secondItems.Total);

		var orgaoCoverage = new Coverage
		{
			N = 2,
			Uf = "TO",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		};
		var firstOrgaos = await client.ListOrgaos(
			uf: "TO",
			quarter: SliceIds.Quarter,
			take: 1);
		Assert.Equal(new[] { s_pageOrgaoAlfa }, firstOrgaos.Items);
		Assert.Equal(orgaoCoverage, firstOrgaos.Coverage);
		Assert.Equal(2, firstOrgaos.Total);

		var secondOrgaos = await client.ListOrgaos(
			uf: "TO",
			quarter: SliceIds.Quarter,
			skip: 1,
			take: 1);
		Assert.Equal(new[] { s_pageOrgaoBeta }, secondOrgaos.Items);
		Assert.Equal(orgaoCoverage, secondOrgaos.Coverage);
		Assert.Equal(2, secondOrgaos.Total);
	}

	private static readonly Coverage s_niteroiOrgaoCoverage = new()
	{
		N = 1,
		Uf = SliceIds.Uf,
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_niteroi = new()
	{
		Id = SliceIds.OrgaoNiteroi,
		Cnpj = "28521748000159",
		RazaoSocial = "Municipio de Niteroi",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = SliceIds.Uf,
		MunicipioIbge = "3303302",
		MunicipioNome = "Niteroi",
		Coverage = s_niteroiOrgaoCoverage,
	};

	private static readonly Coverage s_bauruOrgaoCoverage = new()
	{
		N = 1,
		Uf = "SP",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_bauru = new()
	{
		Id = SliceIds.OrgaoBauru,
		Cnpj = "46137410000180",
		RazaoSocial = "Municipio de Bauru",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "SP",
		MunicipioIbge = "3506003",
		MunicipioNome = "Bauru",
		Coverage = s_bauruOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemNiteroi = new()
	{
		Id = SliceIds.ItemNiteroi,
		ContratacaoId = SliceIds.ContratacaoNiteroi,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Detergente neutro 5L",
		Catmat = "654321",
		Catser = null,
		Quantidade = 8m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 15m,
		ValorTotal = 120m,
		Uf = SliceIds.Uf,
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemBauru = new()
	{
		Id = SliceIds.ItemBauru,
		ContratacaoId = SliceIds.ContratacaoBauru,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Resma papel A4 Bauru",
		Catmat = "654321",
		Catser = null,
		Quantidade = 16m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 5m,
		ValorTotal = 80m,
		Uf = "SP",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_caxiasOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RS",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_caxias = new()
	{
		Id = SliceIds.OrgaoCaxias,
		Cnpj = "88830609000139",
		RazaoSocial = "Municipio de Caxias do Sul",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RS",
		MunicipioIbge = "4305108",
		MunicipioNome = "Caxias do Sul",
		Coverage = s_caxiasOrgaoCoverage,
	};

	private static readonly Coverage s_joinvilleOrgaoCoverage = new()
	{
		N = 1,
		Uf = "SC",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_joinville = new()
	{
		Id = SliceIds.OrgaoJoinville,
		Cnpj = "83169623000110",
		RazaoSocial = "Municipio de Joinville",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "SC",
		MunicipioIbge = "4209102",
		MunicipioNome = "Joinville",
		Coverage = s_joinvilleOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemCaxias = new()
	{
		Id = SliceIds.ItemCaxias,
		ContratacaoId = SliceIds.ContratacaoCaxias,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Suporte para monitor LCD",
		Catmat = "601992",
		Catser = null,
		Quantidade = 100m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 110m,
		ValorTotal = 11000m,
		Uf = "RS",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RS",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemJoinville = new()
	{
		Id = SliceIds.ItemJoinville,
		ContratacaoId = SliceIds.ContratacaoJoinville,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Leitora codigo de barras",
		Catmat = "617529",
		Catser = null,
		Quantidade = 35m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 948m,
		ValorTotal = 33180m,
		Uf = "SC",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "SC",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_uberlandiaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_uberlandia = new()
	{
		Id = SliceIds.OrgaoUberlandia,
		Cnpj = "18431312000115",
		RazaoSocial = "Municipio de Uberlandia",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3170206",
		MunicipioNome = "Uberlandia",
		Coverage = s_uberlandiaOrgaoCoverage,
	};

	private static readonly Coverage s_londrinaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_londrina = new()
	{
		Id = SliceIds.OrgaoLondrina,
		Cnpj = "75771477000170",
		RazaoSocial = "Municipio de Londrina",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PR",
		MunicipioIbge = "4113700",
		MunicipioNome = "Londrina",
		Coverage = s_londrinaOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemUberlandia = new()
	{
		Id = SliceIds.ItemUberlandia,
		ContratacaoId = SliceIds.ContratacaoUberlandia,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Coturno",
		Catmat = "446381",
		Catser = null,
		Quantidade = 127m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 276m,
		ValorTotal = 35052m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemLondrina = new()
	{
		Id = SliceIds.ItemLondrina,
		ContratacaoId = SliceIds.ContratacaoLondrina,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Clindamicina",
		Catmat = "268436",
		Catser = null,
		Quantidade = 10000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1.0999m,
		ValorTotal = 10999m,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_feiraOrgaoCoverage = new()
	{
		N = 1,
		Uf = "BA",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_feira = new()
	{
		Id = SliceIds.OrgaoFeira,
		Cnpj = "14043574000151",
		RazaoSocial = "Municipio de Feira de Santana",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "BA",
		MunicipioIbge = "2910800",
		MunicipioNome = "Feira de Santana",
		Coverage = s_feiraOrgaoCoverage,
	};

	private static readonly Coverage s_caruaruOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PE",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_caruaru = new()
	{
		Id = SliceIds.OrgaoCaruaru,
		Cnpj = "10091536000113",
		RazaoSocial = "Municipio de Caruaru",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PE",
		MunicipioIbge = "2604106",
		MunicipioNome = "Caruaru",
		Coverage = s_caruaruOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemFeira = new()
	{
		Id = SliceIds.ItemFeira,
		ContratacaoId = SliceIds.ContratacaoFeira,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Agua mineral natural",
		Catmat = "445484",
		Catser = null,
		Quantidade = 2000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 33.6m,
		ValorTotal = 67200m,
		Uf = "BA",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "BA",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCaruaru = new()
	{
		Id = SliceIds.ItemCaruaru,
		ContratacaoId = SliceIds.ContratacaoCaruaru,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Placa sinalizadora",
		Catmat = "383339",
		Catser = null,
		Quantidade = 375m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 79m,
		ValorTotal = 29625m,
		Uf = "PE",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PE",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_anapolisOrgaoCoverage = new()
	{
		N = 1,
		Uf = "GO",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_anapolis = new()
	{
		Id = SliceIds.OrgaoAnapolis,
		Cnpj = "01067479000146",
		RazaoSocial = "Municipio de Anapolis",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "GO",
		MunicipioIbge = "5201108",
		MunicipioNome = "Anapolis",
		Coverage = s_anapolisOrgaoCoverage,
	};

	private static readonly Coverage s_vilaVelhaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "ES",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_vilaVelha = new()
	{
		Id = SliceIds.OrgaoVilaVelha,
		Cnpj = "27165554000103",
		RazaoSocial = "Municipio de Vila Velha",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "ES",
		MunicipioIbge = "3205200",
		MunicipioNome = "Vila Velha",
		Coverage = s_vilaVelhaOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemAnapolis = new()
	{
		Id = SliceIds.ItemAnapolis,
		ContratacaoId = SliceIds.ContratacaoAnapolis,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Scanner",
		Catmat = "611695",
		Catser = null,
		Quantidade = 8m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1642.61m,
		ValorTotal = 13140.88m,
		Uf = "GO",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "GO",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemVilaVelha = new()
	{
		Id = SliceIds.ItemVilaVelha,
		ContratacaoId = SliceIds.ContratacaoVilaVelha,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Revelador radiologico",
		Catmat = "405620",
		Catser = null,
		Quantidade = 420m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 7.48m,
		ValorTotal = 3141.6m,
		Uf = "ES",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "ES",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_campinaGrandeOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PB",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_campinaGrande = new()
	{
		Id = SliceIds.OrgaoCampinaGrande,
		Cnpj = "08993917000146",
		RazaoSocial = "Municipio de Campina Grande",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PB",
		MunicipioIbge = "2504009",
		MunicipioNome = "Campina Grande",
		Coverage = s_campinaGrandeOrgaoCoverage,
	};

	private static readonly Coverage s_caucaiaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "CE",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_caucaia = new()
	{
		Id = SliceIds.OrgaoCaucaia,
		Cnpj = "07616162000106",
		RazaoSocial = "Municipio de Caucaia",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "CE",
		MunicipioIbge = "2303709",
		MunicipioNome = "Caucaia",
		Coverage = s_caucaiaOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemCampinaGrande = new()
	{
		Id = SliceIds.ItemCampinaGrande,
		ContratacaoId = SliceIds.ContratacaoCampinaGrande,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Memoria Ram",
		Catmat = "618288",
		Catser = null,
		Quantidade = 4m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 209.99m,
		ValorTotal = 839.96m,
		Uf = "PB",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PB",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCaucaia = new()
	{
		Id = SliceIds.ItemCaucaia,
		ContratacaoId = SliceIds.ContratacaoCaucaia,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Bloco receituario medico",
		Catmat = "485443",
		Catser = null,
		Quantidade = 1000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 8.55m,
		ValorTotal = 8550m,
		Uf = "CE",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "CE",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_imperatrizOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MA",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_imperatriz = new()
	{
		Id = SliceIds.OrgaoImperatriz,
		Cnpj = "06158455000116",
		RazaoSocial = "Municipio de Imperatriz",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MA",
		MunicipioIbge = "2105302",
		MunicipioNome = "Imperatriz",
		Coverage = s_imperatrizOrgaoCoverage,
	};

	private static readonly Coverage s_arapiracaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "AL",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_arapiraca = new()
	{
		Id = SliceIds.OrgaoArapiraca,
		Cnpj = "12198693000158",
		RazaoSocial = "Municipio de Arapiraca",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "AL",
		MunicipioIbge = "2700300",
		MunicipioNome = "Arapiraca",
		Coverage = s_arapiracaOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemImperatriz = new()
	{
		Id = SliceIds.ItemImperatriz,
		ContratacaoId = SliceIds.ContratacaoImperatriz,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Livro didatico",
		Catmat = "464257",
		Catser = null,
		Quantidade = 100m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 525.3m,
		ValorTotal = 52530m,
		Uf = "MA",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MA",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemArapiraca = new()
	{
		Id = SliceIds.ItemArapiraca,
		ContratacaoId = SliceIds.ContratacaoArapiraca,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Lamotrigina",
		Catmat = "602451",
		Catser = null,
		Quantidade = 18m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 16m,
		ValorTotal = 288m,
		Uf = "AL",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "AL",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly Coverage s_douradosOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MS",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_dourados = new()
	{
		Id = SliceIds.OrgaoDourados,
		Cnpj = "20267427000168",
		RazaoSocial = "Municipio de Dourados",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MS",
		MunicipioIbge = "5003702",
		MunicipioNome = "Dourados",
		Coverage = s_douradosOrgaoCoverage,
	};

	private static readonly Coverage s_marabaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PA",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_maraba = new()
	{
		Id = SliceIds.OrgaoMaraba,
		Cnpj = "05853163000130",
		RazaoSocial = "Municipio de Maraba",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PA",
		MunicipioIbge = "1504208",
		MunicipioNome = "Maraba",
		Coverage = s_marabaOrgaoCoverage,
	};

	private static readonly Coverage s_varzeaGrandeOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MT",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_varzeaGrande = new()
	{
		Id = SliceIds.OrgaoVarzeaGrande,
		Cnpj = "03507548000110",
		RazaoSocial = "Municipio de Varzea Grande",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MT",
		MunicipioIbge = "5108402",
		MunicipioNome = "Varzea Grande",
		Coverage = s_varzeaGrandeOrgaoCoverage,
	};

	private static readonly Coverage s_jiParanaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RO",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_jiParana = new()
	{
		Id = SliceIds.OrgaoJiParana,
		Cnpj = "04092672000125",
		RazaoSocial = "Municipio de Ji-Parana",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RO",
		MunicipioIbge = "1100122",
		MunicipioNome = "Ji-Parana",
		Coverage = s_jiParanaOrgaoCoverage,
	};

	private static readonly Coverage s_parnamirimOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RN",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_parnamirim = new()
	{
		Id = SliceIds.OrgaoParnamirim,
		Cnpj = "08170862000174",
		RazaoSocial = "Municipio de Parnamirim",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RN",
		MunicipioIbge = "2403251",
		MunicipioNome = "Parnamirim",
		Coverage = s_parnamirimOrgaoCoverage,
	};

	private static readonly Coverage s_cruzeiroDoSulOrgaoCoverage = new()
	{
		N = 1,
		Uf = "AC",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_cruzeiroDoSul = new()
	{
		Id = SliceIds.OrgaoCruzeiroDoSul,
		Cnpj = "04012548000102",
		RazaoSocial = "Municipio de Cruzeiro do Sul",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "AC",
		MunicipioIbge = "1200203",
		MunicipioNome = "Cruzeiro do Sul",
		Coverage = s_cruzeiroDoSulOrgaoCoverage,
	};

	private static readonly Coverage s_santanaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "AP",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_santana = new()
	{
		Id = SliceIds.OrgaoSantana,
		Cnpj = "23066640000108",
		RazaoSocial = "Municipio de Santana",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "AP",
		MunicipioIbge = "1600600",
		MunicipioNome = "Santana",
		Coverage = s_santanaOrgaoCoverage,
	};

	private static readonly Coverage s_rorainopolisOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RR",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_rorainopolis = new()
	{
		Id = SliceIds.OrgaoRorainopolis,
		Cnpj = "01613031000180",
		RazaoSocial = "Municipio de Rorainopolis",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RR",
		MunicipioIbge = "1400472",
		MunicipioNome = "Rorainopolis",
		Coverage = s_rorainopolisOrgaoCoverage,
	};

	private static readonly Coverage s_maringaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_maringa = new()
	{
		Id = SliceIds.OrgaoMaringa,
		Cnpj = "76282656000106",
		RazaoSocial = "Municipio de Maringa",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PR",
		MunicipioIbge = "4115200",
		MunicipioNome = "Maringa",
		Coverage = s_maringaOrgaoCoverage,
	};

	private static readonly Coverage s_taubateOrgaoCoverage = new()
	{
		N = 1,
		Uf = "SP",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_taubate = new()
	{
		Id = SliceIds.OrgaoTaubate,
		Cnpj = "45176005000108",
		RazaoSocial = "Municipio de Taubate",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "SP",
		MunicipioIbge = "3554102",
		MunicipioNome = "Taubate",
		Coverage = s_taubateOrgaoCoverage,
	};

	private static readonly Coverage s_cascavelOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_cascavel = new()
	{
		Id = SliceIds.OrgaoCascavel,
		Cnpj = "76208867000107",
		RazaoSocial = "Municipio de Cascavel",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PR",
		MunicipioIbge = "4104808",
		MunicipioNome = "Cascavel",
		Coverage = s_cascavelOrgaoCoverage,
	};

	private static readonly Coverage s_juizDeForaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_juizDeFora = new()
	{
		Id = SliceIds.OrgaoJuizDeFora,
		Cnpj = "18338178000102",
		RazaoSocial = "Municipio de Juiz de Fora",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3136702",
		MunicipioNome = "Juiz de Fora",
		Coverage = s_juizDeForaOrgaoCoverage,
	};

	private static readonly Coverage s_fozOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_foz = new()
	{
		Id = SliceIds.OrgaoFoz,
		Cnpj = "76206606000140",
		RazaoSocial = "Municipio de Foz do Iguacu",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PR",
		MunicipioIbge = "4108304",
		MunicipioNome = "Foz do Iguacu",
		Coverage = s_fozOrgaoCoverage,
	};

	private static readonly Coverage s_santaMariaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RS",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_santaMaria = new()
	{
		Id = SliceIds.OrgaoSantaMaria,
		Cnpj = "88488366000100",
		RazaoSocial = "Municipio de Santa Maria",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RS",
		MunicipioIbge = "4316907",
		MunicipioNome = "Santa Maria",
		Coverage = s_santaMariaOrgaoCoverage,
	};

	private static readonly Coverage s_montesClarosOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_montesClaros = new()
	{
		Id = SliceIds.OrgaoMontesClaros,
		Cnpj = "22678874000135",
		RazaoSocial = "Municipio de Montes Claros",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3143302",
		MunicipioNome = "Montes Claros",
		Coverage = s_montesClarosOrgaoCoverage,
	};

	private static readonly Coverage s_governadorValadaresOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_governadorValadares = new()
	{
		Id = SliceIds.OrgaoGovernadorValadares,
		Cnpj = "20622890000180",
		RazaoSocial = "Municipio de Governador Valadares",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3127701",
		MunicipioNome = "Governador Valadares",
		Coverage = s_governadorValadaresOrgaoCoverage,
	};

	private static readonly Coverage s_canoasOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RS",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_canoas = new()
	{
		Id = SliceIds.OrgaoCanoas,
		Cnpj = "88577416000118",
		RazaoSocial = "Municipio de Canoas",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RS",
		MunicipioIbge = "4304606",
		MunicipioNome = "Canoas",
		Coverage = s_canoasOrgaoCoverage,
	};

	private static readonly Coverage s_lagesOrgaoCoverage = new()
	{
		N = 1,
		Uf = "SC",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_lages = new()
	{
		Id = SliceIds.OrgaoLages,
		Cnpj = "82777301000190",
		RazaoSocial = "Municipio de Lages",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "SC",
		MunicipioIbge = "4209300",
		MunicipioNome = "Lages",
		Coverage = s_lagesOrgaoCoverage,
	};

	private static readonly Coverage s_santaremOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PA",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_santarem = new()
	{
		Id = SliceIds.OrgaoSantarem,
		Cnpj = "05182233000761",
		RazaoSocial = "Municipio de Santarem",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PA",
		MunicipioIbge = "1506807",
		MunicipioNome = "Santarem",
		Coverage = s_santaremOrgaoCoverage,
	};

	private static readonly Coverage s_rioVerdeOrgaoCoverage = new()
	{
		N = 1,
		Uf = "GO",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_rioVerde = new()
	{
		Id = SliceIds.OrgaoRioVerde,
		Cnpj = "02056729000105",
		RazaoSocial = "Municipio de Rio Verde",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "GO",
		MunicipioIbge = "5218805",
		MunicipioNome = "Rio Verde",
		Coverage = s_rioVerdeOrgaoCoverage,
	};

	private static readonly Coverage s_pauloAfonsoOrgaoCoverage = new()
	{
		N = 1,
		Uf = "BA",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_pauloAfonso = new()
	{
		Id = SliceIds.OrgaoPauloAfonso,
		Cnpj = "14217327000124",
		RazaoSocial = "Municipio de Paulo Afonso",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "BA",
		MunicipioIbge = "2924009",
		MunicipioNome = "Paulo Afonso",
		Coverage = s_pauloAfonsoOrgaoCoverage,
	};

	private static readonly Coverage s_saoLourencoOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PE",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_saoLourenco = new()
	{
		Id = SliceIds.OrgaoSaoLourenco,
		Cnpj = "11251832000105",
		RazaoSocial = "Municipio de Sao Lourenco da Mata",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PE",
		MunicipioIbge = "2613701",
		MunicipioNome = "Sao Lourenco da Mata",
		Coverage = s_saoLourencoOrgaoCoverage,
	};

	private static readonly Coverage s_cratoOrgaoCoverage = new()
	{
		N = 1,
		Uf = "CE",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_crato = new()
	{
		Id = SliceIds.OrgaoCrato,
		Cnpj = "07587975000107",
		RazaoSocial = "Municipio de Crato",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "CE",
		MunicipioIbge = "2304202",
		MunicipioNome = "Crato",
		Coverage = s_cratoOrgaoCoverage,
	};

	private static readonly Coverage s_ariquemesOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RO",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_ariquemes = new()
	{
		Id = SliceIds.OrgaoAriquemes,
		Cnpj = "04104816000116",
		RazaoSocial = "Municipio de Ariquemes",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RO",
		MunicipioIbge = "1100023",
		MunicipioNome = "Ariquemes",
		Coverage = s_ariquemesOrgaoCoverage,
	};

	private static readonly Coverage s_colatinaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "ES",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_colatina = new()
	{
		Id = SliceIds.OrgaoColatina,
		Cnpj = "27165729000174",
		RazaoSocial = "Municipio de Colatina",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "ES",
		MunicipioIbge = "3201506",
		MunicipioNome = "Colatina",
		Coverage = s_colatinaOrgaoCoverage,
	};

	private static readonly Coverage s_castanhalOrgaoCoverage = new()
	{
		N = 1,
		Uf = "PA",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_castanhal = new()
	{
		Id = SliceIds.OrgaoCastanhal,
		Cnpj = "05121991000184",
		RazaoSocial = "Municipio de Castanhal",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "PA",
		MunicipioIbge = "1502400",
		MunicipioNome = "Castanhal",
		Coverage = s_castanhalOrgaoCoverage,
	};

	private static readonly Coverage s_divinopolisOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_divinopolis = new()
	{
		Id = SliceIds.OrgaoDivinopolis,
		Cnpj = "18291351000164",
		RazaoSocial = "Municipio de Divinopolis",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3122306",
		MunicipioNome = "Divinopolis",
		Coverage = s_divinopolisOrgaoCoverage,
	};

	private static readonly Coverage s_petropolisOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RJ",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_petropolis = new()
	{
		Id = SliceIds.OrgaoPetropolis,
		Cnpj = "29138344000143",
		RazaoSocial = "Municipio de Petropolis",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RJ",
		MunicipioIbge = "3303906",
		MunicipioNome = "Petropolis",
		Coverage = s_petropolisOrgaoCoverage,
	};

	private static readonly Coverage s_ipatingaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_ipatinga = new()
	{
		Id = SliceIds.OrgaoIpatinga,
		Cnpj = "19876424000142",
		RazaoSocial = "Municipio de Ipatinga",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3131307",
		MunicipioNome = "Ipatinga",
		Coverage = s_ipatingaOrgaoCoverage,
	};

	private static readonly Coverage s_macaeOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RJ",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_macae = new()
	{
		Id = SliceIds.OrgaoMacae,
		Cnpj = "29115474000160",
		RazaoSocial = "Municipio de Macae",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RJ",
		MunicipioIbge = "3302403",
		MunicipioNome = "Macae",
		Coverage = s_macaeOrgaoCoverage,
	};

	private static readonly Coverage s_santaLuziaOrgaoCoverage = new()
	{
		N = 1,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_santaLuzia = new()
	{
		Id = SliceIds.OrgaoSantaLuzia,
		Cnpj = "18715409000150",
		RazaoSocial = "Municipio de Santa Luzia",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "MG",
		MunicipioIbge = "3157807",
		MunicipioNome = "Santa Luzia",
		Coverage = s_santaLuziaOrgaoCoverage,
	};

	private static readonly Coverage s_novaFriburgoOrgaoCoverage = new()
	{
		N = 1,
		Uf = "RJ",
		Quarter = SliceIds.Quarter,
		MethodologyVersion = SliceIds.Methodology,
	};

	private static readonly OrgaoRecord s_novaFriburgo = new()
	{
		Id = SliceIds.OrgaoNovaFriburgo,
		Cnpj = "28606630000123",
		RazaoSocial = "Municipio de Nova Friburgo",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "RJ",
		MunicipioIbge = "3303401",
		MunicipioNome = "Nova Friburgo",
		Coverage = s_novaFriburgoOrgaoCoverage,
	};

	private static readonly ItemRecord s_itemDourados = new()
	{
		Id = SliceIds.ItemDourados,
		ContratacaoId = SliceIds.ContratacaoDourados,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Reagente para diagnostico clinico",
		Catmat = "333587",
		Catser = null,
		Quantidade = 12m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 126m,
		ValorTotal = 1512m,
		Uf = "MS",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MS",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemMaraba = new()
	{
		Id = SliceIds.ItemMaraba,
		ContratacaoId = SliceIds.ContratacaoMaraba,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Fogao gas",
		Catmat = "425200",
		Catser = null,
		Quantidade = 4m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 849.99m,
		ValorTotal = 3399.96m,
		Uf = "PA",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemVarzeaGrande = new()
	{
		Id = SliceIds.ItemVarzeaGrande,
		ContratacaoId = SliceIds.ContratacaoVarzeaGrande,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Microcomputador",
		Catmat = "606229",
		Catser = null,
		Quantidade = 2m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 26021m,
		ValorTotal = 52042m,
		Uf = "MT",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MT",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemJiParana = new()
	{
		Id = SliceIds.ItemJiParana,
		ContratacaoId = SliceIds.ContratacaoJiParana,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Assinatura de banco de imagens",
		Catmat = "30130",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 38540m,
		ValorTotal = 38540m,
		Uf = "RO",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RO",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemParnamirim = new()
	{
		Id = SliceIds.ItemParnamirim,
		ContratacaoId = SliceIds.ContratacaoParnamirim,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Automovel",
		Catmat = "430273",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 78500m,
		ValorTotal = 78500m,
		Uf = "RN",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RN",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCruzeiroDoSul = new()
	{
		Id = SliceIds.ItemCruzeiroDoSul,
		ContratacaoId = SliceIds.ContratacaoCruzeiroDoSul,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Grade niveladora",
		Catmat = "463162",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 26784.45m,
		ValorTotal = 26784.45m,
		Uf = "AC",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "AC",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemSantana = new()
	{
		Id = SliceIds.ItemSantana,
		ContratacaoId = SliceIds.ContratacaoSantana,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Prestacao de servicos bancarios",
		Catmat = null,
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1m,
		ValorTotal = 1m,
		Uf = "AP",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "AP",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemRorainopolis = new()
	{
		Id = SliceIds.ItemRorainopolis,
		ContratacaoId = SliceIds.ContratacaoRorainopolis,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Ambulancia",
		Catmat = "621643",
		Catser = null,
		Quantidade = 3m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 324000m,
		ValorTotal = 972000m,
		Uf = "RR",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RR",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemMaringa = new()
	{
		Id = SliceIds.ItemMaringa,
		ContratacaoId = SliceIds.ContratacaoMaringa,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Enalapril maleato",
		Catmat = "267652",
		Catser = null,
		Quantidade = 2505672m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 0.045m,
		ValorTotal = 112755.24m,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemTaubate = new()
	{
		Id = SliceIds.ItemTaubate,
		ContratacaoId = SliceIds.ContratacaoTaubate,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Eletrodos para eletroencefalograma",
		Catmat = "7021",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 8250m,
		ValorTotal = 8250m,
		Uf = "SP",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCascavel = new()
	{
		Id = SliceIds.ItemCascavel,
		ContratacaoId = SliceIds.ContratacaoCascavel,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Motocicleta",
		Catmat = "318890",
		Catser = null,
		Quantidade = 3m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 65370m,
		ValorTotal = 196110m,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemJuizDeFora = new()
	{
		Id = SliceIds.ItemJuizDeFora,
		ContratacaoId = SliceIds.ContratacaoJuizDeFora,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Pembrolizumabe",
		Catmat = "440269",
		Catser = null,
		Quantidade = 10m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 16021.4m,
		ValorTotal = 160214m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemFoz = new()
	{
		Id = SliceIds.ItemFoz,
		ContratacaoId = SliceIds.ContratacaoFoz,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Fermento",
		Catmat = "459596",
		Catser = null,
		Quantidade = 2500m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 16.47m,
		ValorTotal = 41175m,
		Uf = "PR",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PR",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemSantaMaria = new()
	{
		Id = SliceIds.ItemSantaMaria,
		ContratacaoId = SliceIds.ContratacaoSantaMaria,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Risperidona",
		Catmat = "272839",
		Catser = null,
		Quantidade = 200000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 0.141m,
		ValorTotal = 28182m,
		Uf = "RS",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RS",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemMontesClaros = new()
	{
		Id = SliceIds.ItemMontesClaros,
		ContratacaoId = SliceIds.ContratacaoMontesClaros,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Manutencao prevencao combate incendio",
		Catmat = "21822",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 330811.34m,
		ValorTotal = 330811.34m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemGovernadorValadares = new()
	{
		Id = SliceIds.ItemGovernadorValadares,
		ContratacaoId = SliceIds.ContratacaoGovernadorValadares,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Cartao controle acesso",
		Catmat = "618284",
		Catser = null,
		Quantidade = 30000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1.45m,
		ValorTotal = 43500m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCanoas = new()
	{
		Id = SliceIds.ItemCanoas,
		ContratacaoId = SliceIds.ContratacaoCanoas,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Clorimetro",
		Catmat = "247827",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1667.07m,
		ValorTotal = 1667.07m,
		Uf = "RS",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RS",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemLages = new()
	{
		Id = SliceIds.ItemLages,
		ContratacaoId = SliceIds.ContratacaoLages,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Sacola",
		Catmat = "229690",
		Catser = null,
		Quantidade = 30m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 97m,
		ValorTotal = 2910m,
		Uf = "SC",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "SC",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemSantarem = new()
	{
		Id = SliceIds.ItemSantarem,
		ContratacaoId = SliceIds.ContratacaoSantarem,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Obras civis publicas",
		Catmat = "5622",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 326424.56m,
		ValorTotal = 326424.56m,
		Uf = "PA",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemRioVerde = new()
	{
		Id = SliceIds.ItemRioVerde,
		ContratacaoId = SliceIds.ContratacaoRioVerde,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Lampada refletora",
		Catmat = "485659",
		Catser = null,
		Quantidade = 10m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 45m,
		ValorTotal = 450m,
		Uf = "GO",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "GO",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemPauloAfonso = new()
	{
		Id = SliceIds.ItemPauloAfonso,
		ContratacaoId = SliceIds.ContratacaoPauloAfonso,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Acucar",
		Catmat = "603269",
		Catser = null,
		Quantidade = 2000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 4.42m,
		ValorTotal = 8840m,
		Uf = "BA",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "BA",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemSaoLourenco = new()
	{
		Id = SliceIds.ItemSaoLourenco,
		ContratacaoId = SliceIds.ContratacaoSaoLourenco,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Ventilador",
		Catmat = "461897",
		Catser = null,
		Quantidade = 375m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 194m,
		ValorTotal = 72750m,
		Uf = "PE",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PE",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCrato = new()
	{
		Id = SliceIds.ItemCrato,
		ContratacaoId = SliceIds.ContratacaoCrato,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Bolo Alimenticio",
		Catmat = "308385",
		Catser = null,
		Quantidade = 200m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 48.06m,
		ValorTotal = 9612m,
		Uf = "CE",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "CE",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemAriquemes = new()
	{
		Id = SliceIds.ItemAriquemes,
		ContratacaoId = SliceIds.ContratacaoAriquemes,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Alcool Etilico",
		Catmat = "269941",
		Catser = null,
		Quantidade = 6909m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 6.88m,
		ValorTotal = 47533.92m,
		Uf = "RO",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RO",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemColatina = new()
	{
		Id = SliceIds.ItemColatina,
		ContratacaoId = SliceIds.ContratacaoColatina,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Assinatura - Publicacao Informatizada",
		Catmat = "21040",
		Catser = null,
		Quantidade = 5m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 3900m,
		ValorTotal = 19500m,
		Uf = "ES",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "ES",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemCastanhal = new()
	{
		Id = SliceIds.ItemCastanhal,
		ContratacaoId = SliceIds.ContratacaoCastanhal,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Agua Mineral Natural",
		Catmat = "613476",
		Catser = null,
		Quantidade = 89000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 0.37m,
		ValorTotal = 32930m,
		Uf = "PA",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "PA",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemDivinopolis = new()
	{
		Id = SliceIds.ItemDivinopolis,
		ContratacaoId = SliceIds.ContratacaoDivinopolis,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Cadeira digitador",
		Catmat = "246097",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1819.55m,
		ValorTotal = 1819.55m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemPetropolis = new()
	{
		Id = SliceIds.ItemPetropolis,
		ContratacaoId = SliceIds.ContratacaoPetropolis,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Bobina Papel Impressora aplicacao: impressora plotter, comprimento: 50, gramatura: 75, largura: 914, tipo papel: sulfite Papel para Plotter (Bobina) 75 GR 610x50",
		Catmat = "275143",
		Catser = null,
		Quantidade = 12m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 133.33m,
		ValorTotal = 1599.96m,
		Uf = "RJ",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemIpatinga = new()
	{
		Id = SliceIds.ItemIpatinga,
		ContratacaoId = SliceIds.ContratacaoIpatinga,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Betoneira",
		Catmat = "487731",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 3890m,
		ValorTotal = 3890m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemMacae = new()
	{
		Id = SliceIds.ItemMacae,
		ContratacaoId = SliceIds.ContratacaoMacae,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Colete Identificacao",
		Catmat = "482286",
		Catser = null,
		Quantidade = 36m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 57.99m,
		ValorTotal = 2087.64m,
		Uf = "RJ",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemSantaLuzia = new()
	{
		Id = SliceIds.ItemSantaLuzia,
		ContratacaoId = SliceIds.ContratacaoSantaLuzia,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Cadeira escritorio",
		Catmat = "613647",
		Catser = null,
		Quantidade = 1m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 1647.01m,
		ValorTotal = 1647.01m,
		Uf = "MG",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "MG",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	private static readonly ItemRecord s_itemNovaFriburgo = new()
	{
		Id = SliceIds.ItemNovaFriburgo,
		ContratacaoId = SliceIds.ContratacaoNovaFriburgo,
		FornecedorId = SliceIds.FornecedorExtra,
		Descricao = "Toalha De Papel",
		Catmat = "436328",
		Catser = null,
		Quantidade = 1000m,
		UnidadeMedida = "UN",
		UnidadeCanonica = "un",
		ValorUnitario = 8m,
		ValorTotal = 8000m,
		Uf = "RJ",
		Quarter = SliceIds.Quarter,
		SnapshotId = SliceIds.Snapshot,
		MethodologyVersion = SliceIds.Methodology,
		Coverage = new()
		{
			N = 1,
			Uf = "RJ",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		},
	};

	[Fact]
	public async Task FullCycle_BrowseMunicipioAndUf()
	{
		var client = fixture.GetClient();

		var niteroiPage = await client.ListOrgaos(municipioIbge: "3303302", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			niteroiPage.Coverage);
		Assert.Equal(new[] { s_niteroi }, niteroiPage.Items);
		await ValidateOrgao(client, s_niteroi);

		var bauruPage = await client.ListOrgaos(uf: "SP", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "SP",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			bauruPage.Coverage);
		Assert.Equal(new[] { s_bauru, s_taubate }, bauruPage.Items);
		await ValidateOrgao(client, s_bauru);

		var caxiasPage = await client.ListOrgaos(municipioIbge: "4305108", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			caxiasPage.Coverage);
		Assert.Equal(new[] { s_caxias }, caxiasPage.Items);
		await ValidateOrgao(client, s_caxias);

		var joinvillePage = await client.ListOrgaos(uf: "SC", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "SC",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			joinvillePage.Coverage);
		Assert.Equal(new[] { s_joinville, s_lages }, joinvillePage.Items);
		await ValidateOrgao(client, s_joinville);

		var uberlandiaPage = await client.ListOrgaos(municipioIbge: "3170206", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			uberlandiaPage.Coverage);
		Assert.Equal(new[] { s_uberlandia }, uberlandiaPage.Items);
		await ValidateOrgao(client, s_uberlandia);

		var londrinaPage = await client.ListOrgaos(uf: "PR", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 4,
				Uf = "PR",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			londrinaPage.Coverage);
		Assert.Equal(new[] { s_cascavel, s_foz, s_londrina, s_maringa }, londrinaPage.Items);
		await ValidateOrgao(client, s_londrina);

		var feiraPage = await client.ListOrgaos(municipioIbge: "2910800", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			feiraPage.Coverage);
		Assert.Equal(new[] { s_feira }, feiraPage.Items);
		await ValidateOrgao(client, s_feira);

		var caruaruPage = await client.ListOrgaos(uf: "PE", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "PE",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			caruaruPage.Coverage);
		Assert.Equal(new[] { s_caruaru, s_saoLourenco }, caruaruPage.Items);
		await ValidateOrgao(client, s_caruaru);

		var anapolisPage = await client.ListOrgaos(municipioIbge: "5201108", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			anapolisPage.Coverage);
		Assert.Equal(new[] { s_anapolis }, anapolisPage.Items);
		await ValidateOrgao(client, s_anapolis);

		var vilaVelhaPage = await client.ListOrgaos(uf: "ES", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "ES",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			vilaVelhaPage.Coverage);
		Assert.Equal(new[] { s_colatina, s_vilaVelha }, vilaVelhaPage.Items);
		await ValidateOrgao(client, s_vilaVelha);

		var campinaGrandePage = await client.ListOrgaos(municipioIbge: "2504009", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			campinaGrandePage.Coverage);
		Assert.Equal(new[] { s_campinaGrande }, campinaGrandePage.Items);
		await ValidateOrgao(client, s_campinaGrande);

		var caucaiaPage = await client.ListOrgaos(uf: "CE", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "CE",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			caucaiaPage.Coverage);
		Assert.Equal(new[] { s_caucaia, s_crato }, caucaiaPage.Items);
		await ValidateOrgao(client, s_caucaia);

		var imperatrizPage = await client.ListOrgaos(municipioIbge: "2105302", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			imperatrizPage.Coverage);
		Assert.Equal(new[] { s_imperatriz }, imperatrizPage.Items);
		await ValidateOrgao(client, s_imperatriz);

		var arapiracaPage = await client.ListOrgaos(uf: "AL", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "AL",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			arapiracaPage.Coverage);
		Assert.Equal(new[] { s_arapiraca }, arapiracaPage.Items);
		await ValidateOrgao(client, s_arapiraca);

		var douradosPage = await client.ListOrgaos(municipioIbge: "5003702", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			douradosPage.Coverage);
		Assert.Equal(new[] { s_dourados }, douradosPage.Items);
		await ValidateOrgao(client, s_dourados);

		var marabaPage = await client.ListOrgaos(uf: "PA", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 3,
				Uf = "PA",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			marabaPage.Coverage);
		Assert.Equal(new[] { s_castanhal, s_maraba, s_santarem }, marabaPage.Items);
		await ValidateOrgao(client, s_maraba);

		var varzeaGrandePage = await client.ListOrgaos(municipioIbge: "5108402", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			varzeaGrandePage.Coverage);
		Assert.Equal(new[] { s_varzeaGrande }, varzeaGrandePage.Items);
		await ValidateOrgao(client, s_varzeaGrande);

		var jiParanaPage = await client.ListOrgaos(uf: "RO", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "RO",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			jiParanaPage.Coverage);
		Assert.Equal(new[] { s_ariquemes, s_jiParana }, jiParanaPage.Items);
		await ValidateOrgao(client, s_jiParana);

		var parnamirimPage = await client.ListOrgaos(municipioIbge: "2403251", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			parnamirimPage.Coverage);
		Assert.Equal(new[] { s_parnamirim }, parnamirimPage.Items);
		await ValidateOrgao(client, s_parnamirim);

		var cruzeiroPage = await client.ListOrgaos(uf: "AC", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "AC",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			cruzeiroPage.Coverage);
		Assert.Equal(new[] { s_cruzeiroDoSul }, cruzeiroPage.Items);
		await ValidateOrgao(client, s_cruzeiroDoSul);

		var santanaPage = await client.ListOrgaos(municipioIbge: "1600600", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			santanaPage.Coverage);
		Assert.Equal(new[] { s_santana }, santanaPage.Items);
		await ValidateOrgao(client, s_santana);

		var rorainopolisPage = await client.ListOrgaos(uf: "RR", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "RR",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			rorainopolisPage.Coverage);
		Assert.Equal(new[] { s_rorainopolis }, rorainopolisPage.Items);
		await ValidateOrgao(client, s_rorainopolis);

		var maringaPage = await client.ListOrgaos(municipioIbge: "4115200", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			maringaPage.Coverage);
		Assert.Equal(new[] { s_maringa }, maringaPage.Items);
		await ValidateOrgao(client, s_maringa);

		var taubatePage = await client.ListOrgaos(municipioIbge: "3554102", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			taubatePage.Coverage);
		Assert.Equal(new[] { s_taubate }, taubatePage.Items);
		await ValidateOrgao(client, s_taubate);

		var cascavelPage = await client.ListOrgaos(municipioIbge: "4104808", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			cascavelPage.Coverage);
		Assert.Equal(new[] { s_cascavel }, cascavelPage.Items);
		await ValidateOrgao(client, s_cascavel);

		var juizDeForaPage = await client.ListOrgaos(municipioIbge: "3136702", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			juizDeForaPage.Coverage);
		Assert.Equal(new[] { s_juizDeFora }, juizDeForaPage.Items);
		await ValidateOrgao(client, s_juizDeFora);

		var fozPage = await client.ListOrgaos(municipioIbge: "4108304", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			fozPage.Coverage);
		Assert.Equal(new[] { s_foz }, fozPage.Items);
		await ValidateOrgao(client, s_foz);

		var santaMariaPage = await client.ListOrgaos(municipioIbge: "4316907", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			santaMariaPage.Coverage);
		Assert.Equal(new[] { s_santaMaria }, santaMariaPage.Items);
		await ValidateOrgao(client, s_santaMaria);

		var montesClarosPage = await client.ListOrgaos(municipioIbge: "3143302", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			montesClarosPage.Coverage);
		Assert.Equal(new[] { s_montesClaros }, montesClarosPage.Items);
		await ValidateOrgao(client, s_montesClaros);

		var governadorValadaresPage = await client.ListOrgaos(municipioIbge: "3127701", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			governadorValadaresPage.Coverage);
		Assert.Equal(new[] { s_governadorValadares }, governadorValadaresPage.Items);
		await ValidateOrgao(client, s_governadorValadares);

		var mixed = await client.ListOrgaos(quarter: SliceIds.Quarter, take: 100);
		Assert.Equal("", mixed.Coverage.Uf);
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3306305", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3303302", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3506003", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4305108", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4209102", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3170206", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4113700", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2910800", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2604106", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "5201108", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3205200", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2504009", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2303709", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2105302", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2700300", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "5003702", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1504208", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "5108402", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1100122", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2403251", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1200203", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1600600", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1400472", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4115200", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3554102", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4104808", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3136702", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4108304", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4316907", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3143302", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3127701", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4304606", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "4209300", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1506807", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "5218805", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2924009", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2613701", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "2304202", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1100023", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3201506", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "1502400", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3122306", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3303906", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3131307", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3302403", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3157807", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3303401", StringComparison.Ordinal));

		var canoasPage = await client.ListOrgaos(municipioIbge: "4304606", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			canoasPage.Coverage);
		Assert.Equal(new[] { s_canoas }, canoasPage.Items);
		await ValidateOrgao(client, s_canoas);

		var lagesPage = await client.ListOrgaos(municipioIbge: "4209300", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			lagesPage.Coverage);
		Assert.Equal(new[] { s_lages }, lagesPage.Items);
		await ValidateOrgao(client, s_lages);

		var santaremPage = await client.ListOrgaos(municipioIbge: "1506807", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			santaremPage.Coverage);
		Assert.Equal(new[] { s_santarem }, santaremPage.Items);
		await ValidateOrgao(client, s_santarem);

		var rioVerdePage = await client.ListOrgaos(municipioIbge: "5218805", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			rioVerdePage.Coverage);
		Assert.Equal(new[] { s_rioVerde }, rioVerdePage.Items);
		await ValidateOrgao(client, s_rioVerde);

		var pauloAfonsoPage = await client.ListOrgaos(municipioIbge: "2924009", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			pauloAfonsoPage.Coverage);
		Assert.Equal(new[] { s_pauloAfonso }, pauloAfonsoPage.Items);
		await ValidateOrgao(client, s_pauloAfonso);

		var saoLourencoPage = await client.ListOrgaos(municipioIbge: "2613701", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			saoLourencoPage.Coverage);
		Assert.Equal(new[] { s_saoLourenco }, saoLourencoPage.Items);
		await ValidateOrgao(client, s_saoLourenco);

		var cratoPage = await client.ListOrgaos(municipioIbge: "2304202", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			cratoPage.Coverage);
		Assert.Equal(new[] { s_crato }, cratoPage.Items);
		await ValidateOrgao(client, s_crato);

		var ariquemesPage = await client.ListOrgaos(municipioIbge: "1100023", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			ariquemesPage.Coverage);
		Assert.Equal(new[] { s_ariquemes }, ariquemesPage.Items);
		await ValidateOrgao(client, s_ariquemes);

		var colatinaPage = await client.ListOrgaos(municipioIbge: "3201506", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			colatinaPage.Coverage);
		Assert.Equal(new[] { s_colatina }, colatinaPage.Items);
		await ValidateOrgao(client, s_colatina);

		var castanhalPage = await client.ListOrgaos(municipioIbge: "1502400", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			castanhalPage.Coverage);
		Assert.Equal(new[] { s_castanhal }, castanhalPage.Items);
		await ValidateOrgao(client, s_castanhal);

		var divinopolisPage = await client.ListOrgaos(municipioIbge: "3122306", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			divinopolisPage.Coverage);
		Assert.Equal(new[] { s_divinopolis }, divinopolisPage.Items);
		await ValidateOrgao(client, s_divinopolis);

		var petropolisPage = await client.ListOrgaos(municipioIbge: "3303906", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			petropolisPage.Coverage);
		Assert.Equal(new[] { s_petropolis }, petropolisPage.Items);
		await ValidateOrgao(client, s_petropolis);

		var ipatingaPage = await client.ListOrgaos(municipioIbge: "3131307", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			ipatingaPage.Coverage);
		Assert.Equal(new[] { s_ipatinga }, ipatingaPage.Items);
		await ValidateOrgao(client, s_ipatinga);

		var macaePage = await client.ListOrgaos(municipioIbge: "3302403", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			macaePage.Coverage);
		Assert.Equal(new[] { s_macae }, macaePage.Items);
		await ValidateOrgao(client, s_macae);

		var santaLuziaPage = await client.ListOrgaos(municipioIbge: "3157807", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			santaLuziaPage.Coverage);
		Assert.Equal(new[] { s_santaLuzia }, santaLuziaPage.Items);
		await ValidateOrgao(client, s_santaLuzia);

		var novaFriburgoPage = await client.ListOrgaos(municipioIbge: "3303401", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			novaFriburgoPage.Coverage);
		Assert.Equal(new[] { s_novaFriburgo }, novaFriburgoPage.Items);
		await ValidateOrgao(client, s_novaFriburgo);

		var spItems = await client.ListItems(uf: "SP", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "SP",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			spItems.Coverage);
		Assert.Equal(new[] { s_itemTaubate, s_itemBauru }, spItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemBauru,
			OrgaoId = SliceIds.OrgaoBauru,
			OrgaoRazaoSocial = "Municipio de Bauru",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "3506003-1-000001/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemNiteroi,
			OrgaoId = SliceIds.OrgaoNiteroi,
			OrgaoRazaoSocial = "Municipio de Niteroi",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "3303302-1-000001/2024",
		});
		var scItems = await client.ListItems(uf: "SC", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "SC",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			scItems.Coverage);
		Assert.Equal(new[] { s_itemJoinville, s_itemLages }, scItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemJoinville,
			OrgaoId = SliceIds.OrgaoJoinville,
			OrgaoRazaoSocial = "Municipio de Joinville",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "83169623000110-1-000301/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCaxias,
			OrgaoId = SliceIds.OrgaoCaxias,
			OrgaoRazaoSocial = "Municipio de Caxias do Sul",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "88830609000139-1-000888/2024",
		});
		var prItems = await client.ListItems(uf: "PR", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 4,
				Uf = "PR",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			prItems.Coverage);
		Assert.Equal(new[] { s_itemLondrina, s_itemMaringa, s_itemFoz, s_itemCascavel }, prItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemLondrina,
			OrgaoId = SliceIds.OrgaoLondrina,
			OrgaoRazaoSocial = "Municipio de Londrina",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "75771477000170-1-000026/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemUberlandia,
			OrgaoId = SliceIds.OrgaoUberlandia,
			OrgaoRazaoSocial = "Municipio de Uberlandia",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "18431312000115-1-000095/2024",
		});
		var peItems = await client.ListItems(uf: "PE", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "PE",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			peItems.Coverage);
		Assert.Equal(new[] { s_itemCaruaru, s_itemSaoLourenco }, peItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemCaruaru,
			OrgaoId = SliceIds.OrgaoCaruaru,
			OrgaoRazaoSocial = "Municipio de Caruaru",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "10091536000113-1-000124/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemFeira,
			OrgaoId = SliceIds.OrgaoFeira,
			OrgaoRazaoSocial = "Municipio de Feira de Santana",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "14043574000151-1-000544/2024",
		});
		var esItems = await client.ListItems(uf: "ES", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "ES",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			esItems.Coverage);
		Assert.Equal(new[] { s_itemColatina, s_itemVilaVelha }, esItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemColatina,
			OrgaoId = SliceIds.OrgaoColatina,
			OrgaoRazaoSocial = "Municipio de Colatina",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "27165729000174-1-000253/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemVilaVelha,
			OrgaoId = SliceIds.OrgaoVilaVelha,
			OrgaoRazaoSocial = "Municipio de Vila Velha",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "27165554000103-1-000429/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemAnapolis,
			OrgaoId = SliceIds.OrgaoAnapolis,
			OrgaoRazaoSocial = "Municipio de Anapolis",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "01067479000146-1-000086/2024",
		});
		var ceItems = await client.ListItems(uf: "CE", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "CE",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			ceItems.Coverage);
		Assert.Equal(new[] { s_itemCaucaia, s_itemCrato }, ceItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemCaucaia,
			OrgaoId = SliceIds.OrgaoCaucaia,
			OrgaoRazaoSocial = "Municipio de Caucaia",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "07616162000106-1-000076/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCrato,
			OrgaoId = SliceIds.OrgaoCrato,
			OrgaoRazaoSocial = "Municipio de Crato",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "07587975000107-1-000020/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCampinaGrande,
			OrgaoId = SliceIds.OrgaoCampinaGrande,
			OrgaoRazaoSocial = "Municipio de Campina Grande",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "08993917000146-1-000180/2024",
		});
		var alItems = await client.ListItems(uf: "AL", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "AL",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			alItems.Coverage);
		Assert.Equal(new[] { s_itemArapiraca }, alItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemArapiraca,
			OrgaoId = SliceIds.OrgaoArapiraca,
			OrgaoRazaoSocial = "Municipio de Arapiraca",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "12198693000158-1-000088/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemImperatriz,
			OrgaoId = SliceIds.OrgaoImperatriz,
			OrgaoRazaoSocial = "Municipio de Imperatriz",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "06158455000116-1-000002/2024",
		});
		var paItems = await client.ListItems(uf: "PA", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 3,
				Uf = "PA",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			paItems.Coverage);
		Assert.Equal(new[] { s_itemCastanhal, s_itemMaraba, s_itemSantarem }, paItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemCastanhal,
			OrgaoId = SliceIds.OrgaoCastanhal,
			OrgaoRazaoSocial = "Municipio de Castanhal",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "05121991000184-1-000017/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemMaraba,
			OrgaoId = SliceIds.OrgaoMaraba,
			OrgaoRazaoSocial = "Municipio de Maraba",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "05853163000130-1-000142/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemDourados,
			OrgaoId = SliceIds.OrgaoDourados,
			OrgaoRazaoSocial = "Municipio de Dourados",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "20267427000168-1-000043/2024",
		});
		var roItems = await client.ListItems(uf: "RO", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 2,
				Uf = "RO",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			roItems.Coverage);
		Assert.Equal(new[] { s_itemAriquemes, s_itemJiParana }, roItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemJiParana,
			OrgaoId = SliceIds.OrgaoJiParana,
			OrgaoRazaoSocial = "Municipio de Ji-Parana",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "04092672000125-1-000139/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemAriquemes,
			OrgaoId = SliceIds.OrgaoAriquemes,
			OrgaoRazaoSocial = "Municipio de Ariquemes",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "04104816000116-1-000206/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemVarzeaGrande,
			OrgaoId = SliceIds.OrgaoVarzeaGrande,
			OrgaoRazaoSocial = "Municipio de Varzea Grande",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "03507548000110-1-000073/2024",
		});
		var acItems = await client.ListItems(uf: "AC", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "AC",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			acItems.Coverage);
		Assert.Equal(new[] { s_itemCruzeiroDoSul }, acItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemCruzeiroDoSul,
			OrgaoId = SliceIds.OrgaoCruzeiroDoSul,
			OrgaoRazaoSocial = "Municipio de Cruzeiro do Sul",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "04012548000102-1-000033/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemParnamirim,
			OrgaoId = SliceIds.OrgaoParnamirim,
			OrgaoRazaoSocial = "Municipio de Parnamirim",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "08170862000174-1-000034/2024",
		});
		var rrItems = await client.ListItems(uf: "RR", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "RR",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			rrItems.Coverage);
		Assert.Equal(new[] { s_itemRorainopolis }, rrItems.Items);
		await ValidateItem(client, new()
		{
			Item = s_itemRorainopolis,
			OrgaoId = SliceIds.OrgaoRorainopolis,
			OrgaoRazaoSocial = "Municipio de Rorainopolis",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "01613031000180-1-000001/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemSantana,
			OrgaoId = SliceIds.OrgaoSantana,
			OrgaoRazaoSocial = "Municipio de Santana",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "23066640000108-1-000002/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemMaringa,
			OrgaoId = SliceIds.OrgaoMaringa,
			OrgaoRazaoSocial = "Municipio de Maringa",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "76282656000106-1-000691/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemTaubate,
			OrgaoId = SliceIds.OrgaoTaubate,
			OrgaoRazaoSocial = "Municipio de Taubate",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "45176005000108-1-000706/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCascavel,
			OrgaoId = SliceIds.OrgaoCascavel,
			OrgaoRazaoSocial = "Municipio de Cascavel",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "76208867000107-1-000325/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemJuizDeFora,
			OrgaoId = SliceIds.OrgaoJuizDeFora,
			OrgaoRazaoSocial = "Municipio de Juiz de Fora",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "18338178000102-1-000200/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemFoz,
			OrgaoId = SliceIds.OrgaoFoz,
			OrgaoRazaoSocial = "Municipio de Foz do Iguacu",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "76206606000140-1-000362/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemSantaMaria,
			OrgaoId = SliceIds.OrgaoSantaMaria,
			OrgaoRazaoSocial = "Municipio de Santa Maria",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "88488366000100-1-000435/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemMontesClaros,
			OrgaoId = SliceIds.OrgaoMontesClaros,
			OrgaoRazaoSocial = "Municipio de Montes Claros",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "22678874000135-1-000430/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemGovernadorValadares,
			OrgaoId = SliceIds.OrgaoGovernadorValadares,
			OrgaoRazaoSocial = "Municipio de Governador Valadares",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "20622890000180-1-000098/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCanoas,
			OrgaoId = SliceIds.OrgaoCanoas,
			OrgaoRazaoSocial = "Municipio de Canoas",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "88577416000118-1-000156/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemLages,
			OrgaoId = SliceIds.OrgaoLages,
			OrgaoRazaoSocial = "Municipio de Lages",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "82777301000190-1-000260/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemSantarem,
			OrgaoId = SliceIds.OrgaoSantarem,
			OrgaoRazaoSocial = "Municipio de Santarem",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "05182233000761-1-000020/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemRioVerde,
			OrgaoId = SliceIds.OrgaoRioVerde,
			OrgaoRazaoSocial = "Municipio de Rio Verde",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "02056729000105-1-001376/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemPauloAfonso,
			OrgaoId = SliceIds.OrgaoPauloAfonso,
			OrgaoRazaoSocial = "Municipio de Paulo Afonso",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "14217327000124-1-000121/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemSaoLourenco,
			OrgaoId = SliceIds.OrgaoSaoLourenco,
			OrgaoRazaoSocial = "Municipio de Sao Lourenco da Mata",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "11251832000105-1-000065/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCrato,
			OrgaoId = SliceIds.OrgaoCrato,
			OrgaoRazaoSocial = "Municipio de Crato",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "07587975000107-1-000020/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemAriquemes,
			OrgaoId = SliceIds.OrgaoAriquemes,
			OrgaoRazaoSocial = "Municipio de Ariquemes",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "04104816000116-1-000206/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemColatina,
			OrgaoId = SliceIds.OrgaoColatina,
			OrgaoRazaoSocial = "Municipio de Colatina",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "27165729000174-1-000253/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemCastanhal,
			OrgaoId = SliceIds.OrgaoCastanhal,
			OrgaoRazaoSocial = "Municipio de Castanhal",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "05121991000184-1-000017/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemDivinopolis,
			OrgaoId = SliceIds.OrgaoDivinopolis,
			OrgaoRazaoSocial = "Municipio de Divinopolis",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "18291351000164-1-000236/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemPetropolis,
			OrgaoId = SliceIds.OrgaoPetropolis,
			OrgaoRazaoSocial = "Municipio de Petropolis",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "29138344000143-1-000165/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemIpatinga,
			OrgaoId = SliceIds.OrgaoIpatinga,
			OrgaoRazaoSocial = "Municipio de Ipatinga",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "19876424000142-1-000142/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemMacae,
			OrgaoId = SliceIds.OrgaoMacae,
			OrgaoRazaoSocial = "Municipio de Macae",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "29115474000160-1-000119/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemSantaLuzia,
			OrgaoId = SliceIds.OrgaoSantaLuzia,
			OrgaoRazaoSocial = "Municipio de Santa Luzia",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "18715409000150-1-000027/2024",
		});
		await ValidateItem(client, new()
		{
			Item = s_itemNovaFriburgo,
			OrgaoId = SliceIds.OrgaoNovaFriburgo,
			OrgaoRazaoSocial = "Municipio de Nova Friburgo",
			FornecedorRazaoSocial = "Comercio de Limpeza Baixada Ltda",
			ContratacaoPncpId = "28606630000123-1-000093/2024",
		});

		var empty = new Coverage
		{
			N = 0,
			Uf = "SP",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		};
		var none = await client.ListOrgaos(
			q: "nenhum-municipio-xyz",
			uf: "SP",
			quarter: SliceIds.Quarter);
		Assert.Empty(none.Items);
		Assert.Equal(empty, none.Coverage);
		Assert.Equal(0, none.Total);
	}

	[Fact]
	public async Task List_EmptyFilter_ZeroCoverageKeepsSlice()
	{
		var client = fixture.GetClient();
		var empty = new Coverage
		{
			N = 0,
			Uf = SliceIds.Uf,
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		};

		var items = await client.ListItems(
			q: "nenhum-item-xyz",
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter);
		Assert.Empty(items.Items);
		Assert.Equal(empty, items.Coverage);
		Assert.Equal(0, items.Total);

		var orgaos = await client.ListOrgaos(
			q: "nenhum-orgao-xyz",
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter);
		Assert.Empty(orgaos.Items);
		Assert.Equal(empty, orgaos.Coverage);
		Assert.Equal(0, orgaos.Total);
	}

	[Fact]
	public async Task Explorer_HasNoFlagField_AfterInternalFlag()
	{
		var client = fixture.GetClient();
		var created = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item1,
			Kind = "qty_mismatch",
			Delta = "Orgao paid R$8.00/unit for CATMAT 123456 on 2024-03-10. Median across 2 comparable purchases in RJ, 2024-Q2: R$5.00. Source: PNCP 3306305-1-000001/2024.",
			SourceUrl = "https://pncp.gov.br/app/editais/3306305/2024/1",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(created.Content);

		await ValidateItem(client, new()
		{
			Item = s_item1,
			OrgaoId = SliceIds.Orgao,
			OrgaoRazaoSocial = "Municipio de Volta Redonda",
			FornecedorRazaoSocial = "Papelaria Central Ltda",
			ContratacaoPncpId = "3306305-1-000001/2024",
		});

		var items = await client.ListItems(
			contratacaoId: SliceIds.Contratacao,
			uf: SliceIds.Uf,
			quarter: SliceIds.Quarter);
		Assert.Equal(new[] { s_item2, s_item1 }, items.Items);
		Assert.Equal(s_itemSlice, items.Coverage);
		Assert.Equal(2, items.Total);

		var http = fixture.CreateHttpClient();
		await AssertExplorerJsonHasNoFlagField(http, $"/api/items/{SliceIds.Item1}");
		await AssertExplorerJsonHasNoFlagField(
			http,
			$"/api/items?contratacaoId={SliceIds.Contratacao}&uf={SliceIds.Uf}&quarter={SliceIds.Quarter}");
		await AssertExplorerJsonHasNoFlagField(http, $"/api/orgaos?q=Volta&quarter={SliceIds.Quarter}");
		await AssertExplorerJsonHasNoFlagField(http, $"/api/fornecedores?q=Papelaria&uf={SliceIds.Uf}&quarter={SliceIds.Quarter}");
		await AssertExplorerJsonHasNoFlagField(http, $"/api/contratacoes?orgaoId={SliceIds.Orgao}&ano=2024");
	}

	[Fact]
	public async Task PersistRawCpf_Rejected()
	{
		await Assert.ThrowsAsync<Api.Features.Shared.BadRequestException>(() => fixture.SeedAsync(db =>
		{
			db.Fornecedores.Add(new()
			{
				Id = Guid.Parse("99999999-9999-9999-9999-999999999999"),
				Cnpj = "00987654000191",
				RazaoSocial = "52998224725",
			});
			return Task.CompletedTask;
		}));
	}

	private static async Task ValidateOrgao(IComprasApi client, OrgaoRecord expected)
	{
		var loaded = await client.GetOrgao(expected.Id, quarter: SliceIds.Quarter);
		Assert.Equal(expected, loaded.Content);
	}

	private static async Task ValidateFornecedor(IComprasApi client, FornecedorRecord expected)
	{
		var loaded = await client.GetFornecedor(expected.Id, uf: SliceIds.Uf, quarter: SliceIds.Quarter);
		Assert.Equal(expected, loaded.Content);
	}

	private static async Task ValidateContratacao(IComprasApi client, ContratacaoDetail expected)
	{
		var loaded = await client.GetContratacao(expected.Contratacao.Id);
		Assert.NotNull(loaded.Content);
		Assert.Equal(expected.Contratacao, loaded.Content.Contratacao);
		Assert.Equal(expected.Items, loaded.Content.Items);
	}

	private static async Task ValidateItem(IComprasApi client, ItemDetail expected)
	{
		var loaded = await client.GetItem(expected.Item.Id);
		Assert.Equal(expected, loaded.Content);
	}

	private static async Task AssertExplorerJsonHasNoFlagField(HttpClient http, string path)
	{
		var json = await http.GetStringAsync(new Uri(http.BaseAddress!, path));
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

		foreach (var child in element.EnumerateArray())
			AssertNoFlagProperty(child);
	}
}
