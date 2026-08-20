namespace Api.Infrastructure.Logging;

public sealed class LoggingBehavior<TRequest, TResponse>(
	ILogger<LoggingBehavior<TRequest, TResponse>> logger) : Behavior<TRequest, TResponse>
{
	public override async ValueTask<TResponse> HandleAsync(TRequest request, CancellationToken cancellationToken)
	{
		logger.LogInformation("Entering {Handler}", HandlerType.Name);
		var response = await Next(request, cancellationToken);
		logger.LogInformation("Exiting {Handler}", HandlerType.Name);
		return response;
	}
}
