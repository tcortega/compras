using Refit;

namespace Api.Client;

public interface IComprasApi
{
	[Get("/api/orgaos")]
	Task<OrgaoPage> ListOrgaos(
		[Query] string? q = null,
		[Query] Esfera? esfera = null,
		[Query] string? uf = null,
		[Query] string? municipioIbge = null,
		[Query] string? quarter = null,
		[Query] string? methodologyVersion = null,
		[Query] int? skip = null,
		[Query] int? take = null);

	[Get("/api/orgaos/{id}")]
	Task<IApiResponse<OrgaoRecord>> GetOrgao(
		Guid id,
		[Query] string? quarter = null,
		[Query] string? methodologyVersion = null);

	[Get("/api/fornecedores")]
	Task<FornecedorPage> ListFornecedores(
		[Query] string? q = null,
		[Query] string? cnae = null,
		[Query] string? uf = null,
		[Query] string? quarter = null,
		[Query] string? methodologyVersion = null,
		[Query] int? skip = null,
		[Query] int? take = null);

	[Get("/api/fornecedores/{id}")]
	Task<IApiResponse<FornecedorRecord>> GetFornecedor(
		Guid id,
		[Query] string? uf = null,
		[Query] string? quarter = null,
		[Query] string? methodologyVersion = null);

	[Get("/api/contratacoes")]
	Task<ContratacaoPage> ListContratacoes(
		[Query] string? q = null,
		[Query] Guid? orgaoId = null,
		[Query] Guid? fornecedorId = null,
		[Query] int? ano = null,
		[Query] string? modalidade = null,
		[Query] string? uf = null,
		[Query] string? quarter = null,
		[Query] string? methodologyVersion = null,
		[Query] int? skip = null,
		[Query] int? take = null);

	[Get("/api/contratacoes/{id}")]
	Task<IApiResponse<ContratacaoDetail>> GetContratacao(Guid id);

	[Get("/api/items")]
	Task<ItemPage> ListItems(
		[Query] string? q = null,
		[Query] Guid? contratacaoId = null,
		[Query] Guid? fornecedorId = null,
		[Query] Guid? orgaoId = null,
		[Query] string? catmat = null,
		[Query] string? uf = null,
		[Query] string? quarter = null,
		[Query] string? methodologyVersion = null,
		[Query] int? skip = null,
		[Query] int? take = null);

	[Get("/api/items/{id}")]
	Task<IApiResponse<ItemDetail>> GetItem(Guid id);

	[Get("/api/cobertura")]
	Task<CoberturaPayload> GetCobertura();

	[Post("/api/internal/flags")]
	Task<IApiResponse<FlagRecord>> CreateFlag([Body] CreateFlagRequest body);

	[Get("/api/internal/flags")]
	Task<FlagPage> ListFlags(
		[Query] string? kind = null,
		[Query] FlagState? state = null,
		[Query] Guid? itemId = null,
		[Query] int? skip = null,
		[Query] int? take = null);

	[Get("/api/internal/flags/{id}")]
	Task<IApiResponse<FlagRecord>> GetFlag(Guid id);

	[Post("/api/internal/flags/{id}/review")]
	Task<IApiResponse<FlagRecord>> ReviewFlag(Guid id);

	[Post("/api/internal/flags/{id}/notify")]
	Task<IApiResponse<FlagRecord>> NotifyFlag(Guid id, [Body] NotifyFlagRequest? body = null);

	[Post("/api/internal/flags/{id}/publish")]
	Task<IApiResponse<FlagRecord>> PublishFlag(Guid id);

	[Post("/api/internal/flags/{id}/resolve")]
	Task<IApiResponse<FlagRecord>> ResolveFlag(Guid id);

	[Post("/api/internal/flags/{id}/retract")]
	Task<IApiResponse<FlagRecord>> RetractFlag(Guid id);

	[Post("/api/internal/flags/{id}/reply")]
	Task<IApiResponse<FlagRecord>> ReplyFlag(Guid id, [Body] ReplyFlagRequest body);

	[Post("/api/internal/suspend")]
	Task<IApiResponse<SuspendResponse>> Suspend([Body] SuspendRequest body);
}
