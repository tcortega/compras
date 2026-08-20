using System.Linq.Expressions;
using Api.Persistence.Entities;

namespace Api.Features.Items.Models;

public sealed record ItemRecord
{
	public required Guid Id { get; init; }

	public required Guid ContratacaoId { get; init; }

	public Guid? FornecedorId { get; init; }

	public required string Descricao { get; init; }

	public string? Catmat { get; init; }

	public string? Catser { get; init; }

	public required decimal Quantidade { get; init; }

	public required string UnidadeMedida { get; init; }

	public string? UnidadeCanonica { get; init; }

	public decimal? ValorUnitario { get; init; }

	public decimal? ValorTotal { get; init; }

	public required string Uf { get; init; }

	public required string Quarter { get; init; }

	public required string SnapshotId { get; init; }

	public required string MethodologyVersion { get; init; }

	public required Coverage Coverage { get; init; }

	public static Expression<Func<Item, ItemRecord>> Project(IQueryable<Item> visible) =>
		item => new ItemRecord
		{
			Id = item.Id,
			ContratacaoId = item.ContratacaoId,
			FornecedorId = item.FornecedorId,
			Descricao = item.Descricao,
			Catmat = item.Catmat,
			Catser = item.Catser,
			Quantidade = item.Quantidade,
			UnidadeMedida = item.UnidadeMedida,
			UnidadeCanonica = item.UnidadeCanonica,
			ValorUnitario = item.ValorUnitario,
			ValorTotal = item.ValorTotal,
			Uf = item.Uf,
			Quarter = item.Quarter,
			SnapshotId = item.SnapshotId,
			MethodologyVersion = item.MethodologyVersion,
			Coverage = new Coverage
			{
				N = visible.Count(other =>
					other.Uf == item.Uf
					&& other.Quarter == item.Quarter
					&& other.MethodologyVersion == item.MethodologyVersion
					&& (item.Catmat == null || other.Catmat == item.Catmat)),
				Uf = item.Uf,
				Quarter = item.Quarter,
				MethodologyVersion = item.MethodologyVersion,
			},
		};
}

public sealed record ItemDetail
{
	public required ItemRecord Item { get; init; }

	public required Guid OrgaoId { get; init; }

	public required string OrgaoRazaoSocial { get; init; }

	public string? FornecedorRazaoSocial { get; init; }

	public required string ContratacaoPncpId { get; init; }
}
