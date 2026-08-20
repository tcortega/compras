namespace Api.Infrastructure.Startup;

public sealed class AppOptions
{
	public string Host { get; set; } = "0.0.0.0";

	public int Port { get; set; } = 5080;

	public string ConnectionString { get; set; } = "";

	public string MethodologyVersion { get; set; } = "0.1";

	public bool ApplyMigrations { get; set; }
}
