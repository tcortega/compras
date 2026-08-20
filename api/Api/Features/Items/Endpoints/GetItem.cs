using Api.Features.Items.Models;

namespace Api.Features.Items.Endpoints;

[Handler]
[MapGet("/api/items/{id}")]
public static partial class GetItem
{
	public sealed record Command
	{
		public required Guid Id { get; init; }
	}

	private static async ValueTask<ItemDetail> HandleAsync(
		Command command,
		ApplicationDbContext db,
		CancellationToken ct)
	{
		var visible = db.Items.AsNoTracking().Visible();
		var row = await visible
			.Where(i => i.Id == command.Id)
			.Select(i => new
			{
				Item = i,
				i.Contratacao.OrgaoId,
				OrgaoRazaoSocial = i.Contratacao.Orgao.RazaoSocial,
				FornecedorRazaoSocial = i.Fornecedor != null ? i.Fornecedor.RazaoSocial : null,
				i.Contratacao.PncpId,
			})
			.FirstOrDefaultAsync(ct);
		if (row is null)
			NotFoundException.ThrowNotFoundException("Item");

		var item = await visible
			.Where(i => i.Id == command.Id)
			.Select(ItemRecord.Project(visible))
			.FirstAsync(ct);

		return new()
		{
			Item = item,
			OrgaoId = row.OrgaoId,
			OrgaoRazaoSocial = row.OrgaoRazaoSocial,
			FornecedorRazaoSocial = row.FornecedorRazaoSocial,
			ContratacaoPncpId = row.PncpId,
		};
	}
}
