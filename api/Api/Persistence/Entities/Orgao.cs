using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class Orgao : ITimestamped, ISuspendable
{
	public Guid Id { get; init; }

	public required string Cnpj { get; set; }

	public required string RazaoSocial { get; set; }

	public Esfera Esfera { get; set; }

	public required string Poder { get; set; }

	public required string Uf { get; set; }

	public required string MunicipioIbge { get; set; }

	public required string MunicipioNome { get; set; }

	public bool Suspended { get; set; }

	public Instant CreatedAt { get; init; }

	public Instant UpdatedAt { get; set; }

	public List<Contratacao> Contratacoes { get; } = [];

	public sealed class Configuration : IEntityTypeConfiguration<Orgao>
	{
		public void Configure(EntityTypeBuilder<Orgao> builder)
		{
			builder.ToTable("orgao");
			builder.HasIndex(x => x.Cnpj).IsUnique();
			builder.Property(x => x.Cnpj).HasMaxLength(18);
			builder.Property(x => x.RazaoSocial).HasMaxLength(512);
			builder.Property(x => x.Esfera).HasConversion(ClosedSet.Text<Esfera>()).HasMaxLength(16);
			builder.Property(x => x.Poder).HasMaxLength(32);
			builder.Property(x => x.Uf).HasMaxLength(2);
			builder.Property(x => x.MunicipioIbge).HasMaxLength(8);
			builder.Property(x => x.MunicipioNome).HasMaxLength(128);
			builder.HasMany(x => x.Contratacoes)
				.WithOne(x => x.Orgao)
				.HasForeignKey(x => x.OrgaoId)
				.OnDelete(DeleteBehavior.Restrict);
		}
	}
}
