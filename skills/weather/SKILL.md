---
name: weather
description: Validates a requested location, fetches current weather conditions and temperature using the weather tools, and presents the result in a clear, human-friendly summary. Use when the user asks about the weather, forecast, conditions, or temperature for a city.
---

# Weather Skill

## 1. Validate Input First (Required)

**Before calling any tool, validate the user's request:**

1. **City is present and specific:** Confirm the user named a real city (e.g., `Madrid`, `Tokyo`, `New York`).
2. **Handle missing or invalid input:** If the city is missing, vague (e.g., `"here"`, `"outside"`, `"my location"`), or not a recognizable place, **do NOT call any tool**. Instead, politely ask the user to specify a city name.
3. **Normalize temperature unit (optional):**
   - Default to `"celsius"` if the user does not specify a unit.
   - Accept `"celsius"` (`C`, `°C`) or `"fahrenheit"` (`F`, `°F`).
   - If the user asks for an unsupported unit (e.g., Kelvin), let them know you support Celsius and Fahrenheit and ask which they prefer (or report in Celsius).

## 2. Fetch Weather Data (Required)

Once the input is valid, use the available tools instead of guessing or relying on prior knowledge:

1. **Always call `get_weather`** with the validated city name:

```
get_weather(city="Madrid")
```

2. **Call `get_temperature`** when the user asks for temperature or a full weather report:

```
get_temperature(city="Madrid", unit="celsius")
```

**Rules:**
- Never invent or estimate weather conditions or temperatures.
- If a tool returns an error or empty response, apologize briefly and let the user know the weather data could not be retrieved right now.

## 3. Present the Result (Human-Friendly Format)

Turn the raw tool output into a concise, natural, and easy-to-read response:

- **Lead with the city and key takeaway** in plain, conversational language.
- **Include both conditions and temperature** (with `°C` or `°F`) when both were fetched.
- **Keep it scannable**—use a short paragraph or a compact bullet list, not raw tool output.
- **Add a brief, practical note** when helpful (e.g., whether it's pleasant for being outside).

### Examples

**Valid request:** *"What's the weather like in Madrid?"*

Tool calls:
```
get_weather(city="Madrid")
get_temperature(city="Madrid", unit="celsius")
```

Human-friendly response:
> **Madrid Weather**
> - **Conditions:** Clear and mild
> - **Temperature:** 14°C
>
> It's a pleasant, mild day in Madrid—great weather for being outdoors, though a light jacket may be comfortable.

**Invalid/missing input:** *"What's the weather right now?"*

No tool calls. Response:
> Which city would you like me to check the weather for?

## Quality Checklist

Before finishing:
- [ ] Confirmed a valid, specific city was provided before calling tools
- [ ] Called `get_weather` (and `get_temperature` when relevant) instead of guessing
- [ ] Normalized temperature unit to `celsius` or `fahrenheit`
- [ ] Presented the result in a warm, clear, human-friendly format without dumping raw tool strings
