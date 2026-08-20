using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using Api;
using Api.Infrastructure.Startup;
using NodaTime.Serialization.SystemTextJson;
using Serilog;
using Serilog.Exceptions;

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseSerilog((_, _, logger) =>
	logger
		.MinimumLevel.Information()
		.Enrich.FromLogContext()
		.Enrich.WithEnvironmentName()
		.Enrich.WithThreadId()
		.Enrich.WithExceptionDetails()
		.WriteTo.Console(formatProvider: CultureInfo.InvariantCulture));

if (!builder.Environment.IsEnvironment("Testing"))
	builder.WebHost.UseUrls($"http://{builder.Configuration["App:Host"] ?? "127.0.0.1"}:{builder.Configuration["App:Port"] ?? "5080"}");

builder.Services.AddOptions<AppOptions>()
	.BindConfiguration("App")
	.PostConfigure<IConfiguration, IHostEnvironment>(AppOptionsSetup.Apply)
	.ValidateOnStart();
builder.Services.AddSingleton<IValidateOptions<AppOptions>, AppOptionsValidate>();

builder.Services.ConfigureHttpJsonOptions(options =>
{
	options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
	options.SerializerOptions.PropertyNameCaseInsensitive = true;
	options.SerializerOptions.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower));
	options.SerializerOptions.ConfigureForNodaTime(DateTimeZoneProviders.Tzdb);
});

builder.Services.AddApiServices();
builder.Services.AddExceptionHandler<ComprasExceptionHandler>();
builder.Services.AddProblemDetails();
builder.Services.AddApiHandlers();
builder.Services.AddDbContext<ApplicationDbContext>((sp, options) =>
	options
		.UseNpgsql(
			sp.GetRequiredService<IOptions<AppOptions>>().Value.ConnectionString,
			o => o.UseNodaTime())
		.AddInterceptors(
			new TimestampInterceptor(sp.GetRequiredService<IClock>()),
			new CpfGuardInterceptor()));
builder.Services.AddCors(options =>
	options.AddDefaultPolicy(policy =>
		policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod()));

var app = builder.Build();

if (!app.Environment.IsEnvironment("Testing"))
{
	using var scope = app.Services.CreateScope();
	var options = scope.ServiceProvider.GetRequiredService<IOptions<AppOptions>>().Value;
	if (options.ApplyMigrations)
	{
		var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
		db.Database.Migrate();
	}
}

app.UseExceptionHandler();
app.UseCors();
app.MapApiEndpoints();
app.Run();

public partial class Program;
