using System.Text.Json;
using Microsoft.AspNetCore.Diagnostics;

namespace Api.Infrastructure.Startup;

public sealed class ComprasExceptionHandler : IExceptionHandler
{
	private static readonly JsonSerializerOptions s_json = new()
	{
		PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
	};

	public async ValueTask<bool> TryHandleAsync(
		HttpContext httpContext,
		Exception exception,
		CancellationToken cancellationToken)
	{
		var (status, error) = exception switch
		{
			NotFoundException => (StatusCodes.Status404NotFound, exception.Message),
			ConflictException => (StatusCodes.Status409Conflict, exception.Message),
			BadRequestException => (StatusCodes.Status400BadRequest, exception.Message),
			_ => (StatusCodes.Status500InternalServerError, exception.Message),
		};

		httpContext.Response.StatusCode = status;
		httpContext.Response.ContentType = "application/json";
		await httpContext.Response.WriteAsync(
			JsonSerializer.Serialize(new { error }, s_json),
			cancellationToken);
		return true;
	}
}
