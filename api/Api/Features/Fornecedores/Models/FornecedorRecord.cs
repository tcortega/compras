using System.Linq.Expressions;
using Api.Persistence.Entities;

namespace Api.Features.Fornecedores.Models;

public sealed record FornecedorRecord
{
	public required Guid Id { get; init; }

	public required string Cnpj { get; init; }

	public required string RazaoSocial { get; init; }

	public LocalDate? OpenedOn { get; init; }

	public string? Cnae { get; init; }

	public required Coverage Coverage { get; init; }

	public static Expression<Func<Fornecedor, FornecedorRecord>> Project(string? uf, string? quarter, string methodologyVersion) =>
		fornecedor => new FornecedorRecord
		{
			Id = fornecedor.Id,
			Cnpj = fornecedor.Cnpj,
			RazaoSocial = fornecedor.RazaoSocial,
			OpenedOn = fornecedor.OpenedOn,
			Cnae = fornecedor.Cnae,
			Coverage = new Coverage
			{
				N = fornecedor.Items
					.Count(i =>
						!i.Suspended
						&& !i.Contratacao.Suspended
						&& !i.Contratacao.Orgao.Suspended
						&& (uf == null || i.Uf == uf)
						&& (quarter == null || i.Quarter == quarter)
						&& i.MethodologyVersion == methodologyVersion),
				Uf = uf ?? "",
				Quarter = quarter ?? "",
				MethodologyVersion = methodologyVersion,
			},
		};
}
