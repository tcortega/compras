using System.Text.Json;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace Api.Persistence;

public static class ClosedSet
{
	public static ValueConverter<T, string> Text<T>()
		where T : struct, Enum =>
		new(v => Format(v), v => Parse<T>(v));

	public static string Format<T>(T value)
		where T : struct, Enum =>
		JsonNamingPolicy.SnakeCaseLower.ConvertName(value.ToString());

	public static T Parse<T>(string value)
		where T : struct, Enum
	{
		foreach (var member in Enum.GetValues<T>())
		{
			if (string.Equals(Format(member), value, StringComparison.Ordinal))
				return member;
		}

		throw new ArgumentOutOfRangeException(nameof(value), value, $"Unknown {typeof(T).Name}.");
	}
}
