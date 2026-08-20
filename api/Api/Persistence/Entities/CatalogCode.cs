using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class CatalogCode
{
	public required string Codigo { get; set; }

	public CatalogKind Kind { get; set; }

	public sealed class Configuration : IEntityTypeConfiguration<CatalogCode>
	{
		public void Configure(EntityTypeBuilder<CatalogCode> builder)
		{
			builder.ToTable("catalog_code");
			builder.HasKey(x => new { x.Codigo, x.Kind });
			builder.Property(x => x.Codigo).HasMaxLength(16);
			builder.Property(x => x.Kind).HasConversion(ClosedSet.Text<CatalogKind>()).HasMaxLength(16);
		}
	}
}
