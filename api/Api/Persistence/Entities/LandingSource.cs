using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class LandingSource
{
	public required string Name { get; set; }

	public Instant? LastUpdate { get; set; }

	public int N { get; set; }

	public string? SnapshotId { get; set; }

	public sealed class Configuration : IEntityTypeConfiguration<LandingSource>
	{
		public void Configure(EntityTypeBuilder<LandingSource> builder)
		{
			builder.ToTable("landing_source");
			builder.HasKey(x => x.Name);
			builder.Property(x => x.Name).HasMaxLength(32);
			builder.Property(x => x.SnapshotId).HasMaxLength(128);
		}
	}
}
