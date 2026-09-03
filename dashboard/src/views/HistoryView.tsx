import { useEffect, useState } from 'react'
import { Download, Trash2, History, RefreshCw, FileText, CheckCircle2, AlertTriangle, XCircle, Search, ExternalLink, RotateCcw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getApiUrl } from '../config'
import { useSemi } from '../engine/SemiContext'

interface HistoryRecord {
  job_id: string
  filename: string
  timestamp: string
  total_rows: number
  success_count: number
  needs_review_count: number
  failed_count: number
  status: string
  output_dir: string
}

export default function HistoryView() {
  const [history, setHistory] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [retryingId, setRetryingId] = useState<string | null>(null)
  
  const { loadJob, retryJob } = useSemi()
  const navigate = useNavigate()

  const handleRetry = async (jobId: string) => {
    setRetryingId(jobId)
    try {
      await retryJob(jobId)
      navigate('/')
    } catch (err) {
      console.error('Failed to retry run:', err)
    } finally {
      setRetryingId(null)
    }
  }

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(getApiUrl('/api/history'))
      if (res.ok) {
        const data = await res.json()
        setHistory(data)
      }
    } catch (err) {
      console.error('Failed to fetch run history:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this run history record and its output files?')) return
    setDeletingId(jobId)
    try {
      const res = await fetch(getApiUrl(`/api/history/${jobId}`), { method: 'DELETE' })
      if (res.ok) {
        setHistory((prev) => prev.filter((item) => item.job_id !== jobId))
      }
    } catch (err) {
      console.error('Failed to delete history item:', err)
    } finally {
      setDeletingId(null)
    }
  }


  const filtered = history.filter(
    (item) =>
      item.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.job_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.status.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* Header section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-glow/20 border border-cyan-500/30 text-cyan-400">
              <History size={20} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100">Run History & Deliverables</h1>
              <p className="text-xs text-slate-400">
                View, download, and manage all past SEMI batch data validation runs and deliverables.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchHistory}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-200 hover:bg-white/10 hover:text-white transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh History
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search history by filename, job ID, or status..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/[0.04] py-2.5 pl-10 pr-4 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
        />
      </div>

      {/* Table container */}
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <RefreshCw size={24} className="animate-spin text-cyan-400 mb-3" />
            <span className="text-xs">Loading run history...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <FileText size={32} className="mb-3 text-slate-600" />
            <p className="text-sm font-medium text-slate-300">No Run History Found</p>
            <p className="text-xs text-slate-500 mt-1">Run a dataset from the Overview page to generate history logs.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 bg-white/[0.04] text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="px-6 py-3.5">Dataset Filename</th>
                  <th className="px-6 py-3.5">Job ID</th>
                  <th className="px-6 py-3.5">Date & Time</th>
                  <th className="px-6 py-3.5">Total Rows</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Extraction Breakdown</th>
                  <th className="px-6 py-3.5 text-right">Downloads & Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] text-slate-300">
                {filtered.map((item) => (
                  <tr key={item.job_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-100 flex items-center gap-2">
                      <FileText size={15} className="text-cyan-400 shrink-0" />
                      <span className="truncate max-w-[180px]" title={item.filename}>
                        {item.filename}
                      </span>
                    </td>
                    <td className="px-6 py-4 mono text-[11px] text-slate-400">
                      {item.job_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 text-slate-400 whitespace-nowrap">
                      {item.timestamp}
                    </td>
                    <td className="px-6 py-4 font-mono font-medium">
                      {item.total_rows}
                    </td>
                    <td className="px-6 py-4">
                      {item.status === 'COMPLETED' ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 size={12} />
                          COMPLETED
                        </span>
                      ) : item.status === 'RUNNING' ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-2.5 py-1 text-[10px] font-semibold text-cyan-400 border border-cyan-500/20">
                          <RefreshCw size={12} className="animate-spin" />
                          RUNNING
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-2.5 py-1 text-[10px] font-semibold text-rose-400 border border-rose-500/20">
                          <XCircle size={12} />
                          FAILED
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3 text-[11px]">
                        <span className="flex items-center gap-1 text-emerald-400" title="Success">
                          <CheckCircle2 size={12} /> {item.success_count}
                        </span>
                        <span className="flex items-center gap-1 text-amber-400" title="Needs Review">
                          <AlertTriangle size={12} /> {item.needs_review_count}
                        </span>
                        <span className="flex items-center gap-1 text-rose-400" title="Failed">
                          <XCircle size={12} /> {item.failed_count}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleRetry(item.job_id)}
                          disabled={retryingId === item.job_id || item.status === 'RUNNING'}
                          title="Re-run extraction pipeline for this dataset"
                          className="flex items-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1.5 text-[11px] font-medium text-amber-300 hover:bg-amber-500/20 transition-colors"
                        >
                          <RotateCcw size={13} className={retryingId === item.job_id ? 'animate-spin' : ''} />
                          Retry Run
                        </button>
                        <button
                          onClick={() => {
                            loadJob(item.job_id)
                            navigate('/')
                          }}
                          title="Load Job Data into Dashboard"
                          className="flex items-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1.5 text-[11px] font-medium text-indigo-300 hover:bg-indigo-500/20 transition-colors"
                        >
                          <ExternalLink size={13} />
                          Open in Dashboard
                        </button>
                        {item.status === 'COMPLETED' && (
                          <>
                            <a
                              href={getApiUrl(`/api/history/${item.job_id}/download/Unihack_Delivery_Format_Output.csv`)}
                              target="_blank"
                              rel="noreferrer"
                              title="Download 252-column Unilog Delivery CSV"
                              className="flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1.5 text-[11px] font-medium text-cyan-300 hover:bg-cyan-500/20 transition-colors"
                            >
                              <Download size={13} />
                              Delivery CSV
                            </a>
                            <a
                              href={getApiUrl(`/api/history/${item.job_id}/download/status_report.csv`)}
                              target="_blank"
                              rel="noreferrer"
                              title="Download Status Report CSV"
                              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-[11px] font-medium text-slate-300 hover:bg-white/10 transition-colors"
                            >
                              <Download size={13} />
                              Status Report
                            </a>
                            <a
                              href={getApiUrl(`/api/history/${item.job_id}/download/input.csv`)}
                              target="_blank"
                              rel="noreferrer"
                              title="Download Original Input CSV"
                              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-[11px] font-medium text-slate-300 hover:bg-white/10 transition-colors"
                            >
                              <Download size={13} />
                              Original Input
                            </a>
                          </>
                        )}
                        <button
                          onClick={() => handleDelete(item.job_id)}
                          disabled={deletingId === item.job_id}
                          title="Delete History Record"
                          className="flex items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/10 p-1.5 text-rose-400 hover:bg-rose-500/20 hover:text-rose-300 transition-colors"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
