import { runTriageAction } from '@/app/interno/triagem/actions'
import { ACTION_LABEL, actionsFor, type FlagAction, type FlagRecord } from '@/lib/flags'

const ALL_ACTIONS: FlagAction[] = ['review', 'notify', 'publish', 'resolve', 'retract']

export function TriageActions({ flag }: { flag: FlagRecord }) {
  const allowed = new Set(actionsFor(flag.state))

  return (
    <div className="triage-actions">
      <div className="actions">
        {ALL_ACTIONS.map((action) => (
          <form key={action} action={runTriageAction}>
            <input type="hidden" name="id" value={flag.id} />
            <input type="hidden" name="action" value={action} />
            <button
              className={action === 'publish' ? 'btn-ghost' : 'btn'}
              type="submit"
              disabled={!allowed.has(action)}
            >
              {ACTION_LABEL[action]}
            </button>
          </form>
        ))}
      </div>
    </div>
  )
}
