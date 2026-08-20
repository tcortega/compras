using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class Contratacao : ITimestamped, ISuspendable
{
	public Guid Id { get; init; }

	public required string PncpId { get; set; }

	public Guid OrgaoId { get; set; }

	public Orgao Orgao { get; set; } = null!;

	public required string Modalidade { get; set; }

	public required string Objeto { get; set; }

	public int Ano { get; set; }

	public decimal? ValorHomologado { get; set; }

	public Instant? PublicadoEm { get; set; }

	public required string Source { get; set; }

	public required string SnapshotId { get; set; }

	public required string MethodologyVersion { get; set; }

	public bool Suspended { get; set; }

	public Instant CreatedAt { get; init; }

	public Instant UpdatedAt { get; set; }

	public List<Item> Items { get; } = [];

	public sealed class Configuration : IEntityTypeConfiguration<Contratacao>
	{
		public void Configure(EntityTypeBuilder<Contratacao> builder)
		{
			builder.ToTable("contratacao");
			builder.HasIndex(x => x.PncpId).IsUnique();
			builder.HasIndex(x => x.OrgaoId);
			builder.Property(x => x.PncpId).HasMaxLength(128);
			builder.Property(x => x.Modalidade).HasMaxLength(64);
			builder.Property(x => x.Objeto).HasMaxLength(4000);
			builder.Property(x => x.ValorHomologado).HasPrecision(18, 4);
			builder.Property(x => x.Source).HasMaxLength(64);
			builder.Property(x => x.SnapshotId).HasMaxLength(128);
			builder.Property(x => x.MethodologyVersion).HasMaxLength(32);
			builder.HasMany(x => x.Items)
				.WithOne(x => x.Contratacao)
				.HasForeignKey(x => x.ContratacaoId)
				.OnDelete(DeleteBehavior.Restrict);
		}
	}
}
