using Api.Features.Contratacoes.Models;
using Api.Features.Items.Models;

namespace Api.Features.Contratacoes.Endpoints;

[Handler]
[MapGet("/api/contratacoes/{id}")]
public static partial class GetContratacao
{
	public sealed record Command
	{
		public required Guid Id { get; init; }
	}

	private static async ValueTask<ContratacaoDetail> HandleAsync(
		Command command,
		ApplicationDbContext db,
		CancellationToken ct)
	{
		var header = await db.Contratacoes.AsNoTracking()
			.Visible()
			.Where(c => c.Id == command.Id)
			.Select(ContratacaoRecord.Project())
			.FirstOrDefaultAsync(ct);
		if (header is null)
			NotFoundException.ThrowNotFoundException("Contratacao");

		var visible = db.Items.AsNoTracking().Visible();
		var items = await visible
			.Where(i => i.ContratacaoId == command.Id)
			.OrderBy(i => i.Descricao)
			.ThenBy(i => i.Id)
			.Select(ItemRecord.Project(visible))
			.ToListAsync(ct);

		return new()
		{
			Contratacao = header,
			Items = items,
		};
	}
}
