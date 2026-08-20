using System.Text.Json;
using System.Text.Json.Serialization;
using Api.Infrastructure.Startup;

namespace Api.Infrastructure.Search;

public sealed class MeiliClient(HttpClient http, IOptions<AppOptions> options) : IMeiliClient
{
	private static readonly JsonSerializerOptions s_json = new()
	{
		PropertyNameCaseInsensitive = true,
		PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
	};

	private readonly string _key = options.Value.MeiliMasterKey;

	public bool IsConfigured => http.BaseAddress is not null && options.Value.MeiliUrl.Length > 0;

	public async Task<MeiliSearchOutcome> SearchAsync(
		string q,
		string kind,
		int skip,
		int take,
		CancellationToken ct)
	{
		if (!IsConfigured)
			return MeiliSearchOutcome.Unset;

		using var request = new HttpRequestMessage(HttpMethod.Post, "indexes/compras/search");
		if (_key.Length > 0)
			request.Headers.TryAddWithoutValidation("Authorization", $"Bearer {_key}");
		request.Content = JsonContent.Create(
			new MeiliQuery
			{
				Q = q,
				Filter = $"kind = \"{kind}\"",
				Offset = skip,
				Limit = take,
				AttributesToRetrieve = ["id", "kind", "entityId", "text"],
				ShowRankingScore = false,
			},
			options: s_json);

		HttpResponseMessage response;
		try
		{
			response = await http.SendAsync(request, ct);
		}
		catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
		{
			return MeiliSearchOutcome.Unavailable;
		}

		using (response)
		{
			if (response.StatusCode is System.Net.HttpStatusCode.NotFound)
				return new() { Status = MeiliStatus.Ready, Hits = [], EstimatedTotal = 0 };
			if (!response.IsSuccessStatusCode)
				return MeiliSearchOutcome.Unavailable;

			var payload = await response.Content.ReadFromJsonAsync<MeiliResponse>(s_json, ct);
			if (payload is null)
				return new() { Status = MeiliStatus.Ready, Hits = [], EstimatedTotal = 0 };

			var hits = new List<MeiliHit>();
			foreach (var hit in payload.Hits)
			{
				if (hit.Banned)
					continue;
				if (!Guid.TryParse(hit.EntityId, out var id))
					continue;
				if (!string.Equals(hit.Kind, kind, StringComparison.Ordinal))
					continue;
				if (string.IsNullOrWhiteSpace(hit.Text))
					continue;
				hits.Add(new() { EntityId = id, Kind = kind, Text = hit.Text.Trim() });
			}

			return new()
			{
				Status = MeiliStatus.Ready,
				Hits = hits,
				EstimatedTotal = payload.EstimatedTotalHits ?? hits.Count,
			};
		}
	}

	private sealed class MeiliQuery
	{
		public required string Q { get; init; }

		public required string Filter { get; init; }

		public required int Offset { get; init; }

		public required int Limit { get; init; }

		public required IReadOnlyList<string> AttributesToRetrieve { get; init; }

		public required bool ShowRankingScore { get; init; }
	}

	private sealed class MeiliResponse
	{
		public List<MeiliDoc> Hits { get; init; } = [];

		public int? EstimatedTotalHits { get; init; }
	}

	private sealed class MeiliDoc
	{
		public string? EntityId { get; init; }

		public string? Kind { get; init; }

		public string? Text { get; init; }

		[JsonExtensionData]
		public Dictionary<string, JsonElement>? Extra { get; init; }

		public bool Banned
		{
			get
			{
				if (HasBannedName(Kind))
					return true;
				if (Extra is null)
					return false;
				foreach (var key in Extra.Keys)
				{
					if (HasBannedName(key))
						return true;
				}

				return false;
			}
		}

		private static bool HasBannedName(string? name) =>
			name is { Length: > 0 }
			&& (
				name.Contains("flag", StringComparison.OrdinalIgnoreCase)
				|| name.Contains("adjacenc", StringComparison.OrdinalIgnoreCase)
				|| name.Contains("shared_qsa", StringComparison.OrdinalIgnoreCase)
				|| name.Contains("cpf", StringComparison.OrdinalIgnoreCase)
				|| name.Contains("score", StringComparison.OrdinalIgnoreCase));
	}
}
