import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import Anthropic from '@anthropic-ai/sdk'

dotenv.config({ path: '../.env' })

const app = express()
app.use(cors())
app.use(express.json())

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

const SYSTEM_PROMPT = `You are Vicki, a billing support specialist at a healthcare clinic. Your job is to write clear, honest, plain-English email responses that explain to patients why they owe what they owe on their medical bills.

Your tone is professional but warm. Knowledgeable but never corporate or cold. Think of the billing rep at a clinic people actually trust.

Rules you must follow:
- Never use em dashes or en dashes. Use commas or new sentences instead.
- Use no more than one exclamation point in the entire response.
- Do not use the words: straightforward, delve, boundaries, comprehensive, crucial.
- The why_you_owe field must always include specific dollar amounts and the exact reason for the balance. Never vague or generic.
- Always route deductible balance questions to the insurer. The clinic does not have access to a patient's remaining deductible.
- Use the patient's first name once, only in the greeting field.
- Respond only with raw JSON. No markdown fences. No text outside the JSON object.

Output format (raw JSON only):
{
  "greeting": "string",
  "why_you_owe": "string",
  "what_this_means": "string",
  "next_steps": "string",
  "signoff": "string"
}`

app.post('/api/generate', async (req, res) => {
  const { patient } = req.body

  if (!patient || !patient.claim) {
    return res.status(400).json({ error: 'Missing patient data' })
  }

  const { claim, firstName, scenario } = patient

  const userMessage = `Generate a Vicki billing response for this patient.

Patient first name: ${firstName}
Scenario type: ${scenario}
Carrier: ${claim.carrier}
Plan: ${claim.plan}
Service: ${claim.service}
Date of service: ${claim.date}
Amount billed: $${claim.amountBilled}
Allowed amount: $${claim.allowedAmount}
Insurance paid: $${claim.insurancePaid}
Patient owes: $${claim.patientOwes}
Patient's question: ${patient.email}

Respond with a JSON object only. No markdown. No extra text.`

  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: userMessage }],
    })

    const raw = message.content[0].text.trim()
    const parsed = JSON.parse(raw)
    res.json(parsed)
  } catch (err) {
    if (err instanceof SyntaxError) {
      return res.status(500).json({ error: 'Failed to parse API response as JSON' })
    }
    console.error(err)
    res.status(500).json({ error: err.message || 'Internal server error' })
  }
})

const PORT = process.env.PORT || 3001
app.listen(PORT, () => {
  console.log(`Vicki API server running on port ${PORT}`)
})
