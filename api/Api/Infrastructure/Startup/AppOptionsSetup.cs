namespace Api.Infrastructure.Startup;

public static class AppOptionsSetup
{
	public static void Apply(AppOptions options, IConfiguration configuration, IHostEnvironment environment)
	{
		if (options.Port is not > 0)
			options.Port = 5080;
		if (string.IsNullOrWhiteSpace(options.Host))
			options.Host = environment.IsDevelopment() ? "127.0.0.1" : "0.0.0.0";
		if (string.IsNullOrWhiteSpace(options.MethodologyVersion))
			options.MethodologyVersion = "0.1";

		var connectionString = configuration.GetConnectionString("Compras");
		if (string.IsNullOrWhiteSpace(connectionString))
			connectionString = "Host=localhost;Port=5432;Database=compras;Username=compras;Password=compras";
		options.ConnectionString = connectionString;
	}
}
