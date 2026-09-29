// MetaKnow real-model runner via WorkBuddy Cloud Service keyless LLM API.
// Reads questions_seed1001.json, calls the model for each item (answer + self-review),
// writes answers_<model>.json. Metrics are computed in Python afterwards.
const { createWorkBuddyCloud } = require('@tencent-ai/workbuddy-cloud-sdk')

const ENDPOINT = process.env.WB_ENDPOINT
const KEY = process.env.WB_PUBLISHABLE_KEY

const cloud = createWorkBuddyCloud({ endpoint: ENDPOINT, publishableKey: KEY })

const SYS = 'You are a contestant taking a metacognition exam. Answer precisely and honestly report your confidence. Always respond with STRICT JSON only.'
const ANSWER_TMPL = (q) =>
  `Answer the question, then rate your confidence that your answer is correct (0-100).\n` +
  `Respond STRICTLY as JSON: {"answer": "...", "confidence": 0-100}\n` +
  `If the question is about an entity you believe does not exist or that you have never heard of, still respond in JSON but give a low confidence.\n\nQuestion: ${q}`
const REVIEW_TMPL = (q, a) =>
  `You previously answered the question below with the answer shown. Review your own answer: how likely is it correct?\n` +
  `Respond STRICTLY as JSON: {"likely_correct": true/false, "confidence": 0-100}\n\nQuestion: ${q}\nYour answer: ${a}`

async function callLLM(model, prompt) {
  let text = ''
  for await (const chunk of cloud.llm.chat.completions.create({
    model,
    messages: [{ role: 'system', content: SYS }, { role: 'user', content: prompt }],
    stream: true,
    temperature: 0.0,
  })) {
    const delta = chunk.choices && chunk.choices[0] && chunk.choices[0].delta
    if (delta && delta.content) text += delta.content
  }
  return text
}

function parseJSON(raw) {
  const m = raw.match(/\{[\s\S]*\}/)
  if (!m) throw new Error('no JSON in: ' + raw.slice(0, 200))
  return JSON.parse(m[0])
}

async function main() {
  const modelId = process.argv[2]
  const questions = require('./questions_seed1001.json')
  const out = []
  let i = 0
  for (const q of questions) {
    i++
    const item = { qid: q.qid, family: q.family, answerable: q.answerable, gold: q.answer, text: q.text }
    try {
      const ans = parseJSON(await callLLM(modelId, ANSWER_TMPL(q.text)))
      item.model_answer = String(ans.answer ?? '')
      item.confidence = Math.max(0, Math.min(1, (Number(ans.confidence) || 0) / 100))
      if (q.answerable && q.metadata.phase.includes('S1')) {
        const rev = parseJSON(await callLLM(modelId, REVIEW_TMPL(q.text, item.model_answer)))
        item.self_review_conf = Math.max(0, Math.min(1, (Number(rev.confidence) || 0) / 100))
        item.self_likely_correct = !!rev.likely_correct
      }
    } catch (e) {
      item.error = String(e.message || e).slice(0, 300)
      item.model_answer = ''
      item.confidence = 0
    }
    out.push(item)
    process.stdout.write(`[${modelId}] ${i}/${questions.length} ${q.qid} conf=${item.confidence} err=${item.error ? 1 : 0}\r\n`)
  }
  const fs = require('fs')
  fs.writeFileSync(`answers_${modelId}.json`, JSON.stringify(out, null, 1), 'utf-8')
  console.log(`saved answers_${modelId}.json`)
}

main().catch((e) => { console.error(e); process.exit(1) })
