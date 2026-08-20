using Api.Features.Fornecedores.Models;
using Api.Infrastructure.Startup;
using Microsoft.AspNetCore.Mvc;

namespace Api.Features.Fornecedores.Endpoints;

[Handler]
[MapGet("/api/fornecedores/{id}")]
public static partial class GetFornecedor
{
	public sealed record Command
	{
		public required Guid Id { get; init; }

		[FromQuery]
		public string? Uf { get; init; }

		[FromQuery]
		public string? Quarter { get; init; }

		[FromQuery]
		public string? MethodologyVersion { get; init; }
	}

	private static async ValueTask<FornecedorRecord> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var row = await db.Fornecedores.AsNoTracking()
			.Visible()
			.Where(f => f.Id == command.Id)
			.Select(FornecedorRecord.Project(command.Uf, command.Quarter, methodology))
			.FirstOrDefaultAsync(ct);
		if (row is not null)
			return row;
		NotFoundException.ThrowNotFoundException("Fornecedor");
		return default!;
	}
}
