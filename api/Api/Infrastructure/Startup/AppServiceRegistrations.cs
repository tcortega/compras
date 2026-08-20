namespace Api.Infrastructure.Startup;

public static class AppServiceRegistrations
{
	[RegisterServices]
	public static void Register(IServiceCollection services) =>
		services.AddSingleton<IClock>(SystemClock.Instance);
}
