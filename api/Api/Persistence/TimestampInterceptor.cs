using Microsoft.EntityFrameworkCore.Diagnostics;

namespace Api.Persistence;

public sealed class TimestampInterceptor(IClock clock) : SaveChangesInterceptor
{
	public override InterceptionResult<int> SavingChanges(
		DbContextEventData eventData,
		InterceptionResult<int> result)
	{
		Stamp(eventData.Context);
		return result;
	}

	public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
		DbContextEventData eventData,
		InterceptionResult<int> result,
		CancellationToken cancellationToken = default)
	{
		Stamp(eventData.Context);
		return ValueTask.FromResult(result);
	}

	private void Stamp(DbContext? context)
	{
		if (context is null)
			return;

		var now = clock.GetCurrentInstant();
		foreach (var entry in context.ChangeTracker.Entries<ITimestamped>())
		{
			if (entry.State is EntityState.Added)
			{
				entry.Property(entity => entity.CreatedAt).CurrentValue = now;
				entry.Property(entity => entity.UpdatedAt).CurrentValue = now;
			}

			if (entry.State is EntityState.Modified)
				entry.Property(entity => entity.UpdatedAt).CurrentValue = now;
		}
	}
}
