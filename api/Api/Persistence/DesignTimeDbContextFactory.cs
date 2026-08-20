using Microsoft.EntityFrameworkCore.Design;

namespace Api.Persistence;

public sealed class DesignTimeDbContextFactory : IDesignTimeDbContextFactory<ApplicationDbContext>
{
	public ApplicationDbContext CreateDbContext(string[] args)
	{
		var options = new DbContextOptionsBuilder<ApplicationDbContext>()
			.UseNpgsql(
				"Host=localhost;Port=5432;Database=compras;Username=compras;Password=compras",
				o => o.UseNodaTime())
			.AddInterceptors(
				new TimestampInterceptor(SystemClock.Instance),
				new CpfGuardInterceptor())
			.Options;
		return new ApplicationDbContext(options);
	}
}
