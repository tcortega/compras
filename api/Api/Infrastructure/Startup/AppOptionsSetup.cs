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
			options.MethodologyVersion = "0.2";

		var connectionString = configuration.GetConnectionString("Compras");
		if (string.IsNullOrWhiteSpace(connectionString))
			connectionString = "Host=localhost;Port=5432;Database=compras;Username=compras;Password=compras";
		options.ConnectionString = connectionString;

		if (!environment.IsEnvironment("Testing"))
		{
			if (string.IsNullOrWhiteSpace(options.MeiliUrl))
				options.MeiliUrl = FirstNonEmpty(configuration["MEILI_URL"], Environment.GetEnvironmentVariable("MEILI_URL"));
			if (string.IsNullOrWhiteSpace(options.MeiliMasterKey))
				options.MeiliMasterKey = FirstNonEmpty(
					configuration["MEILI_MASTER_KEY"],
					Environment.GetEnvironmentVariable("MEILI_MASTER_KEY"));
		}

		options.MeiliUrl = options.MeiliUrl.Trim();
		options.MeiliMasterKey = options.MeiliMasterKey.Trim();
	}

	private static string FirstNonEmpty(params string?[] values)
	{
		foreach (var value in values)
		{
			if (!string.IsNullOrWhiteSpace(value))
				return value.Trim();
		}

		return "";
	}
}
