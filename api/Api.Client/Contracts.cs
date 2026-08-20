using NodaTime;

namespace Api.Client;

public enum Esfera
{
	Federal,
	Estadual,
	Municipal,
}

public enum FlagState
{
	Detected,
	InternalReview,
	Notified,
	Published,
	Resolved,
	Retracted,
}

public enum SuspendKind
{
	Orgao,
	Fornecedor,
	Contratacao,
	Item,
	Flag,
}

public sealed record Coverage
{
	public required int N { get; init; }

	public required string Uf { get; init; }

	public required string Quarter { get; init; }

	public required string MethodologyVersion { get; init; }
}

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
}

public sealed record OrgaoPage
{
	public required IReadOnlyList<OrgaoRecord> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public int Total { get; init; }
}

public sealed record FornecedorRecord
{
	public required Guid Id { get; init; }

	public required string Cnpj { get; init; }

	public required string RazaoSocial { get; init; }

	public LocalDate? OpenedOn { get; init; }

	public string? Cnae { get; init; }

	public required Coverage Coverage { get; init; }
}

public sealed record FornecedorPage
{
	public required IReadOnlyList<FornecedorRecord> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public int Total { get; init; }
}

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
}

public sealed record ContratacaoPage
{
	public required IReadOnlyList<ContratacaoRecord> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public int Total { get; init; }
}

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

	public decimal? ValorPorUnidadeCanonica { get; init; }

	public required string Uf { get; init; }

	public required string Quarter { get; init; }

	public required string SnapshotId { get; init; }

	public required string MethodologyVersion { get; init; }

	public required Coverage Coverage { get; init; }
}

public sealed record ItemPage
{
	public required IReadOnlyList<ItemRecord> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public int Total { get; init; }
}

public sealed record ContratacaoDetail
{
	public required ContratacaoRecord Contratacao { get; init; }

	public required IReadOnlyList<ItemRecord> Items { get; init; }
}

public sealed record CoberturaMunicipio
{
	public required string Nome { get; init; }

	public required string Uf { get; init; }

	public required string Ibge { get; init; }
}

public sealed record CoberturaMunicipios
{
	public required int N { get; init; }

	public required IReadOnlyList<CoberturaMunicipio> Items { get; init; }
}

public sealed record CoberturaYearCount
{
	public required int Year { get; init; }

	public required int Compras { get; init; }

	public required int Items { get; init; }
}

public sealed record CoberturaRowCounts
{
	public required int Compras { get; init; }

	public required int Items { get; init; }

	public required IReadOnlyList<CoberturaYearCount> PerYear { get; init; }
}

public sealed record CoberturaSource
{
	public required string Name { get; init; }

	public Instant? LastUpdate { get; init; }

	public required int N { get; init; }
}

public sealed record CoberturaPayload
{
	public required CoberturaMunicipios Municipios { get; init; }

	public required IReadOnlyList<int> Years { get; init; }

	public required CoberturaRowCounts Rows { get; init; }

	public required decimal CatmatCoveragePercent { get; init; }

	public required int NCoded { get; init; }

	public required int NItems { get; init; }

	public required IReadOnlyList<CoberturaSource> Sources { get; init; }

	public required Coverage Coverage { get; init; }
}

public sealed record ItemDetail
{
	public required ItemRecord Item { get; init; }

	public required Guid OrgaoId { get; init; }

	public required string OrgaoRazaoSocial { get; init; }

	public string? FornecedorRazaoSocial { get; init; }

	public required string ContratacaoPncpId { get; init; }
}

public sealed record FlagPage
{
	public required IReadOnlyList<FlagRecord> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public int Total { get; init; }
}

public sealed record FlagRecord
{
	public required Guid Id { get; init; }

	public required Guid ItemId { get; init; }

	public required string Kind { get; init; }

	public required FlagState State { get; init; }

	public required Instant DetectedAt { get; init; }

	public Instant? NotifiedAt { get; init; }

	public string? NotifyArtifact { get; init; }

	public Instant? PublishAfter { get; init; }

	public Instant? PublishedAt { get; init; }

	public required string Delta { get; init; }

	public required string SourceUrl { get; init; }

	public required string SnapshotId { get; init; }

	public required string MethodologyVersion { get; init; }

	public string? ReplyText { get; init; }

	public Instant? RepliedAt { get; init; }

	public required bool Suspended { get; init; }

	public required string Framing { get; init; }
}

public sealed record CreateFlagRequest
{
	public required Guid ItemId { get; init; }

	public required string Kind { get; init; }

	public required string Delta { get; init; }

	public required string SourceUrl { get; init; }

	public required string SnapshotId { get; init; }

	public required string MethodologyVersion { get; init; }
}

public sealed record NotifyFlagRequest
{
	public string? Artifact { get; init; }
}

public sealed record ReplyFlagRequest
{
	public required string ReplyText { get; init; }
}

public sealed record SuspendRequest
{
	public required SuspendKind Kind { get; init; }

	public required Guid Id { get; init; }
}

public sealed record SuspendResponse
{
	public required SuspendKind Kind { get; init; }

	public required Guid Id { get; init; }

	public required bool Suspended { get; init; }
}
