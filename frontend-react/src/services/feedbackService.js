import { supabase } from "../lib/supabaseClient"

export async function submitFeedbackToSupabase(feedback) {
  const { data: { user } } = await supabase.auth.getUser()
  const environment = process.env.NODE_ENV === 'development' ? 'dev' : 'prod'

  const { error } = await supabase.from('feedback').insert([
    {
      user_id: user?.email || null,
      environment,
      metrics: feedback.metrics,
      suggestions: feedback.suggestions,
      issues: feedback.issues,
    },
  ])

  if (error) {
    console.error('❌ Error submitting feedback:', error)
  } else {
    console.log('✅ Feedback submitted to Supabase')
  }
} 