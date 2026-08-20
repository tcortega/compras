using System.Net.Http.Json;
using System.Text.Json;
using Api.Tests.Fixtures;

namespace Api.Tests;

public sealed class SearchTests(ComprasApiFixture fixture) : IClassFixture<ComprasApiFixture>
{
	[Fact]
	public async Task FullCycle_Unset_EmptyHonestKeepsSlice()
	{
		var client = fixture.GetClient();
		var empty = await client.Search();
		Assert.Equal("unset", empty.Source);
		Assert.Empty(empty.Orgaos.Items);
		Assert.Empty(empty.Fornecedores.Items);
		Assert.Empty(empty.Items.Items);
		Assert.True(empty.Coverage.N >= 1);
		Assert.Equal("", empty.Coverage.Uf);
		Assert.Equal(SliceIds.Methodology, empty.Coverage.MethodologyVersion);
		AssertNoBannedKeys(empty);

		var missed = await client.Search(q: "Resma");
		Assert.Equal("unset", missed.Source);
		Assert.Empty(missed.Orgaos.Items);
		Assert.Empty(missed.Fornecedores.Items);
		Assert.Empty(missed.Items.Items);
		Assert.Equal(empty.Coverage, missed.Coverage);
		AssertNoBannedKeys(missed);
	}

	internal static void AssertNoBannedKeys(object payload)
	{
		using var doc = JsonDocument.Parse(JsonSerializer.Serialize(payload));
		Walk(doc.RootElement);

		static void Walk(JsonElement element)
		{
			if (element.ValueKind is JsonValueKind.Object)
			{
				foreach (var property in element.EnumerateObject())
				{
					var name = property.Name;
					if (name.Contains("flag", StringComparison.OrdinalIgnoreCase)
						|| name.Contains("adjacenc", StringComparison.OrdinalIgnoreCase)
						|| name.Contains("shared_qsa", StringComparison.OrdinalIgnoreCase)
						|| name.Contains("cpf", StringComparison.OrdinalIgnoreCase))
						Assert.Fail($"search JSON leaked {name}");
					Walk(property.Value);
				}

				return;
			}

			if (element.ValueKind is not JsonValueKind.Array)
				return;
			foreach (var item in element.EnumerateArray())
				Walk(item);
		}
	}
}

public sealed class MeiliSearchTests(MeiliApiFixture fixture) : IClassFixture<MeiliApiFixture>
{
	[Fact]
	public async Task FullCycle_Meili_HydratesWarehouseHits()
	{
		if (!await MeiliApiFixture.EnsureIndexed())
		{
			if (string.Equals(Environment.GetEnvironmentVariable("CI"), "true", StringComparison.OrdinalIgnoreCase))
				Assert.Fail("CI Meili missing for FullCycle search.");
			return;
		}

		var client = fixture.GetClient();
		var empty = await client.Search();
		Assert.Equal("meilisearch", empty.Source);
		Assert.Empty(empty.Items.Items);
		Assert.True(empty.Coverage.N >= 1);
		Assert.Equal("", empty.Coverage.Uf);
		SearchTests.AssertNoBannedKeys(empty);

		var items = await client.Search(q: "Resma", take: 5);
		Assert.Equal("meilisearch", items.Source);
		Assert.Contains(items.Items.Items, row => row.Id == SliceIds.Item1);
		Assert.Equal("Resma papel A4", items.Items.Items.First(row => row.Id == SliceIds.Item1).Descricao);
		Assert.Equal("", items.Coverage.Uf);
		SearchTests.AssertNoBannedKeys(items);

		var orgaos = await client.Search(q: "Volta Redonda", take: 5);
		Assert.Contains(orgaos.Orgaos.Items, row => row.Id == SliceIds.Orgao);
		Assert.Equal("", orgaos.Coverage.Uf);
		SearchTests.AssertNoBannedKeys(orgaos);

		var fornecedores = await client.Search(q: "Papelaria Central", take: 5);
		Assert.Contains(fornecedores.Fornecedores.Items, row => row.Id == SliceIds.Fornecedor);
		SearchTests.AssertNoBannedKeys(fornecedores);
	}
}

