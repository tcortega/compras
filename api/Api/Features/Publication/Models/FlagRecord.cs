using Api.Persistence.Entities;

namespace Api.Features.Publication.Models;

public sealed record FlagRecord
{
	public const string FramingText = "indicio requiring verification";

	public required Guid Id { get; init; }

	public required Guid ItemId { get; init; }

	public required string Kind { get; init; }

	public required FlagState State { get; init; }

	public required Instant DetectedAt { get; init; }

	public Instant? NotifiedAt { get; init; }

	public Instant? PublishAfter { get; init; }

	public Instant? PublishedAt { get; init; }

	public required string Delta { get; init; }

	public required string SourceUrl { get; init; }

	public required string SnapshotId { get; init; }

	public required string MethodologyVersion { get; init; }

	public string? ReplyText { get; init; }

	public Instant? RepliedAt { get; init; }

	public required bool Suspended { get; init; }

	public required string Framing { get; init; }

	public static FlagRecord FromEntity(Flag flag) =>
		new()
		{
			Id = flag.Id,
			ItemId = flag.ItemId,
			Kind = flag.Kind,
			State = flag.State,
			DetectedAt = flag.DetectedAt,
			NotifiedAt = flag.NotifiedAt,
			PublishAfter = flag.PublishAfter,
			PublishedAt = flag.PublishedAt,
			Delta = flag.Delta,
			SourceUrl = flag.SourceUrl,
			SnapshotId = flag.SnapshotId,
			MethodologyVersion = flag.MethodologyVersion,
			ReplyText = flag.ReplyText,
			RepliedAt = flag.RepliedAt,
			Suspended = flag.Suspended,
			Framing = FramingText,
		};
}
