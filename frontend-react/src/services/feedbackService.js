import { supabase } from "../lib/supabaseClient"

export async function getFeedbackFromSupabase(sessionId) {
  const rawEnv = process.env.REACT_APP_ENV
  const isDev = rawEnv && rawEnv.toLowerCase() === 'development'
  const tableName = isDev ? 'feedback_dev' : 'feedback_prod'

  const { data, error } = await supabase
    .from(tableName)
    .select('*')
    .eq('session_id', sessionId)
    .single();

  if (error) {
    console.log('No se encontró feedback existente para la sesión:', sessionId);
    return null;
  }

  return data;
}

export async function submitFeedbackToSupabase(feedback) {
  console.log('🔍 Iniciando submitFeedbackToSupabase...')
  const { sessionId } = feedback;
  
  // Primero verificamos si ya existe feedback para esta sesión
  const existingFeedback = await getFeedbackFromSupabase(sessionId);
  if (existingFeedback) {
    console.log(`✅ Feedback existente encontrado para la sesión ${sessionId}`);
    return existingFeedback.id;
  }

  const rawEnv = process.env.REACT_APP_ENV
  const isDev = rawEnv && rawEnv.toLowerCase() === 'development'
  const tableName = isDev ? 'feedback_dev' : 'feedback_prod'

  const { data: { user } } = await supabase.auth.getUser()
  const vAccount = localStorage.getItem("v_account") || null

  // Si no existe, creamos uno nuevo
  console.log(`Enviando nuevo feedback para la session_id: ${sessionId}`);
  const { data: insertedData, error: insertError } = await supabase.from(tableName).insert([
    {
      user_id: user?.email || null,
      v_account: vAccount,
      metrics: feedback.custom_score,
      suggestions: feedback.suggestions,
      issues: feedback.issues,
      strength: feedback.strength,
      session_id: sessionId
    },
  ]).select('id')

  if (insertError || !insertedData?.length) {
    console.error('❌ Error al enviar nuevo feedback:', insertError)
    return null
  }

  const newFeedbackId = insertedData[0].id;
  console.log(`✅ Nuevo feedback enviado con ID: ${newFeedbackId}`);
  return newFeedbackId;
}
