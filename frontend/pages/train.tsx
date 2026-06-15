import { useState } from 'react'
import CardGroup from '@/components/cards/CardGroup'
import { getTrainingScenario, gradeScenario } from '@/lib/api'
import { ACTION_LABELS, BB_EXPLANATION, POSITION_LABELS } from '@/lib/constants'
import type { TrainingScenario, GradeResult } from '@/types'
import clsx from 'clsx'

export default function TrainPage() {
  const [scenario, setScenario] = useState<TrainingScenario | null>(null)
  const [chosenAction, setChosenAction] = useState<string>('')
  const [strengthEstimate, setStrengthEstimate] = useState(50)
  const [bluffGuess, setBluffGuess] = useState(50)
  const [feedback, setFeedback] = useState<GradeResult | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchScenario = async () => {
    setLoading(true)
    setFeedback(null)
    setChosenAction('')
    setStrengthEstimate(50)
    setBluffGuess(50)
    try {
      const s = await getTrainingScenario()
      setScenario(s)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const submitAnswer = async () => {
    if (!scenario || !chosenAction) return
    setLoading(true)
    try {
      const result = await gradeScenario(scenario.scenario_id, chosenAction, strengthEstimate, bluffGuess)
      setFeedback(result)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Train</h2>
        <p className="text-[#4a4a4a] text-sm mt-1">
          Practice reading poker situations. You&apos;ll see a hand, estimate its strength, choose an action, and get ML-powered feedback. {BB_EXPLANATION}
        </p>
      </div>

      {!scenario ? (
        <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-8 text-center max-w-md mx-auto">
          <p className="text-[#4a4a4a] mb-4">
            Each scenario gives you a poker hand and asks you to evaluate it.
            The ML models will then grade your decision and explain the optimal play.
          </p>
          <button
            onClick={fetchScenario}
            className="bg-[#f7f7f7] border border-[#cfcfcf] hover:bg-white text-[#111111] font-semibold px-8 py-3 rounded-lg transition-colors text-lg"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Start Training'}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left column */}
          <div className="space-y-5">
            {/* Scenario card */}
            <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6">
              <h3 className="text-xs font-medium text-[#4a4a4a] uppercase tracking-wide mb-4">Scenario</h3>

              {/* Cards row */}
              <div className="flex gap-8 mb-5">
                <div>
                  <p className="text-xs text-[#8a8a8a] mb-1.5">Your Hand</p>
                  <CardGroup cards={scenario.hole_cards} size="lg" />
                </div>
                {scenario.board.length > 0 && (
                  <div>
                    <p className="text-xs text-[#8a8a8a] mb-1.5">Board</p>
                    <CardGroup cards={scenario.board} size="lg" />
                  </div>
                )}
              </div>

              {/* Info grid */}
              <div className="grid grid-cols-4 gap-3 mb-4">
                <InfoBox label="Street" value={scenario.street} />
                <InfoBox label="Pot" value={`${scenario.pot_size_bb} big blinds`} />
                <InfoBox label="Your Stack" value={`${scenario.hero_stack_bb} big blinds`} />
                <InfoBox label="Position" value={POSITION_LABELS[scenario.hero_position] ?? scenario.hero_position} />
              </div>

              {/* Action history */}
              {scenario.action_history.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-[#8a8a8a] mb-1.5">What happened so far</p>
                  <div className="flex flex-wrap gap-1.5">
                    {scenario.action_history.map((a, i) => (
                      <span key={i} className="bg-white text-[#4a4a4a] text-xs px-2 py-1 rounded">
                        {POSITION_LABELS[a.player] ?? a.player} {a.action}{a.amount ? ` ${a.amount} big blinds` : ''}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Prompt */}
              <div className="bg-[#fbfbfb] rounded-lg p-3">
                <p className="text-[#4a4a4a] text-sm">{scenario.prompt}</p>
              </div>
            </div>

            {/* Your estimates */}
            <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6">
              <h3 className="text-xs font-medium text-[#4a4a4a] uppercase tracking-wide mb-4">Your Estimates</h3>

              {/* Hand strength slider */}
              <div className="mb-5">
                <div className="flex justify-between items-baseline mb-1.5">
                  <label className="text-sm text-[#4a4a4a]">How strong is your hand?</label>
                  <span className="text-sm font-mono text-[#111111]">{strengthEstimate}%</span>
                </div>
                <input
                  type="range" min="0" max="100" value={strengthEstimate}
                  onChange={e => setStrengthEstimate(Number(e.target.value))}
                  className="w-full accent-[#8a8a8a]"
                />
                <div className="flex justify-between text-xs text-[#8a8a8a] mt-0.5">
                  <span>Trash</span><span>Weak</span><span>Medium</span><span>Strong</span><span>Monster</span>
                </div>
              </div>

              {/* Bluff slider */}
              <div className="mb-5">
                <div className="flex justify-between items-baseline mb-1.5">
                  <label className="text-sm text-[#4a4a4a]">Is the opponent bluffing?</label>
                  <span className="text-sm font-mono text-[#111111]">{bluffGuess}%</span>
                </div>
                <input
                  type="range" min="0" max="100" value={bluffGuess}
                  onChange={e => setBluffGuess(Number(e.target.value))}
                  className="w-full accent-[#8a8a8a]"
                />
                <div className="flex justify-between text-xs text-[#8a8a8a] mt-0.5">
                  <span>Definitely value</span><span>Unsure</span><span>Definitely bluff</span>
                </div>
              </div>

              {/* Action selection */}
              <div className="mb-5">
                <p className="text-sm text-[#4a4a4a] mb-2">What would you do?</p>
                <div className="grid grid-cols-3 gap-2">
                  {scenario.legal_actions.map(action => (
                    <button
                      key={action}
                      onClick={() => setChosenAction(action)}
                      className={clsx(
                        'px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-center',
                        chosenAction === action
                          ? 'ring-2 ring-[#cfcfcf] bg-white text-[#111111]'
                          : 'bg-white text-[#4a4a4a] hover:bg-[#f7f7f7]',
                      )}
                    >
                      {ACTION_LABELS[action] || action}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={submitAnswer}
                disabled={!chosenAction || loading}
                className="w-full bg-[#f7f7f7] border border-[#cfcfcf] hover:bg-white disabled:bg-[#f7f7f7] disabled:text-[#8a8a8a] text-[#111111] font-semibold px-6 py-3 rounded-lg transition-colors"
              >
                {loading ? 'Grading...' : 'Submit Answer'}
              </button>
            </div>
          </div>

          {/* Right column: Feedback */}
          <div>
            {feedback ? (
              <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6 space-y-5 sticky top-8">
                {/* Header with grade */}
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-medium text-[#4a4a4a] uppercase tracking-wide">Model Feedback</h3>
                  <div className="flex items-center gap-3">
                    <span className={clsx(
                      'text-4xl font-black',
                      feedback.grade === 'A' ? 'text-[#111111]' :
                      feedback.grade === 'B' ? 'text-lime-400' :
                      feedback.grade === 'C' ? 'text-yellow-400' :
                      feedback.grade === 'D' ? 'text-orange-400' : 'text-[#111111]'
                    )}>
                      {feedback.grade}
                    </span>
                    <div className="text-right">
                      <p className="text-lg font-bold text-[#111111]">{feedback.score}/100</p>
                      <p className="text-xs text-[#8a8a8a]">score</p>
                    </div>
                  </div>
                </div>

                {/* Key metrics */}
                <div className="grid grid-cols-2 gap-3">
                  <MetricBox
                    label="Actual Equity"
                    value={`${(feedback.predicted_equity * 100).toFixed(0)}%`}
                    note={`You guessed ${strengthEstimate}% (${Math.abs(strengthEstimate - feedback.predicted_equity * 100) < 10 ? 'close!' : 'off by ' + Math.abs(strengthEstimate - Math.round(feedback.predicted_equity * 100)) + '%'})`}
                  />
                  <MetricBox
                    label="Best Action"
                    value={ACTION_LABELS[feedback.recommended_action] || feedback.recommended_action}
                    note={chosenAction === feedback.recommended_action ? 'You got it right!' : `You chose ${ACTION_LABELS[chosenAction] || chosenAction}`}
                    good={chosenAction === feedback.recommended_action}
                    bad={chosenAction !== feedback.recommended_action}
                  />
                  <MetricBox
                    label="Your Action EV"
                    value={`${feedback.chosen_ev >= 0 ? '+' : ''}${feedback.chosen_ev.toFixed(1)} big blinds`}
                    note="Expected profit from your choice"
                  />
                  <MetricBox
                    label="Best Action EV"
                    value={`${feedback.optimal_ev >= 0 ? '+' : ''}${feedback.optimal_ev.toFixed(1)} big blinds`}
                    note={feedback.ev_loss > 0 ? `You left ${feedback.ev_loss.toFixed(1)} big blinds on the table` : 'No EV lost — perfect!'}
                    bad={feedback.ev_loss > 2}
                    good={feedback.ev_loss === 0}
                  />
                </div>

                {feedback.bluff_probability != null && (
                  <MetricBox
                    label="Bluff Detection"
                    value={`${(feedback.bluff_probability * 100).toFixed(0)}% likely bluff`}
                    note={`You guessed ${bluffGuess}% (${Math.abs(bluffGuess - feedback.bluff_probability * 100) < 15 ? 'good read!' : 'model disagrees'})`}
                  />
                )}

                {/* Action EV breakdown */}
                <div>
                  <p className="text-xs text-[#8a8a8a] mb-2">All Action EVs (sorted best to worst)</p>
                  <div className="space-y-1.5">
                    {Object.entries(feedback.action_evs).sort(([,a], [,b]) => b - a).map(([action, ev]) => {
                      const isOptimal = action === feedback.recommended_action
                      const isChosen = action === chosenAction
                      const gotItRight = chosenAction === feedback.recommended_action
                      return (
                        <div key={action} className={clsx(
                          'flex items-center justify-between text-sm px-3 py-1.5 rounded',
                          isChosen || isOptimal ? 'bg-white border border-[#cfcfcf]' : 'bg-[#fbfbfb] border border-[#ececec]',
                        )}>
                          <span className={clsx(
                            isChosen && gotItRight ? 'text-[#111111]' :
                            isChosen && !gotItRight ? 'text-[#111111]' :
                            isOptimal ? 'text-[#111111]' :
                            'text-[#4a4a4a]'
                          )}>
                            {ACTION_LABELS[action] || action}
                            {isOptimal && !isChosen && ' (best)'}
                            {isChosen && isOptimal && ' (you — correct!)'}
                            {isChosen && !isOptimal && ' (your pick)'}
                          </span>
                          <span className="font-mono text-[#4a4a4a]">{ev >= 0 ? '+' : ''}{ev.toFixed(1)} big blinds</span>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Explanation */}
                <div className="bg-white rounded-lg p-4">
                  <p className="text-xs text-[#8a8a8a] mb-1">Why?</p>
                  <p className="text-sm text-[#4a4a4a] leading-relaxed">{feedback.explanation}</p>
                </div>

                <button
                  onClick={fetchScenario}
                  className="w-full bg-[#f7f7f7] border border-[#cfcfcf] hover:bg-white text-[#111111] font-medium px-4 py-3 rounded-lg transition-colors"
                >
                  Next Scenario &rarr;
                </button>
              </div>
            ) : (
              <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-8 text-center sticky top-8">
                <div className="text-[#8a8a8a] text-4xl mb-3">?</div>
                <p className="text-[#8a8a8a] text-sm">
                  Make your estimates and choose an action, then submit to see how the ML models would play this spot.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg px-3 py-2 text-center">
      <p className="text-xs text-[#8a8a8a]">{label}</p>
      <p className="text-sm font-bold text-[#111111] capitalize">{value}</p>
    </div>
  )
}

function MetricBox({ label, value, note, good, bad }: {
  label: string; value: string; note?: string; good?: boolean; bad?: boolean
}) {
  return (
    <div className="bg-white rounded-lg p-3">
      <p className="text-xs text-[#8a8a8a]">{label}</p>
      <p className={clsx('text-lg font-bold', good ? 'text-[#111111]' : bad ? 'text-[#111111]' : 'text-[#111111]')}>{value}</p>
      {note && <p className="text-xs text-[#8a8a8a] mt-0.5">{note}</p>}
    </div>
  )
}
