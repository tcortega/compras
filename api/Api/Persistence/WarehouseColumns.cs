namespace Api.Persistence;

internal static class WarehouseColumns
{
	public static void Apply(ModelBuilder modelBuilder)
	{
		foreach (var entity in modelBuilder.Model.GetEntityTypes())
		{
			foreach (var property in entity.GetProperties())
				property.SetColumnName(CamelCase(property.Name));
		}
	}

	private static string CamelCase(string name)
	{
		if (name.Length <= 1)
			return name.ToLowerInvariant();
		return char.ToLowerInvariant(name[0]) + name[1..];
	}
}
