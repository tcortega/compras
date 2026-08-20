using Api.Persistence.Entities;

namespace Api.Features.Shared;

public static class ExplorerVisibility
{
	public static IQueryable<Orgao> Visible(this IQueryable<Orgao> rows) =>
		rows.Where(x => !x.Suspended);

	public static IQueryable<Fornecedor> Visible(this IQueryable<Fornecedor> rows) =>
		rows.Where(x => !x.Suspended);

	public static IQueryable<Contratacao> Visible(this IQueryable<Contratacao> rows) =>
		rows.Where(x => !x.Suspended && !x.Orgao.Suspended);

	public static IQueryable<Item> Visible(this IQueryable<Item> rows) =>
		rows.Where(x =>
			!x.Suspended
			&& !x.Contratacao.Suspended
			&& !x.Contratacao.Orgao.Suspended
			&& (x.Fornecedor == null || !x.Fornecedor.Suspended));
}
