using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class Item : ITimestamped, ISuspendable
{
	public Guid Id { get; init; }

	public Guid ContratacaoId { get; set; }

	public Contratacao Contratacao { get; set; } = null!;

	public Guid? FornecedorId { get; set; }

	public Fornecedor? Fornecedor { get; set; }

	public required string Descricao { get; set; }

	public string? Catmat { get; set; }

	public string? Catser { get; set; }

	public decimal Quantidade { get; set; }

	public required string UnidadeMedida { get; set; }

	public string? UnidadeCanonica { get; set; }

	public decimal? ValorUnitario { get; set; }

	public decimal? ValorTotal { get; set; }

	public decimal? ValorPorUnidadeCanonica { get; set; }

	public string? SpecConcentracao { get; set; }

	public string? SpecDosagem { get; set; }

	public string? SpecTamanho { get; set; }

	public required string Uf { get; set; }

	public required string Quarter { get; set; }

	public required string SnapshotId { get; set; }

	public required string MethodologyVersion { get; set; }

	public bool Suspended { get; set; }

	public Instant CreatedAt { get; init; }

	public Instant UpdatedAt { get; set; }

	public List<Flag> Flags { get; } = [];

	public sealed class Configuration : IEntityTypeConfiguration<Item>
	{
		public void Configure(EntityTypeBuilder<Item> builder)
		{
			builder.ToTable("item");
			builder.HasIndex(x => x.ContratacaoId);
			builder.HasIndex(x => x.FornecedorId);
			builder.HasIndex(x => new { x.Uf, x.Quarter, x.Catmat });
			builder.Property(x => x.Descricao).HasMaxLength(2000);
			builder.Property(x => x.Catmat).HasMaxLength(16);
			builder.Property(x => x.Catser).HasMaxLength(16);
			builder.Property(x => x.Quantidade).HasPrecision(18, 6);
			builder.Property(x => x.UnidadeMedida).HasMaxLength(64);
			builder.Property(x => x.UnidadeCanonica).HasMaxLength(32);
			builder.Property(x => x.ValorUnitario).HasPrecision(18, 4);
			builder.Property(x => x.ValorTotal).HasPrecision(18, 4);
			builder.Property(x => x.ValorPorUnidadeCanonica).HasPrecision(18, 6);
			builder.Property(x => x.SpecConcentracao).HasMaxLength(64);
			builder.Property(x => x.SpecDosagem).HasMaxLength(64);
			builder.Property(x => x.SpecTamanho).HasMaxLength(64);
			builder.Property(x => x.Uf).HasMaxLength(2);
			builder.Property(x => x.Quarter).HasMaxLength(8);
			builder.Property(x => x.SnapshotId).HasMaxLength(128);
			builder.Property(x => x.MethodologyVersion).HasMaxLength(32);
			builder.HasMany(x => x.Flags)
				.WithOne(x => x.Item)
				.HasForeignKey(x => x.ItemId)
				.OnDelete(DeleteBehavior.Restrict);
		}
	}
}
