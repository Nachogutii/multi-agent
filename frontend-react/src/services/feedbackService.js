import { supabase } from "../lib/supabaseClient"

export async function submitFeedbackToSupabase(feedback) {
  console.log('🔍 Iniciando submitFeedbackToSupabase...')
  const feedbackKey = `feedback_sent_${feedback.sessionId}`
  const alreadySent = localStorage.getItem(feedbackKey)
  const vAccount = localStorage.getItem("v_account") || null

  if (alreadySent) {
    console.log('⚠️ Feedback ya fue enviado anteriormente para esta sesión')
    return null
  }

  const { data: { user } } = await supabase.auth.getUser()
  const rawEnv = process.env.REACT_APP_ENV
  const isDev = rawEnv && rawEnv.toLowerCase() === 'development'
  const tableName = isDev ? 'feedback_dev' : 'feedback_prod'

  const { data, error } = await supabase.from(tableName).insert([
    {
      user_id: user?.email || null,
      v_account: vAccount,
      metrics: feedback.metrics,
      suggestions: feedback.suggestions,
      issues: feedback.issues,
    },
  ]).select('id') // 👈 para obtener el ID del feedback insertado

  if (error || !data?.length) {
    console.error('❌ Error al enviar feedback:', error)
    return null
  }

  const feedbackId = data[0].id
  localStorage.setItem(feedbackKey, 'true')
  return feedbackId
}
