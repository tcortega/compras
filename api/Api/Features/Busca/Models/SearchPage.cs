using Api.Features.Fornecedores.Models;
using Api.Features.Items.Models;
using Api.Features.Orgaos.Models;

namespace Api.Features.Busca.Models;

public sealed record SearchPage
{
	public const string SourceMeilisearch = "meilisearch";

	public const string SourceUnset = "unset";

	public const string SourceUnavailable = "unavailable";

	public required PageResult<OrgaoRecord> Orgaos { get; init; }

	public required PageResult<FornecedorRecord> Fornecedores { get; init; }

	public required PageResult<ItemRecord> Items { get; init; }

	public required Coverage Coverage { get; init; }

	public required string Source { get; init; }
}
