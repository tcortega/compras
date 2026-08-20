using Microsoft.EntityFrameworkCore.Storage.ValueConversion;
using NodaTime.Text;

namespace Api.Persistence;

internal sealed class InstantTicksConverter() : ValueConverter<Instant, long>(
	v => v.ToUnixTimeTicks(),
	v => Instant.FromUnixTimeTicks(v));

internal sealed class NullableInstantTicksConverter() : ValueConverter<Instant?, long?>(
	v => v == null ? null : v.Value.ToUnixTimeTicks(),
	v => v == null ? null : Instant.FromUnixTimeTicks(v.Value));

internal sealed class LocalDateTextConverter() : ValueConverter<LocalDate, string>(
	v => LocalDatePattern.Iso.Format(v),
	v => LocalDatePattern.Iso.Parse(v).Value);

internal sealed class NullableLocalDateTextConverter() : ValueConverter<LocalDate?, string?>(
	v => v == null ? null : LocalDatePattern.Iso.Format(v.Value),
	v => v == null ? null : LocalDatePattern.Iso.Parse(v).Value);
