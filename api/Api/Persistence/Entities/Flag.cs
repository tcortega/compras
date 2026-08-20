using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Api.Persistence.Entities;

public sealed class Flag : ITimestamped, ISuspendable
{
	public static readonly Duration NotifyHold = Duration.FromDays(7);

	public Guid Id { get; init; }

	public Guid ItemId { get; set; }

	public Item Item { get; set; } = null!;

	public required string Kind { get; set; }

	public FlagState State { get; set; }

	public Instant DetectedAt { get; set; }

	public Instant? NotifiedAt { get; set; }

	public Instant? PublishAfter { get; set; }

	public Instant? PublishedAt { get; set; }

	public required string Delta { get; set; }

	public required string SourceUrl { get; set; }

	public required string SnapshotId { get; set; }

	public required string MethodologyVersion { get; set; }

	public string? ReplyText { get; set; }

	public Instant? RepliedAt { get; set; }

	public bool Suspended { get; set; }

	public Instant CreatedAt { get; init; }

	public Instant UpdatedAt { get; set; }

	public void Review()
	{
		if (State is not FlagState.Detected)
			ConflictException.ThrowConflictException("Flag is not in detected.");
		State = FlagState.InternalReview;
	}

	public void Notify(Instant now)
	{
		if (State is not FlagState.InternalReview)
			ConflictException.ThrowConflictException("Flag is not in internal_review.");
		State = FlagState.Notified;
		NotifiedAt = now;
		PublishAfter = now + NotifyHold;
	}

	public void Publish(Instant now)
	{
		if (State is not FlagState.Notified)
			ConflictException.ThrowConflictException("Flag is not in notified.");
		if (PublishAfter is not { } after || now < after)
			ConflictException.ThrowConflictException("Notify hold has not elapsed.");
		if (Suspended)
			ConflictException.ThrowConflictException("Flag is suspended.");
		State = FlagState.Published;
		PublishedAt = now;
	}

	public void Resolve()
	{
		if (State is not FlagState.Published)
			ConflictException.ThrowConflictException("Flag is not in published.");
		State = FlagState.Resolved;
	}

	public void Retract()
	{
		if (State is not FlagState.Published)
			ConflictException.ThrowConflictException("Flag is not in published.");
		State = FlagState.Retracted;
	}

	public void Reply(string text, Instant now)
	{
		if (State is FlagState.Detected or FlagState.InternalReview)
			ConflictException.ThrowConflictException("Flag has not been notified.");
		ReplyText = text;
		RepliedAt = now;
	}

	public sealed class Configuration : IEntityTypeConfiguration<Flag>
	{
		public void Configure(EntityTypeBuilder<Flag> builder)
		{
			builder.ToTable("flag");
			builder.HasIndex(x => x.ItemId);
			builder.HasIndex(x => x.State);
			builder.Property(x => x.Kind).HasMaxLength(64);
			builder.Property(x => x.State).HasConversion(ClosedSet.Text<FlagState>()).HasMaxLength(32);
			builder.Property(x => x.Delta).HasMaxLength(4000);
			builder.Property(x => x.SourceUrl).HasMaxLength(1024);
			builder.Property(x => x.SnapshotId).HasMaxLength(128);
			builder.Property(x => x.MethodologyVersion).HasMaxLength(32);
			builder.Property(x => x.ReplyText).HasMaxLength(8000);
		}
	}
}
