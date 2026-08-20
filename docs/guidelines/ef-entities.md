# EF Core entities

Read this when adding or changing a type under `Api/Persistence/Entities/`.
Job and TranscriptEntry are the reference.

## Shape

```csharp
public sealed class Order
{
	public int Id { get; init; }
	public required string OrderNumber { get; set; }
	public string? Notes { get; set; }
	public Instant CreatedAt { get; init; }

	public int CustomerId { get; set; }
	public Customer Customer { get; set; } = null!;

	public List<OrderLine> Lines { get; } = [];

	public sealed class Configuration : IEntityTypeConfiguration<Order>
	{
		public void Configure(EntityTypeBuilder<Order> builder)
		{
			builder.ToTable("orders");
			builder.Property(x => x.OrderNumber).HasMaxLength(32);
		}
	}
}
```

Nullability in C# is the schema: `string` is NOT NULL, `string?` is NULL. Do not repeat that with `[Required]`.
`required` is a compile-time contract for our code. EF materialization ignores it.
`init` is for the key and fields that never change after insert (`CreatedAt`). Mutable business properties stay `{ get; set; }`.
Collections are never null: `{ get; } = []`. Reference navigations are `= null!;` (or nullable if unloaded is a valid check). Keep the FK + navigation pair.
`ApplicationDbContext.OnModelCreating` only calls `ApplyConfigurationsFromAssembly`. Mapping lives on the nested `Configuration`, not in the DbContext.

Import `Api.Persistence.Entities` and use the short type name.
`Entity.Run` / `Entity.Job` / `Entity.TranscriptEntry` only when a feature model shares that name. No `global::`. No per-type Row aliases.

Entities that have `CreatedAt` / `UpdatedAt` implement `ITimestamped` (`Job : ITimestamped`).
Those fields are `Instant`.
A `TimestampInterceptor` takes `IClock`, sets both on insert and `UpdatedAt` on update.
Handlers and background services do not assign those fields.

Closed sets on an entity are enums.
Store them as strings (`HasConversion` to a readable text value).

PostgreSQL via `UseNpgsql(cs, o => o.UseNodaTime())`.
Packages: `Npgsql.EntityFrameworkCore.PostgreSQL`, `Npgsql.EntityFrameworkCore.PostgreSQL.NodaTime`.
If you pass an `NpgsqlDataSource` into `UseNpgsql`, call `UseNodaTime` on the data source builder too.

`Instant` → `timestamptz` (UTC, no zone stored).
`LocalDateTime` → `timestamp`.
`LocalDate` → `date`.
`LocalTime` → `time`.
`Period` → `interval`.
Do not persist `ZonedDateTime`.
Need a zone? `Instant` plus a text zone-id column.

## Do

- Use a class, not a record. Records are for projections, DTOs, and owned value objects.
- Put `required` on non-nullable scalars. That is the replacement for `= null!;` / `= ""` / constructors-for-NRT.
- Put `init` on the primary key and genuinely immutable fields. EF sets them via backing fields, including store-generated keys after `SaveChanges`.
- Initialize collection navigations to empty. Do not initialize a reference navigation to `new Customer()`.
- Nest `IEntityTypeConfiguration<T>` as `public sealed class Configuration` on the entity. Lengths, indexes, table names, and relationships go there.
- For a required reference navigation, non-nullable + `= null!;` means "unloaded is a programmer error". Use `T?` if code may check whether it was loaded.
- Optional relationship: nullable FK (`int?`) plus nullable navigation.

## Don't

- Don't use records for tracked entities. Change tracking is reference identity; `with` makes a second instance.
- Don't put `init` on properties you load → modify → `SaveChanges`.
- Don't constructor-bind navigations. Constructor binding is scalars only.
- Don't use `[Required]` for column nullability. NRT already did that.
- Don't add `= null!;` on `DbSet<>` (EF Core 7+ initializes them).
- Don't put `required` on navigations just because the relationship is required. That forces every `new Order` to assign the navigation even when you only have the FK. Scalars get `required`; navigations get `= null!;` or `?`.
- Don't use BCL date/time types. `Instant`, not `DateTimeOffset`.