public sealed class MeiliApiFixture : ComprasApiFixture
{
	private static readonly Uri s_meili = new(
		Environment.GetEnvironmentVariable("MEILI_URL") is { Length: > 0 } url
			? url.TrimEnd('/') + "/"
			: "http://127.0.0.1:7700/");

	private static readonly string s_key =
		Environment.GetEnvironmentVariable("MEILI_MASTER_KEY") is { Length: > 0 } key
			? key
			: "test-meili-master-key-32chars-ok";

	private static readonly string[] s_searchable = ["text"];

	private static readonly string[] s_filterable = ["kind"];

	private static readonly string[] s_displayed = ["id", "kind", "entityId", "text"];

	public MeiliApiFixture() : base(s_meili.AbsoluteUri.TrimEnd('/'), s_key)
	{
	}

	public static async Task<bool> EnsureIndexed()
	{
		using var http = new HttpClient { BaseAddress = s_meili, Timeout = TimeSpan.FromSeconds(5) };
		if (s_key.Length > 0)
			http.DefaultRequestHeaders.TryAddWithoutValidation("Authorization", $"Bearer {s_key}");
		try
		{
			var health = await http.GetAsync(new Uri("health", UriKind.Relative));
			if (!health.IsSuccessStatusCode)
				return false;
		}
		catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
		{
			return false;
		}

		var index = await Post(http, "indexes", new { uid = "compras", primaryKey = "id" });
		await Wait(http, index);
		var settings = await Patch(http, "indexes/compras/settings", new
		{
			searchableAttributes = s_searchable,
			filterableAttributes = s_filterable,
			displayedAttributes = s_displayed,
		});
		await Wait(http, settings);
		var docs = await Put(http, "indexes/compras/documents?primaryKey=id", new object[]
		{
			new { id = $"item_{SliceIds.Item1}", kind = "item", entityId = SliceIds.Item1.ToString(), text = "Resma papel A4" },
			new { id = $"orgao_{SliceIds.Orgao}", kind = "orgao", entityId = SliceIds.Orgao.ToString(), text = "Municipio de Volta Redonda" },
			new { id = $"fornecedor_{SliceIds.Fornecedor}", kind = "fornecedor", entityId = SliceIds.Fornecedor.ToString(), text = "Papelaria Central Ltda" },
		});
		await Wait(http, docs);
		return true;
	}

	private static Task<HttpResponseMessage> Post(HttpClient http, string path, object body) =>
		http.PostAsJsonAsync(path, body);

	private static Task<HttpResponseMessage> Put(HttpClient http, string path, object body) =>
		http.PutAsJsonAsync(path, body);

	private static Task<HttpResponseMessage> Patch(HttpClient http, string path, object body) =>
		http.PatchAsJsonAsync(path, body);

	private static async Task Wait(HttpClient http, HttpResponseMessage response)
	{
		using (response)
		{
			if (response.StatusCode is System.Net.HttpStatusCode.Conflict)
				return;
			if (!response.IsSuccessStatusCode)
				throw new InvalidOperationException($"meili {response.StatusCode}: {await response.Content.ReadAsStringAsync()}");
			var payload = await response.Content.ReadFromJsonAsync<JsonElement>();
			if (!payload.TryGetProperty("taskUid", out var uid) && !payload.TryGetProperty("uid", out uid))
				return;
			var id = uid.GetInt64();
			for (var i = 0; i < 50; i++)
			{
				var task = await http.GetFromJsonAsync<JsonElement>($"tasks/{id}");
				var status = task.TryGetProperty("status", out var s) ? s.GetString() : "";
				if (string.Equals(status, "succeeded", StringComparison.Ordinal))
					return;
				if (status is "failed" or "canceled")
				{
					var error = task.TryGetProperty("error", out var err) ? err.ToString() : "";
					throw new InvalidOperationException($"meili task {id} {status}: {error}");
				}
				await Task.Delay(200);
			}

			throw new InvalidOperationException($"meili task {id} timed out");
		}
	}
}
