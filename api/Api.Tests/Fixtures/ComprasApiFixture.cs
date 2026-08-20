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
			Uf = "ES",
			MunicipioIbge = "3205309",
			MunicipioNome = "Vitoria",
		};
		var pageBeta = new Orgao
		{
			Id = SliceIds.PageOrgaoBeta,
			Cnpj = "33333333000191",
			RazaoSocial = "Paginacao Beta",
			Esfera = Api.Persistence.Entities.Esfera.Municipal,
			Poder = "executivo",
			Uf = "ES",
			MunicipioIbge = "3205309",
			MunicipioNome = "Vitoria",
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

		db.Orgaos.AddRange(orgao, hidden, suspendTarget, pageAlfa, pageBeta, niteroi, bauru);
		db.Fornecedores.AddRange(fornecedor, fornecedorExtra);
		db.Contratacoes.AddRange(contratacao, contratacaoNiteroi, contratacaoBauru);
		db.Items.AddRange(item1, item2, itemNiteroi, itemBauru);
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
