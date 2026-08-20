# ASP.NET Core options

Read this when adding or changing configuration.

Use the options pattern.
Do not walk the tree, deserialize a file, overlay env vars by hand, and `AddSingleton` the result.

## Bind

`IConfiguration` is the source.
`appsettings.json`, environment variables, and `UseSetting` in tests all feed the same tree.
Do not read `Environment.GetEnvironmentVariable` at a call site.

```csharp
builder.Services.AddOptions<AppOptions>()
	.BindConfiguration("App")
	.PostConfigure<IConfiguration, IHostEnvironment>(AppOptionsSetup.Apply)
	.ValidateOnStart();
builder.Services.AddSingleton<IValidateOptions<AppOptions>, AppOptionsValidate>();
```

`BindConfiguration` is the bind.
Path resolve, computed defaults, and environment-specific order belong in `IPostConfigureOptions` / `PostConfigure`, not in a private `Load`.

## Fail at boot

`ValidateOnStart` throws `OptionsValidationException` at host start, not on the first request.
Prefer `IValidateOptions<T>` when more than one rule needs a message.

```csharp
public sealed class AppOptionsValidate : IValidateOptions<AppOptions>
{
	public ValidateOptionsResult Validate(string? name, AppOptions options)
	{
		if (string.IsNullOrWhiteSpace(options.Host))
			return ValidateOptionsResult.Fail("App:Host must not be empty.");
		return ValidateOptionsResult.Success;
	}
}
```

`[Range]`, `[Required]`, and `ValidateDataAnnotations()` are fine for a small closed set.
Use `IValidateOptions` when the rule needs `IConfiguration`, the environment, or more than one failure string.

## Call sites

Handlers and services take `IOptions<AppOptions>`.
Use `IOptionsMonitor<AppOptions>` only when the consumer must see a reload.

```csharp
private static ValueTask<Created<Order>> HandleAsync(
	Command request,
	IOptions<AppOptions> options,
	CancellationToken ct)
{
	var config = options.Value;
}
```

Do not `AddSingleton` the bound object.
Do not inject `AppOptions` directly once options exist.
Options types are classes with `{ get; set; }`.
Binding and `PostConfigure` assign properties.
Records we own still never use primary constructors.

## Tests

`WebApplicationFactory.UseSetting("App:...")` is the test overlay.
Do not special-case tests by reading env after bind.

## Do not

* Keep a second `AppOptions.Load` next to `IConfiguration`.
* Validate lazily in a handler when `ValidateOnStart` would have caught it.
