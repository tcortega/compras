using System.Diagnostics.CodeAnalysis;

namespace Api.Features.Shared;

public sealed class BadRequestException(string message) : Exception(message)
{
	[DoesNotReturn]
	public static void ThrowBadRequestException(string message) =>
		throw new BadRequestException(message);
}
