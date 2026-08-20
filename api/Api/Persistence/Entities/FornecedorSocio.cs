using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class FornecedorSocio
{
	public Guid Id { get; init; }

	public Guid FornecedorId { get; set; }

	public required string FornecedorCnpj { get; set; }

	public required string Nome { get; set; }

	public string? CpfMasked { get; set; }

	public string? Qualificacao { get; set; }

	public Fornecedor Fornecedor { get; set; } = null!;

	public sealed class Configuration : IEntityTypeConfiguration<FornecedorSocio>
	{
		public void Configure(EntityTypeBuilder<FornecedorSocio> builder)
		{
			builder.ToTable("fornecedor_socio");
			builder.HasIndex(x => x.FornecedorCnpj);
			builder.HasIndex(x => x.FornecedorId);
			builder.Property(x => x.FornecedorCnpj).HasMaxLength(18);
			builder.Property(x => x.Nome).HasMaxLength(512);
			builder.Property(x => x.CpfMasked).HasMaxLength(18);
			builder.Property(x => x.Qualificacao).HasMaxLength(128);
			builder.HasOne(x => x.Fornecedor)
				.WithMany(x => x.Socios)
				.HasForeignKey(x => x.FornecedorId)
				.OnDelete(DeleteBehavior.Restrict);
		}
	}
}
