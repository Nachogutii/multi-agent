import { supabase } from "../lib/supabaseClient"

export async function submitFeedbackToSupabase(feedback) {
  console.log('🔍 Iniciando submitFeedbackToSupabase...')
  console.log('📦 Feedback recibido:', feedback)

  // Verificar si ya se envió feedback para esta sesión
  const feedbackKey = `feedback_sent_${feedback.sessionId}`
  const alreadySent = localStorage.getItem(feedbackKey)
  
  console.log('🔑 Clave de feedback:', feedbackKey)
  console.log('📝 Estado de envío previo:', alreadySent)
  
  if (alreadySent) {
    console.log('⚠️ Feedback ya fue enviado anteriormente para esta sesión')
    return
  }

  console.log('🔄 Obteniendo usuario de Supabase...')
  const { data: { user } } = await supabase.auth.getUser()
  const rawEnv = process.env.REACT_APP_ENV
  const environment = rawEnv && rawEnv.toLowerCase() === 'development' ? 'dev' : 'prod'
  

  console.log('👤 Usuario:', user?.email)
  console.log('🌍 Ambiente:', environment)

  console.log('📤 Enviando feedback a Supabase...')
  const { error } = await supabase.from('feedback').insert([
    {
      user_id: user?.email || null,
      environment,
      metrics: feedback.metrics,
      suggestions: feedback.suggestions,
      issues: feedback.issues
    },
  ])

  if (error) {
    console.error('❌ Error al enviar feedback:', error)
  } else {
    console.log('✅ Feedback enviado exitosamente a Supabase')
    // Marcar que el feedback ya fue enviado para esta sesión
    localStorage.setItem(feedbackKey, 'true')
    console.log('📝 Feedback marcado como enviado en localStorage')
  }
} 