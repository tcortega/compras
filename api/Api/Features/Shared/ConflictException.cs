using System.Diagnostics.CodeAnalysis;

namespace Api.Features.Shared;

public sealed class ConflictException(string message) : Exception(message)
{
	[DoesNotReturn]
	public static void ThrowConflictException(string message) =>
		throw new ConflictException(message);
}
