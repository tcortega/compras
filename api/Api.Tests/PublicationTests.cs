using System.Net;
using Api.Client;
using Api.Tests.Fixtures;

namespace Api.Tests;

public sealed class PublicationTests(ComprasApiFixture fixture) : IClassFixture<ComprasApiFixture>
{
	[Fact]
	public async Task FullCycle_DetectReviewNotifyHoldPublishReplyResolve()
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

		var resolved = await client.ResolveFlag(expected.Id);
		expected = expected with { State = FlagState.Resolved };
		Assert.Equal(expected, resolved.Content);
		await ValidateFlag(client, expected);

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
}
