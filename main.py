from dotenv import load_dotenv
load_dotenv()
import os
import streamlit as st
import google.generativeai as genai
from PIL import Image

#api_key =st.sidebar.text_input("Please enter your Google API Key in the",key="password",type="password")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input,image,prompt) -> str:
   model=genai.GenerativeModel("gemini-2.5-flash")
   response = model.generate_content([input,image[0],prompt])
   return response.text
   
def input_image(uploaded_file):
    if uploaded_file is not None:
        byte_data = uploaded_file.getvalue()
        image_parts =[{
            "mime_type": uploaded_file.type,    
            "data": byte_data
        }]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")
    
st.title("Nutrition Agent")
st.write("Upload an image of your meal and ask any nutrition-related questions!")
input_text = st.text_input("Input:",key="input_text")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
image =""
if uploaded_file is not None:
    
    st.image(Image.open(uploaded_file), caption='Uploaded Image.', width=200)

submit =st.button("Get Nutrition Info")

input_prompt = """You are an expert nutritionist. Analyze the food items in the image and give the output in a clear, structured, and detailed format.

For each food item, provide the following fields in order:

- Item
- Calories (number only)
- Portion (describe size clearly)
- Macronutrients:
     Carbs_g
     Protein_g
     Fat_g
- Category (e.g., vegetable, grain, dairy, meat, seafood, fruit, snack)
- Health_Risk_Flags (if any)
- Interesting facts (1–2 detailed sentences about nutrition, benefits, or concerns)

After listing all items, provide:

- TOTAL_CALORIES (sum of all items, number only)
- Suggestion (2–3 detailed interesting sentences about overall meal quality)
- OVERALL_MODEL_CONFIDENCE (0–100)

Format your output EXACTLY like this:

1. <name>
   * Calories: <number>
   * Portion: <text>
   * Carbs_g: <number>
   * Protein_g: <number>
   * Fat_g: <number>
   * Category: <text>
   * Health_Risk_Flags: <text or none>
   * Interesting facts: <detailed text>

2. <name>
   * Calories: <number>
   * Portion: <text>
   * Carbs_g: <number>
   * Protein_g: <number>
   * Fat_g: <number>
   * Category: <text>
   * Health_Risk_Flags: <text or none>
   * Interesting facts: <detailed text>

TOTAL_CALORIES: <number>
TOTAL_Protien_g: <number>
TOTAL_Carbs_g: <number>
TOTAL_Fat_g: <number>

Suggestion :<detailed text keep short and precise>

OVERALL_MODEL_CONFIDENCE: <0–100>
"""
if submit:
    try:
        if uploaded_file:
            with st.spinner('Getting response from Gemini...'):
                image = input_image(uploaded_file)
                response = get_gemini_response(input_text,image,input_prompt)
                st.subheader("The Response is")
                st.write(response)
    except FileNotFoundError as e:
        st.error(e)

# def main():
#     print("Hello from nutrition-agent!")


# if __name__ == "__main__":
#     main()
