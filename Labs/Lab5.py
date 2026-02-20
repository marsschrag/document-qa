import streamlit as st
import requests
import json
from openai import OpenAI

#api key calls
ow_api_key = st.secrets["openweather_api_key"]
openai_api_key = st.secrets["OPENAI_API_KEY"]

#current weather function
def get_current_weather(location, ow_api_key, units='fahrenheit'):
    url = (
        f'https://api.openweathermap.org/data/2.5/weather'
        f'?q={location}&appid={ow_api_key}&units={units}'
        )
    response = requests.get(url)
    if response.status_code == 401:
        raise Exception('authentication failed, invalid API key (401 unauthorized)')
    if response.status_code == 404:
        error_message = response.json().get('message')
        raise Exception(f'404 error: {error_message}')
    data = response.json()
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    humidity = data['main']['humidity']
    return {'location': location,
            'temperature': round(temp, 2),
            'feels_like': round(feels_like, 2),
            'temp_min': round(temp_min, 2),
            'temp_max': round(temp_max, 2),
            'humidity': round(humidity, 2)
            }

#toolbox
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state, e.g. 'Boston, MA' or 'London, UK'.",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units. Determine from the forecast location.",
                    },
                },
                "required": ["location", "format"],
            },
        },
    }
]

def get_advice(city_input: str, units: str = "fahrenheit") -> tuple[str, dict | None]:
    user_msg = (
        f"What is the weather like in {city_input}? "
        "Based on that, what clothes should I wear today and what outdoor "
        "activities would be appropriate?"
    ) if city_input.strip() else (
        "What is the weather like right now? "
        "Based on that, what clothes should I wear today and what outdoor "
        "activities would be appropriate?"
    )

    messages = [
        {
            "role": "system",
            "content": (
                "When asked about weather, use the get_current_weather tool. If no city is given, default to Syracuse, NY. "
                "After retrieving weather data, give advice on clothing to wear and suitable outdoor activities."
            ),
        },
        {"role": "user", "content": user_msg},
    ]

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    msg = response.choices[0].message
    weather_data = None

    if msg.tool_calls:
        tool_call = msg.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        location = args.get("location") or "Syracuse, NY"
        units_arg = args.get("units", units)

        try:
            weather_data = get_current_weather(location, units_arg)
        except Exception as e:
            return f"Could not fetch weather: {e}", None

        w = weather_data
        weather_summary = (
            f"Location: {w['location']}\n"
            f"Condition: {w['description']}\n"
            f"Temperature: {w['temperature']}{w['unit_symbol']} "
            f"(feels like {w['feels_like']}{w['unit_symbol']})\n"
            f"High / Low: {w['temp_max']}{w['unit_symbol']} / {w['temp_min']}{w['unit_symbol']}\n"
            f"Humidity: {w['humidity']}%\n"
        )

        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": weather_summary,
        })

        messages.append({
            "role": "user",
            "content": (
                "Given the weather information above, please suggest what clothes to wear today and recommend outdoor activities suitable for these conditions."
            ),
        })

        second_response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
        )
        advice = second_response.choices[0].message.content
    else:
        advice = msg.content

    return advice, weather_data

st.title("Weather Advice Bot")

st.caption("Enter a city and get personalized clothing & activity suggestions")

city  = st.text_input("City", placeholder="e.g. Chicago, IL  (leave blank for Syracuse, NY)")
units = st.radio("Units", ["celsius, fahrenheit"],
                 format_func=lambda u: "celsius (°C)" if u == "celsius" else "fahrenheit (°F)",
                 horizontal=True)

if st.button("Get Advice"):
    with st.spinner("Checking the weather and thinking…"):
        try:
            advice, weather = get_advice(city, units)

            if weather:
                w = weather
                st.subheader(f"📍 {w['location']}  —  {w['description']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Temp",      f"{w['temperature']}{w['unit_symbol']}")
                c1.metric("Feels Like",f"{w['feels_like']}{w['unit_symbol']}")
                c2.metric("High / Low",f"{w['temp_max']} / {w['temp_min']}{w['unit_symbol']}")
                c2.metric("Humidity",  f"{w['humidity']}%")
                st.divider()

            st.subheader("AI Advice")
            st.markdown(advice)

        except Exception as e:
            st.error(str(e))