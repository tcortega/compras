using NodaTime.Text;

namespace Api.Features.Publication.Models;

public sealed record FlagAuditRecord
{
	public required string Id { get; init; }

	public required Guid FlagId { get; init; }

	public string? FromState { get; init; }

	public required string ToState { get; init; }

	public required Instant At { get; init; }

	public required string Actor { get; init; }

	public string? Reason { get; init; }

	public string? Delta { get; init; }
}

public sealed record FlagAuditPage
{
	public required IReadOnlyList<FlagAuditRecord> Items { get; init; }
}

internal sealed record FlagAuditSqlRow
{
	public string Id { get; init; } = "";

	public string FlagId { get; init; } = "";

	public string? FromState { get; init; }

	public string ToState { get; init; } = "";

	public string At { get; init; } = "";

	public string Actor { get; init; } = "";

	public string? Reason { get; init; }

	public string? Delta { get; init; }

	public FlagAuditRecord ToRecord() =>
		new()
		{
			Id = Id,
			FlagId = Guid.Parse(FlagId),
			FromState = FromState,
			ToState = ToState,
			At = FlagAuditAt.Parse(At),
			Actor = Actor,
			Reason = Reason,
			Delta = Delta,
		};
}

internal static class FlagAuditAt
{
	public static Instant Parse(string raw)
	{
		if (long.TryParse(raw, out var ticks))
			return Instant.FromUnixTimeTicks(ticks);

		var text = raw.Trim().Replace(' ', 'T');
		if (text.Length >= 3 && (text[^3] is '+' or '-') && !text[^3..].Contains(':', StringComparison.Ordinal))
			text = $"{text}:00";

		var instant = InstantPattern.ExtendedIso.Parse(text);
		if (instant.Success)
			return instant.Value;

		var offset = OffsetDateTimePattern.ExtendedIso.Parse(text);
		if (offset.Success)
			return offset.Value.ToInstant();

		var local = LocalDateTimePattern.ExtendedIso.Parse(text.TrimEnd('Z'));
		if (local.Success)
			return local.Value.InUtc().ToInstant();

		return Instant.FromUtc(1970, 1, 1, 0, 0);
	}
}
