using System;
using Microsoft.EntityFrameworkCore.Migrations;
using NodaTime;

#nullable disable

namespace Api.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class Initial : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "fornecedor",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Cnpj = table.Column<string>(type: "character varying(18)", maxLength: 18, nullable: false),
                    RazaoSocial = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    OpenedOn = table.Column<LocalDate>(type: "date", nullable: true),
                    Cnae = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: true),
                    Suspended = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_fornecedor", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "orgao",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Cnpj = table.Column<string>(type: "character varying(18)", maxLength: 18, nullable: false),
                    RazaoSocial = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    Esfera = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                    Poder = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    Uf = table.Column<string>(type: "character varying(2)", maxLength: 2, nullable: false),
                    MunicipioIbge = table.Column<string>(type: "character varying(8)", maxLength: 8, nullable: false),
                    MunicipioNome = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    Suspended = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_orgao", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "contratacao",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    PncpId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    OrgaoId = table.Column<Guid>(type: "uuid", nullable: false),
                    Modalidade = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    Objeto = table.Column<string>(type: "character varying(4000)", maxLength: 4000, nullable: false),
                    Ano = table.Column<int>(type: "integer", nullable: false),
                    ValorHomologado = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    PublicadoEm = table.Column<Instant>(type: "timestamp with time zone", nullable: true),
                    Source = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    SnapshotId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    MethodologyVersion = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    Suspended = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_contratacao", x => x.Id);
                    table.ForeignKey(
                        name: "FK_contratacao_orgao_OrgaoId",
                        column: x => x.OrgaoId,
                        principalTable: "orgao",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "item",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ContratacaoId = table.Column<Guid>(type: "uuid", nullable: false),
                    FornecedorId = table.Column<Guid>(type: "uuid", nullable: true),
                    Descricao = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: false),
                    Catmat = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: true),
                    Catser = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: true),
                    Quantidade = table.Column<decimal>(type: "numeric(18,6)", precision: 18, scale: 6, nullable: false),
                    UnidadeMedida = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    UnidadeCanonica = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: true),
                    ValorUnitario = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    ValorTotal = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    Uf = table.Column<string>(type: "character varying(2)", maxLength: 2, nullable: false),
                    Quarter = table.Column<string>(type: "character varying(8)", maxLength: 8, nullable: false),
                    SnapshotId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    MethodologyVersion = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    Suspended = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item", x => x.Id);
                    table.ForeignKey(
                        name: "FK_item_contratacao_ContratacaoId",
                        column: x => x.ContratacaoId,
                        principalTable: "contratacao",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_fornecedor_FornecedorId",
                        column: x => x.FornecedorId,
                        principalTable: "fornecedor",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "flag",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ItemId = table.Column<Guid>(type: "uuid", nullable: false),
                    Kind = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    State = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    DetectedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false),
                    NotifiedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: true),
                    PublishAfter = table.Column<Instant>(type: "timestamp with time zone", nullable: true),
                    PublishedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: true),
                    Delta = table.Column<string>(type: "character varying(4000)", maxLength: 4000, nullable: false),
                    SourceUrl = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: false),
                    SnapshotId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    MethodologyVersion = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    ReplyText = table.Column<string>(type: "character varying(8000)", maxLength: 8000, nullable: true),
                    RepliedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: true),
                    Suspended = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<Instant>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_flag", x => x.Id);
                    table.ForeignKey(
                        name: "FK_flag_item_ItemId",
                        column: x => x.ItemId,
                        principalTable: "item",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_contratacao_OrgaoId",
                table: "contratacao",
                column: "OrgaoId");

            migrationBuilder.CreateIndex(
                name: "IX_contratacao_PncpId",
                table: "contratacao",
                column: "PncpId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_flag_ItemId",
                table: "flag",
                column: "ItemId");

            migrationBuilder.CreateIndex(
                name: "IX_flag_State",
                table: "flag",
                column: "State");

            migrationBuilder.CreateIndex(
                name: "IX_fornecedor_Cnpj",
                table: "fornecedor",
                column: "Cnpj",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_item_ContratacaoId",
                table: "item",
                column: "ContratacaoId");

            migrationBuilder.CreateIndex(
                name: "IX_item_FornecedorId",
                table: "item",
                column: "FornecedorId");

            migrationBuilder.CreateIndex(
                name: "IX_item_Uf_Quarter_Catmat",
                table: "item",
                columns: new[] { "Uf", "Quarter", "Catmat" });

            migrationBuilder.CreateIndex(
                name: "IX_orgao_Cnpj",
                table: "orgao",
                column: "Cnpj",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "flag");

            migrationBuilder.DropTable(
                name: "item");

            migrationBuilder.DropTable(
                name: "contratacao");

            migrationBuilder.DropTable(
                name: "fornecedor");

            migrationBuilder.DropTable(
                name: "orgao");
        }
    }
}
