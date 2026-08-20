# C# idioms

Read this when writing or changing code under `Api/`.
CreateJob and JobWork are the in-repo reference.
The handler shape is copied from viceroypenguin/VsaTemplate.

## Handler

Nest `Command` and `Response` on the handler.
That is the slice.
Parking a return type in `Models/` because "that is where models go" is layer segregation, and VSA exists to fight that.

Promote a type to `Features/<Slice>/Models/` only when a second handler or the Refit client actually reuses it.
`Job` and `JobDetail` live there because create, get, and send all return them.
A response that exists for one handler stays nested.

```csharp
[Handler]
[MapPost("/api/todos/create")]
public static partial class CreateTodo
{
	[Validate]
	public sealed partial record Command : IValidationTarget<Command>
	{
		[NotEmpty]
		public required string Name { get; init; }
	}

	public sealed record Response
	{
		public required int TodoId { get; init; }
	}

	internal static Created<Response> TransformResult(Response response) =>
		TypedResults.Created($"/api/todos/{response.TodoId}", response);

	private static async ValueTask<Response> HandleAsync(
		Command command,
		CancellationToken ct)
	{
		var id = await SaveAsync(command, ct);
		return new() { TodoId = id };
	}
}
```

Handlers stay thin.
They talk to `DbContext`, other handlers, and the few services below.
A second call is not a reason to add a service.

## Handler vs service

Yes, either can pretend to be the other.
VsaTemplate does not.

A handler is one request in, one response out, through the Immediate pipeline.
HTTP handlers live in `Endpoints/` and have `[MapGet]` / `[MapPost]` / `[MapPut]`.
Internal handlers live in `Queries/` (or next to the cache they fill) and have `[Handler]` only.
`GetTodo` fills `TodoCache`. `GetUserId` is dispatched from auth. Both are handlers, not services.

A service outlives one request.
In his repo that is only:

* a cache (`TodoCache`, `UserRolesCache`) that wraps `Owned<IHandler<...>>`
* ambient context (`CurrentUserService` reads `HttpContext`)
* a process or gate that must be a singleton (our `JobTurnGate`, cliproxy host)

Use Immediate.Injections (`[RegisterSingleton]` / `[RegisterScoped]` / `[RegisterTransient]`) for the few allowed process, cache, or ambient types. Do not add a service just to have an attribute. Conditional registrations (cliproxy only when enabled, stub worker in Testing) go on a `[RegisterServices]` method, not a pile of `if`s in `Program.cs`.
`[RegisterSingleton]` is still a smell that you wanted a service.
If there is no cache, no ambient context, and no process, write a handler.

Do not add a `*Work` / `*Service` class to "coordinate" create/get/send.
Put the use case in the handler.
`JobWork` is leftover from before this rule. Do not copy it.

## Control flow

Do not write `else`.
VsaTemplate does not either.
This is habit, not an analyzer. Leave MA0071 off.

Use a guard and continue:

```csharp
if (cnt != 1)
	NotFoundException.ThrowNotFoundException("Job");
```

Invert the condition and return early.
Use `is not` when it reads cleaner.
Use a ternary for a value.
Use a switch expression for a mapping.
Single line `if` has no braces.

Test members with a property pattern, not a pile of `is null`s.

```csharp
if (snapshot is not { Pid: null })
	return;
```

Throw through helpers. Always. Never `throw new NotFoundException(...)` or `throw new ConflictException(...)` at a call site.

```csharp
if (row is null)
	NotFoundException.ThrowNotFoundException("Run");
```

Closed sets are enums, not strings: state, stop reason, restore, task class, and the like.

List endpoints are server-side paged from the first commit via the shared `PageRequest` / `SkipTake` helper. Do not copy page constants per slice. Do not `ToList` a growing table and page in memory.
List/query endpoints project in the IQueryable with a reusable `Expression` (see `Card.Project`). Do not `ToList` full entities and then `FromEntity` / `[.. list.Select(...)]`. If Vogen or JSON cannot translate, project a slim primitive row in SQL, then one cheap map.

## Types

Records we own never use primary constructors.
That is VSA0002: positional records fight queries and make refactors lie.

```csharp
public sealed record Job
{
	public required Guid Id { get; init; }
	public required string Title { get; init; }
}
```

Classes use a primary constructor where possible (`JobWork(...)`, test classes, behaviors, exception types).
Seal types.
`var` everywhere.
Expression-bodied only while the method is one statement.
The moment there is sequencing, use a block.

Import `Api.Persistence.Entities` in files with no name clash and use the short type name.
`Entity.X` is an escape hatch for a name clash only: the feature model and the entity share `Job`, `Run`, or `TranscriptEntry`.
`OutboxCard` has no feature twin (`Card`); never write `Entity.OutboxCard`.
Never write `global::`. Do not add per-type Row aliases.
The `Entity` alias lives in the csproj `ItemGroup Label="Usings"` (VsaTemplate shape).

Time is NodaTime.
Never `DateTime`, `DateTimeOffset`, `DateOnly`, `TimeOnly`, `TimeZoneInfo`, or `TimeProvider`.
`Instant` is a point in time.
`LocalDate` / `LocalTime` / `LocalDateTime` are civil values with no zone.
`Duration` is a fixed length.
`Period` is a calendrical length.
`DateTimeZone` is an IANA zone.
Now is `IClock`: register `SystemClock.Instance`, inject it, tests use `FakeClock` (`NodaTime.Testing`).
Do not call `SystemClock.Instance` at a call site.
`TimeSpan` only at BCL interop (timeouts, delays).
Do not store it.
JSON: `ConfigureHttpJsonOptions(o => o.SerializerOptions.ConfigureForNodaTime(DateTimeZoneProviders.Tzdb))` (`NodaTime.Serialization.SystemTextJson`).
Ban the BCL types with [BannedSymbols.txt](BannedSymbols.txt) and `Microsoft.CodeAnalysis.BannedApiAnalyzers`:

```xml
<ItemGroup>
	<GlobalPackageReference Include="Microsoft.CodeAnalysis.BannedApiAnalyzers" PrivateAssets="all" />
	<AdditionalFiles Include="$(MSBuildThisFileDirectory)BannedSymbols.txt" />
</ItemGroup>
```

## Do not

* Add an interface just to mock it.
* Put mapping in `OnModelCreating`. See [ef-entities.md](ef-entities.md).
* Bind options by hand or `AddSingleton` a loaded config. See [aspnet-core.md](aspnet-core.md).
* Use BCL date/time types. See Types.
* Copy VsaTemplate Auth0, Hangfire, email, Linq2DB, or TUnit.
* Move a one-handler `Response` into `Models/` for symmetry.
