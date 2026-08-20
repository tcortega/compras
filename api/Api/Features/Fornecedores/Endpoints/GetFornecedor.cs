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

	public sealed record SocioRecord
	{
		public required string Nome { get; init; }

		public string? CpfMasked { get; init; }

		public string? Qualificacao { get; init; }
	}

	public sealed record Response
	{
		public required Guid Id { get; init; }

		public required string Cnpj { get; init; }

		public required string RazaoSocial { get; init; }

		public LocalDate? OpenedOn { get; init; }

		public string? Cnae { get; init; }

		public string? CnaeDescricao { get; init; }

		public string? IdadeCadastral { get; init; }

		public LocalDate? IdadeAsOf { get; init; }

		public required IReadOnlyList<SocioRecord> Qsa { get; init; }

		public required Coverage Coverage { get; init; }
	}

	private static async ValueTask<Response> HandleAsync(
		Command command,
		ApplicationDbContext db,
		IOptions<AppOptions> options,
		IClock clock,
		CancellationToken ct)
	{
		var methodology = Slice.Methodology(command.MethodologyVersion, options);
		var row = await db.Fornecedores.AsNoTracking()
			.Visible()
			.Where(f => f.Id == command.Id)
			.Select(FornecedorRecord.Project(command.Uf, command.Quarter, methodology))
			.FirstOrDefaultAsync(ct);
		if (row is not null)
		{
			var qsa = await db.FornecedorSocios.AsNoTracking()
				.Where(s => s.FornecedorId == command.Id)
				.OrderBy(s => s.Nome)
				.Select(s => new SocioRecord
				{
					Nome = s.Nome,
					CpfMasked = s.CpfMasked,
					Qualificacao = s.Qualificacao,
				})
				.ToListAsync(ct);
			var cnaeDescricao = await CnaeDescricaoAsync(db, row.Cnae, ct);
			var asOf = clock.GetCurrentInstant()
				.InZone(DateTimeZoneProviders.Tzdb["America/Sao_Paulo"])
				.Date;
			return new Response
			{
				Id = row.Id,
				Cnpj = row.Cnpj,
				RazaoSocial = row.RazaoSocial,
				OpenedOn = row.OpenedOn,
				Cnae = row.Cnae,
				CnaeDescricao = cnaeDescricao,
				IdadeCadastral = FormatIdade(row.OpenedOn, asOf),
				IdadeAsOf = asOf,
				Qsa = qsa,
				Coverage = row.Coverage,
			};
		}

		NotFoundException.ThrowNotFoundException("Fornecedor");
		return default!;
	}

	private static async Task<string?> CnaeDescricaoAsync(
		ApplicationDbContext db,
		string? cnae,
		CancellationToken ct)
	{
		if (cnae is not { Length: > 0 })
			return null;

		var digits = new string(cnae.Where(char.IsDigit).ToArray());
		if (digits.Length == 0)
			return null;

		return await db.Cnaes.AsNoTracking()
			.Where(row => row.Codigo == digits)
			.Select(row => row.Descricao)
			.FirstOrDefaultAsync(ct);
	}

	private static string FormatIdade(LocalDate? openedOn, LocalDate asOf)
	{
		if (openedOn is not { } opened)
			return "n/d";
		if (opened > asOf)
			return "n/d";

		var period = Period.Between(opened, asOf, PeriodUnits.Years | PeriodUnits.Months);
		if (period.Years == 0 && period.Months == 0)
			return "menos de 1 mês";
		if (period.Years == 0)
			return period.Months == 1 ? "1 mês" : $"{period.Months} meses";
		if (period.Months == 0)
			return period.Years == 1 ? "1 ano" : $"{period.Years} anos";

		var years = period.Years == 1 ? "1 ano" : $"{period.Years} anos";
		var months = period.Months == 1 ? "1 mês" : $"{period.Months} meses";
		return $"{years} e {months}";
	}
}
