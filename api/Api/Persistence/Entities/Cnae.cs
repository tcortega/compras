using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class Cnae
{
	public required string Codigo { get; set; }

	public required string Descricao { get; set; }

	public sealed class Configuration : IEntityTypeConfiguration<Cnae>
	{
		public void Configure(EntityTypeBuilder<Cnae> builder)
		{
			builder.ToTable("cnae");
			builder.HasKey(x => x.Codigo);
			builder.Property(x => x.Codigo).HasMaxLength(16);
			builder.Property(x => x.Descricao).HasMaxLength(512);
		}
	}
}
