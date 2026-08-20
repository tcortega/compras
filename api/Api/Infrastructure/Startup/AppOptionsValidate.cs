namespace Api.Infrastructure.Startup;

public sealed class AppOptionsValidate : IValidateOptions<AppOptions>
{
	public ValidateOptionsResult Validate(string? name, AppOptions options)
	{
		var failures = new List<string>();
		if (string.IsNullOrWhiteSpace(options.Host))
			failures.Add("App:Host must not be empty.");
		if (options.Port is < 1 or > 65535)
			failures.Add("App:Port must be between 1 and 65535.");
		if (string.IsNullOrWhiteSpace(options.ConnectionString))
			failures.Add("ConnectionStrings:Compras must not be empty.");
		if (string.IsNullOrWhiteSpace(options.MethodologyVersion))
			failures.Add("App:MethodologyVersion must not be empty.");
		if (failures.Count == 0)
			return ValidateOptionsResult.Success;
		return ValidateOptionsResult.Fail(failures);
	}
}
