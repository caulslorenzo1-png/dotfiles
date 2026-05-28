import os
import requests
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 80: "Rain showers", 81: "Heavy rain showers", 95: "Thunderstorm",
}

def get_current_temperature(location: str) -> dict:
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
    ).json()
    if not geo.get("results"):
        return {"error": f"Location '{location}' not found"}
    r = geo["results"][0]
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "current": "temperature_2m,weathercode",
            "temperature_unit": "fahrenheit",
        },
    ).json()
    current = weather["current"]
    return {
        "location": r["name"],
        "temperature": f"{current['temperature_2m']}F",
        "condition": WMO_CODES.get(current["weathercode"], "Unknown"),
    }


weather_function = {
    "name": "get_current_temperature",
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
        },
        "required": ["location"],
    },
}

tools = types.Tool(function_declarations=[weather_function])
config = types.GenerateContentConfig(tools=[tools])

contents = ["What's the weather like in London, Tokyo, New York, Sydney, Paris, Dubai, Mumbai, São Paulo, Toronto, and Singapore right now?"]

while True:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=config,
    )

    candidate = response.candidates[0]
    function_calls = [p for p in candidate.content.parts if p.function_call]

    if not function_calls:
        print("Final Response:", response.text)
        break

    contents.append(candidate.content)

    fn_response_parts = []
    for part in function_calls:
        fc = part.function_call
        print(f"Calling {fc.name} with args {fc.args}")
        result = get_current_temperature(**fc.args)
        print(f"  -> {result}")
        fn_response_parts.append(types.Part.from_function_response(name=fc.name, response=result))

    contents.append(types.Content(role="user", parts=fn_response_parts))
