using System.Linq.Expressions;
using Api.Persistence.Entities;

namespace Api.Features.Orgaos.Models;

public sealed record OrgaoRecord
{
	public required Guid Id { get; init; }

	public required string Cnpj { get; init; }

	public required string RazaoSocial { get; init; }

	public required Esfera Esfera { get; init; }

	public required string Poder { get; init; }

	public required string Uf { get; init; }

	public required string MunicipioIbge { get; init; }

	public required string MunicipioNome { get; init; }

	public required Coverage Coverage { get; init; }

	public static Expression<Func<Orgao, OrgaoRecord>> Project(string? quarter, string methodologyVersion) =>
		orgao => new OrgaoRecord
		{
			Id = orgao.Id,
			Cnpj = orgao.Cnpj,
			RazaoSocial = orgao.RazaoSocial,
			Esfera = orgao.Esfera,
			Poder = orgao.Poder,
			Uf = orgao.Uf,
			MunicipioIbge = orgao.MunicipioIbge,
			MunicipioNome = orgao.MunicipioNome,
			Coverage = new Coverage
			{
				N = orgao.Contratacoes
					.Where(c => !c.Suspended)
					.SelectMany(c => c.Items)
					.Count(i =>
						!i.Suspended
						&& (i.Fornecedor == null || !i.Fornecedor.Suspended)
						&& (quarter == null || i.Quarter == quarter)
						&& i.MethodologyVersion == methodologyVersion),
				Uf = orgao.Uf,
				Quarter = quarter ?? "",
				MethodologyVersion = methodologyVersion,
			},
		};
}
