using Api.Infrastructure.Startup;

namespace Api.Features.Shared;

internal static class Slice
{
	public static string Methodology(string? requested, IOptions<AppOptions> options) =>
		requested is { Length: > 0 } ? requested : options.Value.MethodologyVersion;

	public static Coverage Page(int n, string? uf, string? quarter, string methodologyVersion) =>
		new()
		{
			N = n,
			Uf = uf ?? "",
			Quarter = quarter ?? "",
			MethodologyVersion = methodologyVersion,
		};
}
