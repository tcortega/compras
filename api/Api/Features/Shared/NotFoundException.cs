using System.Diagnostics.CodeAnalysis;

namespace Api.Features.Shared;

public sealed class NotFoundException(string message = "Resource not found") : Exception(message)
{
	[DoesNotReturn]
	public static void ThrowNotFoundException(string? resource = null)
	{
		if (resource is null)
			throw new NotFoundException();
		throw new NotFoundException($"{resource} not found");
	}
}
