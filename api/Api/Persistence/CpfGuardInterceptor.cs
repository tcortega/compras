using System.Text.RegularExpressions;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace Api.Persistence;

public sealed partial class CpfGuardInterceptor : SaveChangesInterceptor
{
	public override InterceptionResult<int> SavingChanges(
		DbContextEventData eventData,
		InterceptionResult<int> result)
	{
		RejectRawCpf(eventData.Context);
		return result;
	}

	public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
		DbContextEventData eventData,
		InterceptionResult<int> result,
		CancellationToken cancellationToken = default)
	{
		RejectRawCpf(eventData.Context);
		return ValueTask.FromResult(result);
	}

	private static void RejectRawCpf(DbContext? context)
	{
		if (context is null)
			return;

		foreach (var entry in context.ChangeTracker.Entries())
		{
			if (entry.State is not (EntityState.Added or EntityState.Modified))
				continue;

			foreach (var property in entry.Properties)
			{
				if (property.CurrentValue is not string text)
					continue;
				if (!ContainsRawCpf(text))
					continue;
				BadRequestException.ThrowBadRequestException("CPF must not be stored raw.");
			}
		}
	}

	internal static bool ContainsRawCpf(string text)
	{
		if (FormattedCpf().IsMatch(text))
			return true;
		if (text.Length != 11 || !Digits().IsMatch(text))
			return false;
		return HasCpfChecksum(text);
	}

	private static bool HasCpfChecksum(string digits)
	{
		var values = new int[11];
		for (var i = 0; i < 11; i++)
			values[i] = digits[i] - '0';

		if (values.Distinct().Count() == 1)
			return false;

		var d1 = CheckDigit(values, 9, 10);
		var d2 = CheckDigit(values, 10, 11);
		return values[9] == d1 && values[10] == d2;
	}

	private static int CheckDigit(int[] values, int length, int weightStart)
	{
		var sum = 0;
		for (var i = 0; i < length; i++)
			sum += values[i] * (weightStart - i);
		var rem = sum % 11;
		return rem < 2 ? 0 : 11 - rem;
	}

	[GeneratedRegex(@"\d{3}\.\d{3}\.\d{3}-\d{2}", RegexOptions.CultureInvariant)]
	private static partial Regex FormattedCpf();

	[GeneratedRegex(@"^\d{11}$", RegexOptions.CultureInvariant)]
	private static partial Regex Digits();
}
