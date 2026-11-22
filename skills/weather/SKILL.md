---
name: weather
description: Mandatory workflow for all weather, forecast, conditions, and temperature requests. Read this skill before calling weather tools to validate locations, normalize units, fetch both conditions and temperature, and format responses.
---

# Weather Skill

## 1. Validate Input First (Required)

**Before calling any tool, validate the user's request:**

1. **City is present and specific:** Confirm the user named a specific city or place (e.g., `Madrid`, `Tokyo`, `New York`).
2. **Handle missing or vague input:** If the city is missing or vague (e.g., `"here"`, `"outside"`, `"my location"`), **do NOT call any tool**. Instead, politely ask the user to specify a city name. If the user provides a specific place name, let the weather tools verify whether it exists rather than guessing.
3. **Normalize temperature unit (optional):**
   - Default to `"celsius"` if the user does not specify a unit.
   - Accept `"celsius"` (`C`, `°C`) or `"fahrenheit"` (`F`, `°F`).
   - If the user asks for an unsupported unit (e.g., Kelvin), **do NOT manually convert** the temperature, **do NOT output a Kelvin value or conversion formula (such as `+ 273.15`)**, and **never mention internal tool/function names (such as `get_temperature`)**. Explicitly tell the user that you only support **Celsius** and **Fahrenheit**, and either ask which they prefer or provide the temperature in Celsius.

## 2. Fetch Weather Data (Required)

Once the input is valid, use the available tools instead of guessing or relying on prior knowledge:

1. **Always call both `get_weather` and `get_temperature` together in parallel** for general weather queries (e.g., *"What is the weather like in Madrid?"*). Remember that `get_weather` only returns sky/humidity/wind and does **not** return temperature:

```
get_weather(city="Madrid")
get_temperature(city="Madrid", unit="celsius")
```

2. **Exceptions for narrow requests:**
   - If the user asks *only* a yes/no condition question (e.g., *"Is it raining in London?"*), calling `get_weather` alone is sufficient.
   - If the user asks *only* for the temperature (e.g., *"What is the temperature there in Fahrenheit?"*), calling `get_temperature` alone is sufficient.

**Rules:**
- Never invent or estimate weather conditions or temperatures.
- Never mention a temperature unless you called `get_temperature` and use the exact value returned by the tool.
- If a tool returns an error or empty response, apologize briefly and let the user know the weather data could not be retrieved right now.

## 3. Present the Result (Human-Friendly Format)

Turn the raw tool output into a concise, natural, and easy-to-read response:

- **Lead with the city and key takeaway** in plain, conversational language.
- **Include both conditions and temperature** (with `°C` or `°F`) when both were fetched.
- **Keep it scannable**—use a short paragraph or a compact bullet list, not raw tool output.
- **Add a brief, practical note** when helpful (e.g., whether it's pleasant for being outside).
- **Stay within scope:** Do not offer multi-day or future forecasts in closing follow-up questions (you only check current conditions and temperatures).

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
- [ ] Confirmed a specific city was provided (not missing or vague) before calling tools
- [ ] Called both `get_weather` and `get_temperature` for general weather queries instead of guessing
- [ ] Normalized temperature unit to `celsius` or `fahrenheit` (and did not manually convert unsupported units)
- [ ] Presented the result in a warm, clear, human-friendly format without dumping raw tool strings or offering out-of-scope forecasts
