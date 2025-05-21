# Testing the Supabase Connection

This directory contains tests for the Supabase connection and the orchestrator integration.

## Prerequisites

Before running the tests, make sure you have:

1. Created a `.env` file in the `backend` directory with your Supabase credentials:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-api-key
   ```

2. Set up the database tables in Supabase as shown in the schema diagram.

3. Populated the database with sample data using the provided SQL files:
   - `red_flags_rows.sql`
   - `phases_rows.sql`
   - `conditions_rows.sql`
   - `phase_conditions_rows.sql`

## Running the Tests

To run the tests, execute:

```bash
cd multi-agent
python -m backend.app.tests.test_supabase
```

## Expected Output

If the connection and data retrieval are working correctly, you should see:

1. A confirmation of successful Supabase connection
2. A list of red flags retrieved from the database
3. A list of phases with their names
4. Detailed data for the "welcome" phase
5. A list of conditions associated with the welcome phase
6. Results from the orchestrator processing test messages

## Troubleshooting

If you encounter connection issues:

1. Verify your Supabase URL and API key in the `.env` file
2. Ensure your IP is allowed in Supabase settings
3. Check that the required tables exist and have the correct structure
4. Verify that the SQL queries in the service are compatible with your Supabase setup 