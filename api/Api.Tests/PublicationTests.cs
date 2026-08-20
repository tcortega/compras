using System.Net;
using System.Text.Json;
using Api.Client;
using Api.Tests.Fixtures;

namespace Api.Tests;

public sealed class PublicationTests(ComprasApiFixture fixture) : IClassFixture<ComprasApiFixture>
{
	[Fact]
	public async Task FullCycle_DetectReviewNotifyHoldPublishReplyRetract()
	{
		var client = fixture.GetClient();
		var now = fixture.Clock.GetCurrentInstant();

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
		var expected = created.Content with
		{
			State = FlagState.Detected,
			DetectedAt = now,
			NotifiedAt = null,
			PublishAfter = null,
			PublishedAt = null,
			ReplyText = null,
			RepliedAt = null,
			Suspended = false,
			Framing = "indicio requiring verification",
		};
		Assert.Equal(expected, created.Content);
		await ValidateFlag(client, expected);

		var illegalJump = await client.PublishFlag(expected.Id);
		Assert.Equal(HttpStatusCode.Conflict, illegalJump.StatusCode);
		await ValidateFlag(client, expected);

		var sqlJump = await Record.ExceptionAsync(() => fixture.UpdateFlagState(expected.Id, "published"));
		Assert.NotNull(sqlJump);
		await ValidateFlag(client, expected);

		var reviewed = await client.ReviewFlag(expected.Id);
		expected = expected with { State = FlagState.InternalReview };
		Assert.Equal(expected, reviewed.Content);
		await ValidateFlag(client, expected);

		var notified = await client.NotifyFlag(expected.Id);
		expected = expected with
		{
			State = FlagState.Notified,
			NotifiedAt = now,
			PublishAfter = now + Duration.FromDays(7),
		};
		Assert.Equal(expected, notified.Content);
		await ValidateFlag(client, expected);

		var early = await client.PublishFlag(expected.Id);
		Assert.Equal(HttpStatusCode.Conflict, early.StatusCode);
		await ValidateFlag(client, expected);

		fixture.Clock.Advance(Duration.FromDays(7));
		var publishedAt = now + Duration.FromDays(7);
		var published = await client.PublishFlag(expected.Id);
		expected = expected with
		{
			State = FlagState.Published,
			PublishedAt = publishedAt,
		};
		Assert.Equal(expected, published.Content);
		await ValidateFlag(client, expected);

		var replied = await client.ReplyFlag(expected.Id, new()
		{
			ReplyText = "Unidade estava em caixa com 10 resmas.",
		});
		expected = expected with
		{
			ReplyText = "Unidade estava em caixa com 10 resmas.",
			RepliedAt = publishedAt,
		};
		Assert.Equal(expected, replied.Content);
		await ValidateFlag(client, expected);

		var retracted = await client.RetractFlag(expected.Id);
		expected = expected with { State = FlagState.Retracted };
		Assert.Equal(expected, retracted.Content);
		await ValidateFlag(client, expected);

		var resolveFromRetracted = await client.ResolveFlag(expected.Id);
		Assert.Equal(HttpStatusCode.Conflict, resolveFromRetracted.StatusCode);
		await ValidateFlag(client, expected);

		var audit = await fixture.ListFlagAudit(expected.Id);
		Assert.Equal(5, audit.Count);
		Assert.Equal(
			[
				new() { FromState = null, ToState = "detected" },
				new() { FromState = "detected", ToState = "internal_review" },
				new() { FromState = "internal_review", ToState = "notified" },
				new() { FromState = "notified", ToState = "published" },
				new() { FromState = "published", ToState = "retracted" },
			],
			audit);

		var httpAudit = await client.ListFlagAudit(expected.Id);
		Assert.NotNull(httpAudit.Content);
		Assert.Equal(
			audit.Select(row => (row.FromState, row.ToState)).ToArray(),
			httpAudit.Content.Items.Select(row => (row.FromState, row.ToState)).ToArray());
		Assert.All(httpAudit.Content.Items, row => Assert.Equal(expected.Id, row.FlagId));

		var explorer = await client.GetItem(SliceIds.Item1);
		Assert.Equal(
			new ItemDetail
			{
				Item = new()
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
					Coverage = new()
					{
						N = 2,
						Uf = SliceIds.Uf,
						Quarter = SliceIds.Quarter,
						MethodologyVersion = SliceIds.Methodology,
					},
				},
				OrgaoId = SliceIds.Orgao,
				OrgaoRazaoSocial = "Municipio de Volta Redonda",
				FornecedorRazaoSocial = "Papelaria Central Ltda",
				ContratacaoPncpId = "3306305-1-000001/2024",
			},
			explorer.Content);
	}

	[Fact]
	public async Task FullCycle_DetectReviewNotifyHoldPublishResolve()
	{
		var client = fixture.GetClient();
		var now = fixture.Clock.GetCurrentInstant();

		var created = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item2,
			Kind = "qty_mismatch",
			Delta = "Orgao paid R$2.00/unit for CATMAT 123456 on 2024-03-10. Median across 2 comparable purchases in RJ, 2024-Q2: R$5.00. Source: PNCP 3306305-1-000001/2024.",
			SourceUrl = "https://pncp.gov.br/app/editais/3306305/2024/1",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(created.Content);
		var expected = created.Content with
		{
			State = FlagState.Detected,
			DetectedAt = now,
			NotifiedAt = null,
			PublishAfter = null,
			PublishedAt = null,
			ReplyText = null,
			RepliedAt = null,
			Suspended = false,
			Framing = "indicio requiring verification",
		};
		Assert.Equal(expected, created.Content);
		await ValidateFlag(client, expected);

		var reviewed = await client.ReviewFlag(expected.Id);
		expected = expected with { State = FlagState.InternalReview };
		Assert.Equal(expected, reviewed.Content);
		await ValidateFlag(client, expected);

		var notified = await client.NotifyFlag(expected.Id);
		expected = expected with
		{
			State = FlagState.Notified,
			NotifiedAt = now,
			PublishAfter = now + Duration.FromDays(7),
		};
		Assert.Equal(expected, notified.Content);
		await ValidateFlag(client, expected);

		var early = await client.PublishFlag(expected.Id);
		Assert.Equal(HttpStatusCode.Conflict, early.StatusCode);
		await ValidateFlag(client, expected);

		fixture.Clock.Advance(Duration.FromDays(7));
		var publishedAt = now + Duration.FromDays(7);
		var published = await client.PublishFlag(expected.Id);
		expected = expected with
		{
			State = FlagState.Published,
			PublishedAt = publishedAt,
		};
		Assert.Equal(expected, published.Content);
		await ValidateFlag(client, expected);

		var resolved = await client.ResolveFlag(expected.Id);
		expected = expected with { State = FlagState.Resolved };
		Assert.Equal(expected, resolved.Content);
		await ValidateFlag(client, expected);

		var audit = await fixture.ListFlagAudit(expected.Id);
		Assert.Equal(5, audit.Count);
		Assert.Equal(
			[
				new() { FromState = null, ToState = "detected" },
				new() { FromState = "detected", ToState = "internal_review" },
				new() { FromState = "internal_review", ToState = "notified" },
				new() { FromState = "notified", ToState = "published" },
				new() { FromState = "published", ToState = "resolved" },
			],
			audit);

		var httpAudit = await client.ListFlagAudit(expected.Id);
		Assert.NotNull(httpAudit.Content);
		Assert.Equal(
			audit.Select(row => (row.FromState, row.ToState)).ToArray(),
			httpAudit.Content.Items.Select(row => (row.FromState, row.ToState)).ToArray());
		Assert.All(httpAudit.Content.Items, row => Assert.Equal(expected.Id, row.FlagId));

		var http = fixture.CreateHttpClient();
		await AssertExplorerJsonHasNoFlagField(http, $"/api/items/{SliceIds.Item2}");
	}

	[Fact]
	public async Task FullCycle_NotifyArtifactHoldAndRejectFromPublished()
	{
		var client = fixture.GetClient();
		var now = fixture.Clock.GetCurrentInstant();
		const string Artifact = "protocolo-lai-2024-0615.pdf";

		var created = await client.CreateFlag(new()
		{
			ItemId = SliceIds.ItemNiteroi,
			Kind = "qty_mismatch",
			Delta = "Orgao paid R$15.00/unit for CATMAT 654321 on 2024-03-20. Median across 2 comparable purchases in RJ, 2024-Q2: R$5.00. Source: landing snapshot.",
			SourceUrl = "https://example.test/editais/3303302/2024/1",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(created.Content);
		var expected = created.Content with
		{
			State = FlagState.Detected,
			DetectedAt = now,
			NotifiedAt = null,
			NotifyArtifact = null,
			PublishAfter = null,
			PublishedAt = null,
			ReplyText = null,
			RepliedAt = null,
			Suspended = false,
			Framing = "indicio requiring verification",
		};
		Assert.Equal(expected, created.Content);
		await ValidateFlag(client, expected);

		var reviewed = await client.ReviewFlag(expected.Id);
		expected = expected with { State = FlagState.InternalReview };
		Assert.Equal(expected, reviewed.Content);
		await ValidateFlag(client, expected);

		var notified = await client.NotifyFlag(expected.Id, new() { Artifact = Artifact });
		expected = expected with
		{
			State = FlagState.Notified,
			NotifiedAt = now,
			NotifyArtifact = Artifact,
			PublishAfter = now + Duration.FromDays(7),
		};
		Assert.Equal(expected, notified.Content);
		await ValidateFlag(client, expected);

		var early = await client.PublishFlag(expected.Id);
		Assert.Equal(HttpStatusCode.Conflict, early.StatusCode);
		await ValidateFlag(client, expected);

		fixture.Clock.Advance(Duration.FromDays(7));
		var publishedAt = now + Duration.FromDays(7);
		var published = await client.PublishFlag(expected.Id);
		expected = expected with
		{
			State = FlagState.Published,
			PublishedAt = publishedAt,
		};
		Assert.Equal(expected, published.Content);
		await ValidateFlag(client, expected);

		var illegal = await client.NotifyFlag(expected.Id, new() { Artifact = "late-ref.txt" });
		Assert.Equal(HttpStatusCode.Conflict, illegal.StatusCode);
		await ValidateFlag(client, expected);

		var http = fixture.CreateHttpClient();
		await AssertExplorerJsonHasNoFlagField(http, $"/api/items/{SliceIds.ItemNiteroi}");
	}

	[Fact]
	public async Task FullCycle_ListAfterFlagsExist()
	{
		var client = fixture.GetClient();
		var now = fixture.Clock.GetCurrentInstant();
		var qtyDelta = "qty * unit_price != total_value. qty=10 unit_price=5.00 product=50.00 total=40.00";
		var sanctionDelta = "CNPJ present on CEIS/CNEP. Source: PNCP 3306305-1-000001/2024.";
		var sourceUrl = "https://pncp.gov.br/app/editais/3306305/2024/1";

		var qtyItem1 = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item1,
			Kind = "qty_unit_price_neq_total",
			Delta = qtyDelta,
			SourceUrl = sourceUrl,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(qtyItem1.Content);
		var expectedQty1 = qtyItem1.Content with
		{
			State = FlagState.Detected,
			DetectedAt = now,
			NotifiedAt = null,
			PublishAfter = null,
			PublishedAt = null,
			ReplyText = null,
			RepliedAt = null,
			Suspended = false,
			Framing = "indicio requiring verification",
		};
		Assert.Equal(expectedQty1, qtyItem1.Content);
		await ValidateFlag(client, expectedQty1);

		var qtyItem2 = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item2,
			Kind = "qty_unit_price_neq_total",
			Delta = qtyDelta,
			SourceUrl = sourceUrl,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(qtyItem2.Content);
		var expectedQty2 = qtyItem2.Content with
		{
			State = FlagState.Detected,
			DetectedAt = now,
			NotifiedAt = null,
			PublishAfter = null,
			PublishedAt = null,
			ReplyText = null,
			RepliedAt = null,
			Suspended = false,
			Framing = "indicio requiring verification",
		};
		Assert.Equal(expectedQty2, qtyItem2.Content);
		await ValidateFlag(client, expectedQty2);

		var sanction = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item1,
			Kind = "sanctioned_ceis_cnep",
			Delta = sanctionDelta,
			SourceUrl = sourceUrl,
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(sanction.Content);
		var expectedSanction = sanction.Content with
		{
			State = FlagState.Detected,
			DetectedAt = now,
			NotifiedAt = null,
			PublishAfter = null,
			PublishedAt = null,
			ReplyText = null,
			RepliedAt = null,
			Suspended = false,
			Framing = "indicio requiring verification",
		};
		Assert.Equal(expectedSanction, sanction.Content);
		await ValidateFlag(client, expectedSanction);

		var qtyCoverage = new Coverage
		{
			N = 2,
			Uf = "",
			Quarter = "",
			MethodologyVersion = SliceIds.Methodology,
		};
		var listed = await client.ListFlags(kind: "qty_unit_price_neq_total", state: FlagState.Detected);
		Assert.Equal(qtyCoverage, listed.Coverage);
		Assert.Equal(2, listed.Total);
		Assert.Equal(new[] { expectedQty1, expectedQty2 }, listed.Items);

		var listedSanction = await client.ListFlags(kind: "sanctioned_ceis_cnep", state: FlagState.Detected);
		Assert.Equal(qtyCoverage with { N = 1 }, listedSanction.Coverage);
		Assert.Equal(1, listedSanction.Total);
		Assert.Equal(new[] { expectedSanction }, listedSanction.Items);

		var firstPage = await client.ListFlags(kind: "qty_unit_price_neq_total", take: 1);
		Assert.Equal(qtyCoverage, firstPage.Coverage);
		Assert.Equal(2, firstPage.Total);
		Assert.Equal(new[] { expectedQty1 }, firstPage.Items);

		var secondPage = await client.ListFlags(kind: "qty_unit_price_neq_total", skip: 1, take: 1);
		Assert.Equal(qtyCoverage, secondPage.Coverage);
		Assert.Equal(2, secondPage.Total);
		Assert.Equal(new[] { expectedQty2 }, secondPage.Items);

		var byItem = await client.ListFlags(
			kind: "qty_unit_price_neq_total",
			state: FlagState.Detected,
			itemId: SliceIds.Item1);
		Assert.Equal(qtyCoverage with { N = 1 }, byItem.Coverage);
		Assert.Equal(1, byItem.Total);
		Assert.Equal(new[] { expectedQty1 }, byItem.Items);

		var reviewed = await client.ReviewFlag(expectedQty1.Id);
		expectedQty1 = expectedQty1 with { State = FlagState.InternalReview };
		Assert.Equal(expectedQty1, reviewed.Content);
		await ValidateFlag(client, expectedQty1);

		var stillDetected = await client.ListFlags(kind: "qty_unit_price_neq_total", state: FlagState.Detected);
		Assert.Equal(qtyCoverage with { N = 1 }, stillDetected.Coverage);
		Assert.Equal(1, stillDetected.Total);
		Assert.Equal(new[] { expectedQty2 }, stillDetected.Items);

		var inReview = await client.ListFlags(kind: "qty_unit_price_neq_total", state: FlagState.InternalReview);
		Assert.Equal(qtyCoverage with { N = 1 }, inReview.Coverage);
		Assert.Equal(1, inReview.Total);
		Assert.Equal(new[] { expectedQty1 }, inReview.Items);

		var explorer = await client.GetItem(SliceIds.Item1);
		Assert.Equal(
			new ItemDetail
			{
				Item = new()
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
					Coverage = new()
					{
						N = 2,
						Uf = SliceIds.Uf,
						Quarter = SliceIds.Quarter,
						MethodologyVersion = SliceIds.Methodology,
					},
				},
				OrgaoId = SliceIds.Orgao,
				OrgaoRazaoSocial = "Municipio de Volta Redonda",
				FornecedorRazaoSocial = "Papelaria Central Ltda",
				ContratacaoPncpId = "3306305-1-000001/2024",
			},
			explorer.Content);

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
	public async Task Publish_FromDetected_Conflict()
	{
		var client = fixture.GetClient();
		var created = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item2,
			Kind = "cnae_mismatch",
			Delta = "CNAE unrelated to item sold. Source: PNCP 3306305-1-000001/2024.",
			SourceUrl = "https://pncp.gov.br/app/editais/3306305/2024/1",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(created.Content);

		var published = await client.PublishFlag(created.Content.Id);
		Assert.Equal(HttpStatusCode.Conflict, published.StatusCode);

		var loaded = await client.GetFlag(created.Content.Id);
		Assert.Equal(FlagState.Detected, loaded.Content!.State);
	}

	[Fact]
	public async Task Retract_FromPublished()
	{
		var client = fixture.GetClient();
		var created = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item2,
			Kind = "retroactive_edit",
			Delta = "Record hash changed after publication. Source: landing snapshot.",
			SourceUrl = "https://pncp.gov.br/app/editais/3306305/2024/1",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(created.Content);
		_ = await client.ReviewFlag(created.Content.Id);
		_ = await client.NotifyFlag(created.Content.Id);
		fixture.Clock.Advance(Duration.FromDays(7));
		var published = await client.PublishFlag(created.Content.Id);
		Assert.NotNull(published.Content);

		var retracted = await client.RetractFlag(created.Content.Id);
		Assert.Equal(
			published.Content with { State = FlagState.Retracted },
			retracted.Content);
	}

	[Fact]
	public async Task Publish_SuspendedFlag_Conflict()
	{
		var client = fixture.GetClient();
		var created = await client.CreateFlag(new()
		{
			ItemId = SliceIds.Item1,
			Kind = "fracionamento",
			Delta = "Repeated purchases under dispensa threshold. Source: PNCP.",
			SourceUrl = "https://pncp.gov.br/app/editais/3306305/2024/1",
			SnapshotId = SliceIds.Snapshot,
			MethodologyVersion = SliceIds.Methodology,
		});
		Assert.NotNull(created.Content);
		_ = await client.ReviewFlag(created.Content.Id);
		_ = await client.NotifyFlag(created.Content.Id);
		_ = await client.Suspend(new() { Kind = SuspendKind.Flag, Id = created.Content.Id });
		fixture.Clock.Advance(Duration.FromDays(7));

		var published = await client.PublishFlag(created.Content.Id);
		Assert.Equal(HttpStatusCode.Conflict, published.StatusCode);
	}

	private static async Task ValidateFlag(IComprasApi client, FlagRecord expected)
	{
		var loaded = await client.GetFlag(expected.Id);
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
