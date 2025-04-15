// src/services/submitConversationToSupabase.js
import { supabase } from "../lib/supabaseClient"

export async function submitConversationToSupabase(feedbackId, messages) {
  const rawEnv = process.env.REACT_APP_ENV
  const isDev = rawEnv && rawEnv.toLowerCase() === 'development'
  const tableName = isDev ? 'conversation_log_dev' : 'conversation_log'

  const { error } = await supabase.from(tableName).insert([
    {
      feedback_id: feedbackId,
      messages,
    },
  ])

  if (error) {
    console.error('❌ Error al guardar la conversación:', error)
  } else {
    console.log('✅ Conversación guardada con éxito')
  }
}
