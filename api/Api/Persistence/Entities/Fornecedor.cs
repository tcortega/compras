using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class Fornecedor : ITimestamped, ISuspendable
{
	public Guid Id { get; init; }

	public required string Cnpj { get; set; }

	public required string RazaoSocial { get; set; }

	public LocalDate? OpenedOn { get; set; }

	public string? Cnae { get; set; }

	public bool Suspended { get; set; }

	public Instant CreatedAt { get; init; }

	public Instant UpdatedAt { get; set; }

	public List<Item> Items { get; } = [];

	public List<FornecedorSocio> Socios { get; } = [];

	public sealed class Configuration : IEntityTypeConfiguration<Fornecedor>
	{
		public void Configure(EntityTypeBuilder<Fornecedor> builder)
		{
			builder.ToTable("fornecedor");
			builder.HasIndex(x => x.Cnpj).IsUnique();
			builder.Property(x => x.Cnpj).HasMaxLength(18);
			builder.Property(x => x.RazaoSocial).HasMaxLength(512);
			builder.Property(x => x.Cnae).HasMaxLength(16);
			builder.HasMany(x => x.Items)
				.WithOne(x => x.Fornecedor)
				.HasForeignKey(x => x.FornecedorId)
				.OnDelete(DeleteBehavior.Restrict);
		}
	}
}
