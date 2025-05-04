from google import genai

client = genai.Client(api_key="AIzaSyBTFbN8a9clizv4u1Us1wE_1o8kRsuJ24Y")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words plz korean"
)
print(response.text)