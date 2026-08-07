import { Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/TopBar'
import OverviewView from './views/View0_Overview'
import DiscoveryView from './views/View1_Discovery'
import AuditView from './views/View2_Audit'
import ConsensusView from './views/View3_Consensus'
import OutputView from './views/View4_Output'
import EvidenceView from './views/View5_Evidence'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="min-h-0 flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<OverviewView />} />
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