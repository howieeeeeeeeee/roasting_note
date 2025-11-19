  GET /api/temp/current_fast (every 1 second)
  POST /api/roast/log_temp_local (every 1 second, only when roast running)
  GET /api/temp/current (every 5 seconds, only when roast running)
  POST /api/roast/add_event (every 5 seconds, only when roast running)

  analyze this, see how to achieve this efficiently and without too much lagging
