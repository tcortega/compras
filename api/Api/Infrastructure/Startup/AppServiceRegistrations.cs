using Api.Infrastructure.Search;

namespace Api.Infrastructure.Startup;

public static class AppServiceRegistrations
{
	[RegisterServices]
	public static void Register(IServiceCollection services)
	{
		services.AddSingleton<IClock>(SystemClock.Instance);
		services.AddHttpClient<IMeiliClient, MeiliClient>((sp, client) =>
		{
			var options = sp.GetRequiredService<IOptions<AppOptions>>().Value;
			if (options.MeiliUrl is { Length: > 0 } url)
				client.BaseAddress = new Uri(url.EndsWith('/') ? url : url + "/");
			client.Timeout = TimeSpan.FromSeconds(5);
		});
	}
}
