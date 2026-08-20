using Api.Persistence;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Api.Persistence.Migrations
{
    /// <inheritdoc />
    [DbContext(typeof(ApplicationDbContext))]
    [Migration("20260820160000_CoverageWarehouse")]
    public partial class CoverageWarehouse : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "catalog_code",
                columns: table => new
                {
                    codigo = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                    kind = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_catalog_code", x => new { x.codigo, x.kind });
                });

            migrationBuilder.CreateTable(
                name: "landing_source",
                columns: table => new
                {
                    name = table.Column<string>(type: "character varying(32)", maxLength: 32, nullable: false),
                    lastUpdate = table.Column<NodaTime.Instant>(type: "timestamp with time zone", nullable: true),
                    n = table.Column<int>(type: "integer", nullable: false),
                    snapshotId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: true),
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_landing_source", x => x.name);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(name: "catalog_code");
            migrationBuilder.DropTable(name: "landing_source");
        }
    }
}
