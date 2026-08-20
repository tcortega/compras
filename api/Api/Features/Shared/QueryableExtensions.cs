namespace Api.Features.Shared;

public static class QueryableExtensions
{
	public static IQueryable<T> SkipTake<T>(this IQueryable<T> query, PageRequest page) =>
		query.SkipTake(page.Skip ?? 0, page.Take ?? 0);

	public static IQueryable<T> SkipTake<T>(this IQueryable<T> query, int skip, int take)
	{
		var clampedSkip = skip is >= 0 ? skip : 0;
		var clampedTake = take switch
		{
			> PageRequest.MaxTake => PageRequest.MaxTake,
			> 0 => take,
			_ => PageRequest.DefaultTake,
		};
		return query.Skip(clampedSkip).Take(clampedTake);
	}
}
