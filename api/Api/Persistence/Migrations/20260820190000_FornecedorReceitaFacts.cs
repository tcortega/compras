using Api.Persistence;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Api.Persistence.Migrations
{
    /// <inheritdoc />
    [DbContext(typeof(ApplicationDbContext))]
    [Migration("20260820190000_FornecedorReceitaFacts")]
    public partial class FornecedorReceitaFacts : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "cnae",
                columns: table => new
                {
                    codigo = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                    descricao = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_cnae", x => x.codigo);
                });

            migrationBuilder.CreateTable(
                name: "fornecedor_socio",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    fornecedorId = table.Column<Guid>(type: "uuid", nullable: false),
                    fornecedorCnpj = table.Column<string>(type: "character varying(18)", maxLength: 18, nullable: false),
                    nome = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    cpfMasked = table.Column<string>(type: "character varying(18)", maxLength: 18, nullable: true),
                    qualificacao = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: true),
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_fornecedor_socio", x => x.id);
                    table.ForeignKey(
                        name: "FK_fornecedor_socio_fornecedor_fornecedorId",
                        column: x => x.fornecedorId,
                        principalTable: "fornecedor",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_fornecedor_socio_fornecedorCnpj",
                table: "fornecedor_socio",
                column: "fornecedorCnpj");

            migrationBuilder.CreateIndex(
                name: "IX_fornecedor_socio_fornecedorId",
                table: "fornecedor_socio",
                column: "fornecedorId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(name: "fornecedor_socio");
            migrationBuilder.DropTable(name: "cnae");
        }
    }
}
