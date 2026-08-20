namespace Api.Tests.Fixtures;

internal static class FlagStateMachineSqlite
{
	internal static readonly string[] s_statements =
	[
		"""
		CREATE TABLE IF NOT EXISTS flag_audit (
		  id INTEGER PRIMARY KEY AUTOINCREMENT,
		  "flagId" TEXT NOT NULL,
		  "fromState" TEXT,
		  "toState" TEXT NOT NULL,
		  at INTEGER NOT NULL,
		  actor TEXT NOT NULL,
		  reason TEXT,
		  delta TEXT
		)
		""",
		"""
		CREATE INDEX IF NOT EXISTS flag_audit_flag_idx ON flag_audit ("flagId")
		""",
		"""
		CREATE TRIGGER IF NOT EXISTS flag_audit_insert
		AFTER INSERT ON flag
		BEGIN
		  SELECT CASE
		    WHEN NEW.state = 'detected' THEN NULL
		    ELSE RAISE(ABORT, 'illegal flag state transition')
		  END;
		  INSERT INTO flag_audit ("flagId", "fromState", "toState", at, actor, delta)
		  VALUES (NEW.id, NULL, NEW.state, NEW."createdAt", 'internal/staging', NEW.delta);
		END
		""",
		"""
		CREATE TRIGGER IF NOT EXISTS flag_enforce_update
		BEFORE UPDATE OF state ON flag
		WHEN NEW.state IS NOT OLD.state
		BEGIN
		  SELECT CASE
		    WHEN OLD.state = 'detected' AND NEW.state = 'internal_review' THEN NULL
		    WHEN OLD.state = 'internal_review' AND NEW.state = 'notified' THEN NULL
		    WHEN OLD.state = 'notified' AND NEW.state = 'published' THEN NULL
		    WHEN OLD.state = 'published' AND NEW.state IN ('resolved', 'retracted') THEN NULL
		    ELSE RAISE(ABORT, 'illegal flag state transition')
		  END;
		END
		""",
		"""
		CREATE TRIGGER IF NOT EXISTS flag_audit_update
		AFTER UPDATE OF state ON flag
		WHEN NEW.state IS NOT OLD.state
		BEGIN
		  INSERT INTO flag_audit ("flagId", "fromState", "toState", at, actor)
		  VALUES (NEW.id, OLD.state, NEW.state, NEW."updatedAt", 'internal/staging');
		END
		""",
	];
}
