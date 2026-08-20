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
		Uf = "ES",
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
		Uf = "ES",
		MunicipioIbge = "3205309",
		MunicipioNome = "Vitoria",
		Coverage = s_pageOrgaoRecord,
	};

	private static readonly OrgaoRecord s_pageOrgaoBeta = new()
	{
		Id = SliceIds.PageOrgaoBeta,
		Cnpj = "33333333000191",
		RazaoSocial = "Paginacao Beta",
		Esfera = Esfera.Municipal,
		Poder = "executivo",
		Uf = "ES",
		MunicipioIbge = "3205309",
		MunicipioNome = "Vitoria",
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
			Uf = "ES",
			Quarter = SliceIds.Quarter,
			MethodologyVersion = SliceIds.Methodology,
		};
		var firstOrgaos = await client.ListOrgaos(
			uf: "ES",
			quarter: SliceIds.Quarter,
			take: 1);
		Assert.Equal(new[] { s_pageOrgaoAlfa }, firstOrgaos.Items);
		Assert.Equal(orgaoCoverage, firstOrgaos.Coverage);
		Assert.Equal(2, firstOrgaos.Total);

		var secondOrgaos = await client.ListOrgaos(
			uf: "ES",
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
				N = 1,
				Uf = "SP",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			bauruPage.Coverage);
		Assert.Equal(new[] { s_bauru }, bauruPage.Items);
		await ValidateOrgao(client, s_bauru);

		var mixed = await client.ListOrgaos(quarter: SliceIds.Quarter);
		Assert.Equal("", mixed.Coverage.Uf);
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3306305", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3303302", StringComparison.Ordinal));
		Assert.Contains(mixed.Items, o => string.Equals(o.MunicipioIbge, "3506003", StringComparison.Ordinal));

		var spItems = await client.ListItems(uf: "SP", quarter: SliceIds.Quarter);
		Assert.Equal(
			new Coverage
			{
				N = 1,
				Uf = "SP",
				Quarter = SliceIds.Quarter,
				MethodologyVersion = SliceIds.Methodology,
			},
			spItems.Coverage);
		Assert.Equal(new[] { s_itemBauru }, spItems.Items);
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
