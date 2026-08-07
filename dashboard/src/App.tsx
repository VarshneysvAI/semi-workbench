import { Route, Routes } from 'react-router-dom'
import Aurora from './components/Aurora'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import CommandCenterView from './views/View0_CommandCenter'
import DiscoveryView from './views/View1_Discovery'
import AuditView from './views/View2_Audit'
import ConsensusView from './views/View3_Consensus'
import OutputView from './views/View4_Output'
import EvidenceView from './views/View5_Evidence'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-ink text-slate-200">
      <Aurora />
      <Sidebar />
      <div className="relative flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="min-h-0 flex-1 overflow-y-auto scroll-smooth">
          <Routes>
            <Route path="/" element={<CommandCenterView />} />
            <Route path="/discovery" element={<DiscoveryView />} />
            <Route path="/audit" element={<AuditView />} />
            <Route path="/consensus" element={<ConsensusView />} />
            <Route path="/output" element={<OutputView />} />
            <Route path="/evidence" element={<EvidenceView />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}