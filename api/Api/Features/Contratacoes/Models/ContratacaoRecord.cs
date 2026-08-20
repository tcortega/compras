using System.Linq.Expressions;
using Api.Features.Items.Models;
using Api.Persistence.Entities;

namespace Api.Features.Contratacoes.Models;

public sealed record ContratacaoRecord
{
	public required Guid Id { get; init; }

	public required string PncpId { get; init; }

	public required Guid OrgaoId { get; init; }

	public required string OrgaoRazaoSocial { get; init; }

	public required string Modalidade { get; init; }

	public required string Objeto { get; init; }

	public required int Ano { get; init; }

	public decimal? ValorHomologado { get; init; }

	public Instant? PublicadoEm { get; init; }

	public required string Source { get; init; }

	public required string SnapshotId { get; init; }

	public required string MethodologyVersion { get; init; }

	public required Coverage Coverage { get; init; }

	public static Expression<Func<Contratacao, ContratacaoRecord>> Project() =>
		contratacao => new ContratacaoRecord
		{
			Id = contratacao.Id,
			PncpId = contratacao.PncpId,
			OrgaoId = contratacao.OrgaoId,
			OrgaoRazaoSocial = contratacao.Orgao.RazaoSocial,
			Modalidade = contratacao.Modalidade,
			Objeto = contratacao.Objeto,
			Ano = contratacao.Ano,
			ValorHomologado = contratacao.ValorHomologado,
			PublicadoEm = contratacao.PublicadoEm,
			Source = contratacao.Source,
			SnapshotId = contratacao.SnapshotId,
			MethodologyVersion = contratacao.MethodologyVersion,
			Coverage = new Coverage
			{
				N = contratacao.Items.Count(i =>
					!i.Suspended
					&& (i.Fornecedor == null || !i.Fornecedor.Suspended)),
				Uf = contratacao.Orgao.Uf,
				Quarter = contratacao.Items
					.OrderByDescending(i => i.Quarter)
					.Select(i => i.Quarter)
					.FirstOrDefault() ?? "",
				MethodologyVersion = contratacao.MethodologyVersion,
			},
		};
}

public sealed record ContratacaoDetail
{
	public required ContratacaoRecord Contratacao { get; init; }

	public required IReadOnlyList<ItemRecord> Items { get; init; }
}
