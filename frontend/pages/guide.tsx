import { motion } from 'motion/react'
import {
  ArrowRight,
  Bot,
  BrainCircuit,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  ListChecks,
  Network,
  RotateCcw,
  Sparkles,
  Workflow,
  type LucideIcon,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const systemSteps = [
  {
    title: 'Create poker personalities',
    icon: Bot,
    body: 'PokerLab starts with built-in agents like Tight-Aggressive, Loose-Aggressive, Calling Station, and Random.',
  },
  {
    title: 'Run simulated hands',
    icon: Workflow,
    body: 'The simulator deals cards, moves the hand forward, and lets each agent make choices.',
  },
  {
    title: 'Record every decision',
    icon: Database,
    body: 'Before an agent acts, PokerLab saves what the table looked like and what the agent chose.',
  },
  {
    title: 'Build feature vectors',
    icon: Network,
    body: 'Cards, position, stack size, pot size, board texture, and betting pressure become structured training features.',
  },
  {
    title: 'Score what happened later',
    icon: Gauge,
    body: 'The system tracks the result of the hand so each decision can be connected to profit or loss.',
  },
  {
    title: 'Train the Random Forest',
    icon: BrainCircuit,
    body: 'Many small decision trees learn patterns from the examples, then vote or average together.',
    highlight: true,
  },
  {
    title: 'Save an EV model',
    icon: BrainCircuit,
    body: 'The trained model can estimate expected value for actions like fold, call, check, bet, or all-in.',
  },
  {
    title: 'Score each legal action',
    icon: ListChecks,
    body: 'For a new poker spot, PokerLab creates a row for every legal action and asks the model to score each one.',
  },
  {
    title: 'MLAgent picks the best score',
    icon: Sparkles,
    body: 'The MLAgent chooses the action with the highest predicted expected value.',
  },
  {
    title: 'Custom strategies join the loop',
    icon: FlaskConical,
    body: 'A typed strategy becomes an agent, gets simulated, gets diagnosed, and can be patched.',
  },
]

const modelOutputs = [
  ['Hand Strength Model', 'Classifies hand-strength buckets from engineered poker state features.'],
  ['Opponent Action Model', 'Learns what actions different simulated styles usually take in similar spots.'],
  ['Bluff Detector', 'Flags likely bluff patterns when low-strength hands take aggressive actions.'],
  ['EV Regressor', 'Predicts the expected profit of each possible action in the current state.'],
]

const customSteps = [
  ['Write strategy', 'Example: "Play aggressive preflop, bluff rivers often, and fold less to small bets."'],
  ['Compile config', 'The app maps that sentence into strategy parameters like aggression, tightness, bluff frequency, and call threshold.'],
  ['Create agent', 'That config becomes a custom poker agent that can play inside the simulator.'],
  ['Stress test', 'The custom agent plays against built-in baselines so PokerLab can measure strengths and leaks.'],
  ['Patch and rerun', 'The app suggests parameter changes and reruns the diagnostic to see if the strategy improved.'],
]

export default function GuidePage() {
  return (
    <div className="max-w-7xl">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <Badge variant="outline" className="mb-3">How it works</Badge>
        <h2 className="text-3xl font-semibold tracking-tight">PokerLab System Overview</h2>
        <p className="text-zinc-400 text-sm mt-2 max-w-3xl">
          PokerLab is a simulation-driven ML system for poker strategy. It generates synthetic hands,
          converts decision states into feature vectors, trains Random Forest models on supervised labels
          and EV targets, then uses the trained model to evaluate new decisions and custom strategies.
        </p>
      </motion.div>

      <TenStepGuide />
      <LearningLoopVisual />

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_.9fr] gap-6 mt-6">
        <Card>
          <CardHeader>
            <CardTitle>What the Random Forest Learns</CardTitle>
            <CardDescription>
              The model does not understand poker like a human. It learns patterns from examples.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {modelOutputs.map(([title, body]) => (
              <div key={title} className="rounded-lg border border-white/10 bg-zinc-950 p-4">
                <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-md bg-white text-black">
                  <BrainCircuit size={16} />
                </div>
                <h3 className="text-sm font-medium">{title}</h3>
                <p className="text-xs text-zinc-500 mt-2 leading-relaxed">{body}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>EV Decision Loop</CardTitle>
            <CardDescription>How the MLAgent picks one action.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg bg-white text-black p-4">
              <p className="text-sm font-medium">Same decision state, multiple legal actions:</p>
              <div className="mt-3 space-y-2 text-xs">
                <ScoreRow action="Fold" score="-1.20 expected value" />
                <ScoreRow action="Call" score="+0.15 expected value" />
                <ScoreRow action="Small bet" score="+0.42 expected value" winner />
                <ScoreRow action="All-in" score="-0.65 expected value" />
              </div>
              <p className="text-xs text-zinc-700 mt-3">
                The Random Forest outputs scores. The MLAgent chooses the highest score.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Custom Strategy Path</CardTitle>
          <CardDescription>
            How a plain-English strategy becomes something the app can test.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {customSteps.map(([title, body], index) => (
              <div key={title} className="rounded-lg border border-white/10 bg-zinc-950 p-4">
                <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-md bg-white text-black">
                  <span className="text-sm font-semibold">{index + 1}</span>
                </div>
                <h3 className="text-sm font-medium">{title}</h3>
                <p className="text-xs text-zinc-500 mt-2 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Portfolio Summary</CardTitle>
          <CardDescription>A concise way to describe the system on your website.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-white/10 bg-zinc-950 p-5">
            <p className="text-sm text-zinc-300 leading-relaxed">
              PokerLab is a simulation-driven AI strategy platform. It generates synthetic poker decisions
              from rule-based agents, converts game states into engineered ML features, trains Random Forest
              models to estimate behavior and expected value, and uses those models to power an MLAgent.
              Users can also write a natural-language strategy, compile it into an executable agent,
              simulate it against baselines, detect leaks, and test recommended patches.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function TenStepGuide() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Step-by-Step Story</CardTitle>
        <CardDescription>
          The whole system in 10 steps, from simulated hands to model-backed decisions.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
          {systemSteps.map((step, index) => (
            <StepCard key={step.title} step={step} index={index} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function LearningLoopVisual() {
  const phases = [
    { title: 'Agents', subtitle: 'Different player styles', icon: GitBranch },
    { title: 'Simulator', subtitle: 'Runs synthetic hands', icon: Workflow },
    { title: 'Dataset', subtitle: 'Stores labels and outcomes', icon: Database },
    { title: 'Features', subtitle: 'Creates training vectors', icon: Network },
    { title: 'Random Forest', subtitle: 'Learns decision patterns', icon: BrainCircuit, highlight: true },
    { title: 'EV Model', subtitle: 'Scores each action', icon: Gauge },
    { title: 'MLAgent', subtitle: 'Chooses best score', icon: Sparkles },
  ]

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Visual Map</CardTitle>
        <CardDescription>
          One loop: create examples, train the model, send the trained model back into the game.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-xl border border-white/10 bg-zinc-950 p-4 md:p-5">
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr]">
            <MiniPhase {...phases[0]} />
            <Connector />
            <MiniPhase {...phases[1]} />
            <Connector />
            <MiniPhase {...phases[2]} />
            <Connector />
            <MiniPhase {...phases[3]} />
          </div>

          <div className="my-4 flex items-center justify-center text-zinc-500">
            <ArrowRight className="hidden rotate-90 md:block" size={22} />
          </div>

          <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr]">
            <MiniPhase {...phases[4]} />
            <Connector />
            <MiniPhase {...phases[5]} />
            <Connector />
            <MiniPhase {...phases[6]} />
          </div>

          <div className="mt-4 rounded-lg border border-dashed border-white/20 bg-black p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-white text-black">
                  <RotateCcw size={17} />
                </div>
                <div>
                  <h3 className="text-sm font-medium">The feedback loop</h3>
                  <p className="mt-1 text-xs leading-relaxed text-zinc-500">
                    Once the Random Forest becomes an EV model, the MLAgent can play in the same simulator.
                    That creates more decisions to analyze, compare, and improve.
                  </p>
                </div>
              </div>
              <div className="rounded-md bg-white px-3 py-2 text-xs font-medium text-black">
                MLAgent goes back to Simulator
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function StepCard({
  step,
  index,
}: {
  step: {
    title: string
    body: string
    icon: LucideIcon
    highlight?: boolean
  }
  index: number
}) {
  const Icon = step.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.025 }}
      className={[
        'rounded-lg border p-4',
        step.highlight ? 'border-white bg-white text-black' : 'border-white/10 bg-zinc-950 text-white',
      ].join(' ')}
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <div
          className={[
            'flex h-9 w-9 items-center justify-center rounded-md',
            step.highlight ? 'bg-black text-white' : 'bg-white text-black',
          ].join(' ')}
        >
          <Icon size={17} />
        </div>
        <span className={step.highlight ? 'text-xs font-semibold text-zinc-700' : 'text-xs font-semibold text-zinc-500'}>
          Step {index + 1}
        </span>
      </div>
      <h3 className="text-sm font-semibold">{step.title}</h3>
      <p className={step.highlight ? 'mt-2 text-xs leading-relaxed text-zinc-700' : 'mt-2 text-xs leading-relaxed text-zinc-500'}>
        {step.body}
      </p>
    </motion.div>
  )
}

function MiniPhase({
  title,
  subtitle,
  icon: Icon,
  highlight,
}: {
  title: string
  subtitle: string
  icon: LucideIcon
  highlight?: boolean
}) {
  return (
    <div
      className={[
        'rounded-lg border p-4',
        highlight ? 'border-white bg-white text-black' : 'border-white/10 bg-black text-white',
      ].join(' ')}
    >
      <div
        className={[
          'mb-3 flex h-9 w-9 items-center justify-center rounded-md',
          highlight ? 'bg-black text-white' : 'bg-white text-black',
        ].join(' ')}
      >
        <Icon size={17} />
      </div>
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className={highlight ? 'mt-1 text-xs text-zinc-700' : 'mt-1 text-xs text-zinc-500'}>{subtitle}</p>
    </div>
  )
}

function Connector() {
  return (
    <div className="flex items-center justify-center text-zinc-500">
      <ArrowRight className="hidden lg:block" size={22} />
      <ArrowRight className="rotate-90 lg:hidden" size={22} />
    </div>
  )
}

function ScoreRow({
  action,
  score,
  winner,
}: {
  action: string
  score: string
  winner?: boolean
}) {
  return (
    <div className={['flex items-center justify-between rounded-md border px-3 py-2', winner ? 'border-black bg-black text-white' : 'border-zinc-200 bg-zinc-50 text-black'].join(' ')}>
      <span className="font-medium">{action}</span>
      <span>{score}</span>
    </div>
  )
}
