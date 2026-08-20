using System.Net;
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
}
