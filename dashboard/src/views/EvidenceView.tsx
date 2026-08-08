import { useMemo } from 'react'
import { useSemi } from '../engine/SemiContext'
import Inspector from '../components/Inspector'
import { Badge, SectionTitle } from '../components/ui'
import { STAGE_LABELS } from '../data/seed'

export default function EvidenceView() {
  const { engine, select, selectedId } = useSemi()

  const doneRows = useMemo(
    () => engine.state.rows.filter((r) => r.stage === 'done' || r.stage === 'conflict' || r.stage === 'refused'),
    [engine.state.rows],
  )

  return (
    <div className="flex h-full min-h-0">
      <div className="min-w-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-[1000px] space-y-5 p-5">
          <div>
            <h1 className="text-[23px] font-semibold tracking-tight text-slate-100">Evidence &amp; provenance</h1>
            <p className="mt-1 text-[13.5px] text-slate-400">
              every value traces to a source URL · page · quote · confidence
            </p>
          </div>

          <div className="panel p-4">
            <SectionTitle
              right={<span className="mono text-[10px] text-slate-600">{doneRows.length} rows</span>}
            >
              Worked rows
            </SectionTitle>
            <div className="space-y-1">
              {doneRows.length ? (
                doneRows.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => select(r.id)}
                    className={`focus-ring flex w-full items-center justify-between rounded-lg border border-line px-3 py-2 text-left transition-colors hover:bg-white/[0.03] ${
                      selectedId === r.id ? 'border-accent bg-accent-05' : ''
                    }`}
                  >
                    <div className="flex min-w-0 items-center gap-2.5">
                      <span className="mono text-[13px] font-medium text-slate-100">{r.pn}</span>
                      <Badge tone="cyan">{r.mfr}</Badge>
                      <Badge tone={r.stage === 'done' ? 'emerald' : r.stage === 'conflict' ? 'amber' : 'rose'}>
                        {STAGE_LABELS[r.stage]}
                      </Badge>
                    </div>
                    <span className="mono shrink-0 text-[11px] text-slate-500">
                      {r.sources.length} sources · {r.audits.filter((a) => a.state === 'pass').length}/5 audits
                    </span>
                  </button>
                ))
              ) : (
                <div className="py-8 text-center text-[13px] text-slate-500">no completed rows yet</div>
              )}
            </div>
          </div>

          <div className="panel p-4">
            <SectionTitle right={null}>Retrieval &amp; precedent notes</SectionTitle>
            <div className="mono grid gap-2 text-[11.5px] text-slate-500 sm:grid-cols-2">
              <div className="rounded-md border border-white/[0.1] bg-white/[0.03] px-2.5 py-2">
                ledger retrieval cosine threshold ≥ <span className="text-accent-strong">0.85</span>
              </div>
              <div className="rounded-md border border-white/[0.1] bg-white/[0.03] px-2.5 py-2">
                classifier retrained on <span className="text-accent-strong">{engine.state.retrains * 5}</span> rows (seeded + real)
              </div>
              <div className="rounded-md border border-white/[0.1] bg-white/[0.03] px-2.5 py-2">
                every ledger row writes <span className="text-accent-strong">source_url</span>
              </div>
              <div className="rounded-md border border-white/[0.1] bg-white/[0.03] px-2.5 py-2">
                no URL passes past the source validator
              </div>
            </div>
          </div>
        </div>
      </div>

      <Inspector showCloser={false} />
    </div>
  )
}