using Api.Persistence.Entities;

namespace Api.Persistence;

public sealed class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : DbContext(options)
{
	public DbSet<Orgao> Orgaos => Set<Orgao>();

	public DbSet<Fornecedor> Fornecedores => Set<Fornecedor>();

	public DbSet<Contratacao> Contratacoes => Set<Contratacao>();

	public DbSet<Item> Items => Set<Item>();

	public DbSet<Flag> Flags => Set<Flag>();

	public DbSet<CatalogCode> CatalogCodes => Set<CatalogCode>();

	public DbSet<LandingSource> LandingSources => Set<LandingSource>();

	protected override void ConfigureConventions(ModelConfigurationBuilder configurationBuilder)
	{
		if (Database.ProviderName is { Length: > 0 }
			&& !string.Equals(Database.ProviderName, "Microsoft.EntityFrameworkCore.Sqlite", StringComparison.Ordinal))
			return;

		configurationBuilder.Properties<Instant>().HaveConversion<InstantTicksConverter>();
		configurationBuilder.Properties<Instant?>().HaveConversion<NullableInstantTicksConverter>();
		configurationBuilder.Properties<LocalDate>().HaveConversion<LocalDateTextConverter>();
		configurationBuilder.Properties<LocalDate?>().HaveConversion<NullableLocalDateTextConverter>();
	}

	protected override void OnModelCreating(ModelBuilder modelBuilder)
	{
		modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
		WarehouseColumns.Apply(modelBuilder);
	}
}
