# Tests

Read this before writing or touching a test.
JobsTests is the in-repo reference.
The cycle shape is copied from VsaTemplate `TodosTests`, mapped to xunit.

Syntax comes from VsaTemplate.
The filter comes from the research: a green suite is worthless if it still passes when the code is wrong.

## Prime directive

The spec (the issue, this repo's docs, the user path) is the source of truth, not the suite.
If a test conflicts with the spec, stop.
Do not make it pass.
Do not silently edit the test.
Say what is blocked and wait.

## Default

Every feature gets one integration FullCycle against the real API and a real SQLite file.
Unit tests exist only for Pi RPC framing (`agent_settled`) and the cliproxy loopback bind.

Two valid shapes: a FullCycle for a simple slice, and one method per behavior when TDD or a distinct rule needs its own red/green.
Do not write a test to raise a coverage number.
Line coverage is a diagnostic. Behavior coverage is the point.

## Fixture

One `BridgeApiFixture` via `IClassFixture<BridgeApiFixture>`.
Call `GetClient()` and talk Refit `IBridgeApi`.
Do not new a factory per test.
Do not mock handlers, EF, or the HTTP layer.
The stub worker is allowed only when the cycle is about the control plane, not about Pi.

xunit, not TUnit.
Do not copy `ClassDataSource` or `[Test]`.

## FullCycle

Use this for a simple slice whose happy path is the feature.
Name it `FullCycle_...`.
Walk the real user path: create, read, change, read, finish.

After each mutation, GET and assert the whole record.

```csharp
[Fact]
public async Task FullCycle_CreateContinueListGetStop()
{
	var client = fixture.GetClient();
	var created = await client.CreateJob(new() { Title = "Kraken module", Message = "hello" });
	await ValidateJob(client, created.Content);
}

private static async Task ValidateJob(IBridgeApi client, JobDetail expected)
{
	var loaded = await client.GetJob(expected.Job.Id);
	Assert.Equal(expected, loaded.Content);
}
```

Prefer `Assert.Equal` on the DTO.
Prefer `with { }` to build the next expected from values you computed, not from rerunning the code and pasting output.
The Validate helper may only GET and `Assert.Equal`.
It may not hide loops, branches, or swallowed failures.

Do not laundry-list fields.
Do not assert status codes, headers, or ProblemDetails unless that is the product.

## One method per behavior

Use this when the slice is not simple, or when TDD needs a single rule red before the rest exists.
One user visible behavior per method.
The name says the behavior: `GetUnknownJob_NotFound`, `CreateJob_Empty_BadRequest`, `Promote_Conflict_KicksBack`.

Same fixture, same Refit client, same boundary (HTTP, SQLite, events).
Same filter: the method must die when that behavior breaks.

Do not turn this into one method per endpoint (`Create_ReturnsCreated`).
That is a laundry list with extra names.
A NotFound or empty BadRequest test belongs here when it is a real product rule.

## Write it so it can fail

A new test is not accepted until it is seen failing for the right reason: an assertion, not a compile error, not a fixture typo.

Then mutate: break the production path the test claims to cover, rerun, confirm that test fails, revert the break.
If it still passes, delete the test.
State the mutation in the commit body.

This is the TestGen-LLM filter and the ACH point.
Raw tests are junk until they die when the code is wrong.

Holdout extra cases do not save a weak cycle.
If the happy path would stay green after a user-visible break, more 404 tests will not help.

## Existing tests are frozen during implementation

Do not modify, delete, skip, or weaken an existing test to make a slice pass.
Changing a test is its own task and its own diff.

A new test may ship in the same commit as the feature (we push slices atomically).
Write the test first, see it red, then implement.
Once it has gone red for the right reason, do not edit it to match a weaker implementation.
If the test looks wrong, stop and say so.

## Banned

Any of these in a diff is a failed slice, green or not:

* `Environment.Exit`, `Environment.FailFast`, or anything that kills the runner
* hooks or modules that patch xunit results
* overriding `Equals`, `==`, or a comparer on a DTO so assertions pass (record structural equality is required, not a cheat)
* `try/catch` or `if` around an assert so failure is swallowed
* new `Skip`, `Skip.If`, commented-out facts, or `Assert.True(true)`
* weakening `Assert.Equal(expected, actual)` to `NotNull` or dropping fields
* special-casing titles, ids, or payloads that exist only in the test
* retries or loops to get past a failure
* deriving expected values by running the code under test and pasting the output

## Determinism

A flaky test is a failing test.
Fix it or delete it on sight.

No `Thread.Sleep`.
No public network in the default suite.
No order dependence between facts beyond what the shared fixture already owns.
Wait on a condition, not a duration.

## Live Pi

The default suite and CI use the stub worker. That is the control-plane suite.

`BRIDGE_LIVE_PI=1` (and optional `BRIDGE_LIVE_MODEL`) runs the same worker-path tests against a real `pi --mode rpc` child. Same assertions. No live-only skips and no weakened equals.

Stub-seam tests (`HoldRuns`, `CrashBeforePid`) stay on fixtures that always stub. They are not a live-Pi concern.

Run briefs come from `LivePi` so a live turn does not try to write a module.

## Bugs

Start with a failing E2E reproduction the way a user hits it.
No reproduction, no fix.

## Do not

* Fake a passing test.
* Hit `HandleAsync` directly.
* Reset the store mid cycle unless the cycle needs a clean slate.
* Add FluentAssertions or a second assertion library.
* Chase coverage or mutation score as a number. Use mutation only as the "does this test actually die" check.
