from dotenv import load_dotenv
load_dotenv()
import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime

#api_key =st.sidebar.text_input("Please enter your Google API Key in the",key="password",type="password")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize session state for tracking meals
if "meals" not in st.session_state:
    st.session_state.meals = []

# Initialize session state for nutrition targets
if "nutrition_targets" not in st.session_state:
    st.session_state.nutrition_targets = {
        "daily_calories": 2000,
        "daily_protein": 50,
        "daily_carbs": 300,
        "daily_fat": 65
    }
def get_gemini_response(input: str, image: list, prompt: str) -> str:
   model=genai.GenerativeModel("gemini-2.5-flash")
   response = model.generate_content([input,image[0],prompt])
   return response.text

def parse_nutrition_response(response_text: str) -> dict:
    """Parse Gemini's response to extract nutrition data"""
    try:
        lines = response_text.strip().split('\n')
        nutrition_data = {}
        items = []
        current_item = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line and line[0].isdigit() and '.' in line:  # Item number like "1. item_name"
                if current_item:
                    items.append(current_item)
                current_item = {"name": line.split('.', 1)[1].strip()}
            elif 'Calories:' in line:
                try:
                    cal_str = ''.join(filter(str.isdigit, line.split(':')[1]))
                    current_item['calories'] = int(cal_str) if cal_str else 0
                except:
                    current_item['calories'] = 0
            elif 'Portion:' in line:
                current_item['portion'] = line.split(':', 1)[1].strip()
            elif 'Carbs_g:' in line:
                try:
                    carbs_str = ''.join(c for c in line.split(':')[1] if c.isdigit() or c == '.')
                    current_item['carbs'] = float(carbs_str) if carbs_str else 0.0
                except:
                    current_item['carbs'] = 0.0
            elif 'Protein_g:' in line:
                try:
                    protein_str = ''.join(c for c in line.split(':')[1] if c.isdigit() or c == '.')
                    current_item['protein'] = float(protein_str) if protein_str else 0.0
                except:
                    current_item['protein'] = 0.0
            elif 'Fat_g:' in line:
                try:
                    fat_str = ''.join(c for c in line.split(':')[1] if c.isdigit() or c == '.')
                    current_item['fat'] = float(fat_str) if fat_str else 0.0
                except:
                    current_item['fat'] = 0.0
            elif 'Category:' in line:
                current_item['category'] = line.split(':', 1)[1].strip()
            elif 'TOTAL_CALORIES:' in line:
                try:
                    cal_str = ''.join(filter(str.isdigit, line.split(':')[1]))
                    nutrition_data['total_calories'] = int(cal_str) if cal_str else 0
                except:
                    nutrition_data['total_calories'] = 0
            elif 'TOTAL_Protien_g:' in line or 'TOTAL_Protein_g:' in line:
                try:
                    protein_str = ''.join(c for c in line.split(':')[1] if c.isdigit() or c == '.')
                    nutrition_data['total_protein'] = float(protein_str) if protein_str else 0.0
                except:
                    nutrition_data['total_protein'] = 0.0
            elif 'TOTAL_Carbs_g:' in line:
                try:
                    carbs_str = ''.join(c for c in line.split(':')[1] if c.isdigit() or c == '.')
                    nutrition_data['total_carbs'] = float(carbs_str) if carbs_str else 0.0
                except:
                    nutrition_data['total_carbs'] = 0.0
            elif 'TOTAL_Fat_g:' in line:
                try:
                    fat_str = ''.join(c for c in line.split(':')[1] if c.isdigit() or c == '.')
                    nutrition_data['total_fat'] = float(fat_str) if fat_str else 0.0
                except:
                    nutrition_data['total_fat'] = 0.0
            elif 'OVERALL_MODEL_CONFIDENCE:' in line:
                try:
                    conf_str = ''.join(filter(str.isdigit, line.split(':')[1]))
                    nutrition_data['confidence'] = int(conf_str) if conf_str else 0
                except:
                    nutrition_data['confidence'] = 0
        
        if current_item:
            items.append(current_item)
        
        nutrition_data['items'] = items
        nutrition_data['timestamp'] = datetime.now().isoformat()
        return nutrition_data
    except Exception as e:
        st.error(f"Error parsing response: {e}")
        return {}
   
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

def display_dashboard():
    """Display nutrition dashboard with charts"""
    if not st.session_state.meals:
        st.info("No meals logged yet. Analyze an image to start tracking!")
        return
    
    st.subheader("📊 Nutrition Dashboard")
    
    # Calculate totals
    total_calories = sum(meal.get('total_calories', 0) for meal in st.session_state.meals)
    total_protein = sum(meal.get('total_protein', 0) for meal in st.session_state.meals)
    total_carbs = sum(meal.get('total_carbs', 0) for meal in st.session_state.meals)
    total_fat = sum(meal.get('total_fat', 0) for meal in st.session_state.meals)
    
    # Get targets
    targets = st.session_state.nutrition_targets
    
    # Calculate percentages
    cal_percent = min(100, (total_calories / targets['daily_calories'] * 100)) if targets['daily_calories'] > 0 else 0
    protein_percent = min(100, (total_protein / targets['daily_protein'] * 100)) if targets['daily_protein'] > 0 else 0
    carbs_percent = min(100, (total_carbs / targets['daily_carbs'] * 100)) if targets['daily_carbs'] > 0 else 0
    fat_percent = min(100, (total_fat / targets['daily_fat'] * 100)) if targets['daily_fat'] > 0 else 0
    
    # Display metrics with targets
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calories", f"{total_calories:.0f}", f"/{targets['daily_calories']}")
    with col2:
        st.metric("Protein (g)", f"{total_protein:.1f}", f"/{targets['daily_protein']}")
    with col3:
        st.metric("Carbs (g)", f"{total_carbs:.1f}", f"/{targets['daily_carbs']}")
    with col4:
        st.metric("Fat (g)", f"{total_fat:.1f}", f"/{targets['daily_fat']}")
    
    # Progress bars for targets
    st.subheader("📈 Progress Towards Daily Goals")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("**Calories**")
        st.progress(min(cal_percent / 100, 1.0))
        st.write("**Protein**")
        st.progress(min(protein_percent / 100, 1.0))
        st.write("**Carbs**")
        st.progress(min(carbs_percent / 100, 1.0))
        st.write("**Fat**")
        st.progress(min(fat_percent / 100, 1.0))
    
    with col2:
        st.write("**Completion**")
        st.metric("Cal", f"{cal_percent:.0f}%", delta=None)
        st.metric("Protein", f"{protein_percent:.0f}%", delta=None)
        st.metric("Carbs", f"{carbs_percent:.0f}%", delta=None)
        st.metric("Fat", f"{fat_percent:.0f}%", delta=None)
    
    # Gauge charts for each nutrient
    st.subheader("🎯 Target Achievement Gauges")
    col1, col2, col3, col4 = st.columns(4)
    
    # nutrients = [
    #     ("Calories", total_calories, targets['daily_calories'], col1),
    #     ("Protein", total_protein, targets['daily_protein'], col2),
    #     ("Carbs", total_carbs, targets['daily_carbs'], col3),
    #     ("Fat", total_fat, targets['daily_fat'], col4)
    # ]
    
    # for nutrient_name, current, target, col in nutrients:
    #     with col:
    #         percent = min(100, (current / target * 100)) if target > 0 else 0
    #         fig = go.Figure(data=[go.Indicator(
    #             mode="gauge+number+delta",
    #             value=percent,
    #             domain={'x': [0, 1], 'y': [0, 1]},
    #             title={'text': nutrient_name},
    #             delta={'reference': 100, 'suffix': '%'},
    #             gauge={
    #                 'axis': {'range': [None, 100]},
    #                 'bar': {'color': '#95E1D3'},
    #                 'steps': [
    #                     {'range': [0, 50], 'color': '#FFE66D'},
    #                     {'range': [50, 100], 'color': '#95E1D3'},
    #                     {'range': [100, 150], 'color': '#FF6B6B'}
    #                 ],
    #                 'threshold': {
    #                     'line': {'color': 'red', 'width': 4},
    #                     'thickness': 0.75,
    #                     'value': 100
    #                 }
    #             }
    #         )])
    #         fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    #         st.plotly_chart(fig, use_container_width=True)
    
    # Macronutrient pie chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Macronutrient Distribution")
        macros = [total_protein, total_carbs, total_fat]
        if sum(macros) > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Protein', 'Carbs', 'Fat'],
                values=macros,
                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#FFE66D'])
            )])
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Calories Per Meal")
        meal_calories = [meal.get('total_calories', 0) for meal in st.session_state.meals]
        meal_labels = [f"Meal {i+1}" for i in range(len(meal_calories))]
        fig_bar = go.Figure(data=[go.Bar(
            x=meal_labels,
            y=meal_calories,
            marker=dict(color='#95E1D3')
        )])
        fig_bar.update_layout(height=400, xaxis_title="Meal", yaxis_title="Calories")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Food categories distribution
    st.subheader("Food Categories Breakdown")
    all_items = []
    for meal in st.session_state.meals:
        all_items.extend(meal.get('items', []))
    
    if all_items:
        categories = {}
        for item in all_items:
            cat = item.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = {'count': 0, 'calories': 0}
            categories[cat]['count'] += 1
            categories[cat]['calories'] += item.get('calories', 0)
        
        cat_df = pd.DataFrame([
            {'Category': k, 'Count': v['count'], 'Calories': v['calories']}
            for k, v in categories.items()
        ])
        
        fig_cat = px.bar(cat_df, x='Category', y='Calories', color='Count',
                        hover_data=['Count'], title='Calories by Food Category')
        st.plotly_chart(fig_cat, use_container_width=True)
    
    # Detailed meal log
    st.subheader("📝 Detailed Meal Log")
    for i, meal in enumerate(st.session_state.meals):
        with st.expander(f"Meal {i+1} - {meal.get('total_calories', 0):.0f} cal", expanded=False):
            for item in meal.get('items', []):
                st.write(f"**{item.get('name', 'Unknown')}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"Cal: {item.get('calories', 0)}")
                with col2:
                    st.caption(f"P: {item.get('protein', 0):.1f}g")
                with col3:
                    st.caption(f"C: {item.get('carbs', 0):.1f}g")
                with col4:
                    st.caption(f"F: {item.get('fat', 0):.1f}g")
    
    # Clear history button
    if st.button("🗑️ Clear History", key="clear_history"):
        st.session_state.meals = []
        st.rerun()

def display_settings():
    """Display settings page for nutrition targets"""
    st.subheader("⚙️ Nutrition Settings")
    st.write("Set your daily nutrition targets and goals")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Daily Targets")
        
        daily_calories = st.number_input(
            "Daily Calorie Goal",
            min_value=500,
            max_value=5000,
            value=st.session_state.nutrition_targets['daily_calories'],
            step=100,
            help="Your target daily calorie intake"
        )
        
        daily_protein = st.number_input(
            "Daily Protein Goal (g)",
            min_value=10,
            max_value=500,
            value=st.session_state.nutrition_targets['daily_protein'],
            step=5,
            help="Your target daily protein intake in grams"
        )
    
    with col2:
        st.write("### Daily Targets (cont.)")
        
        daily_carbs = st.number_input(
            "Daily Carbs Goal (g)",
            min_value=50,
            max_value=1000,
            value=st.session_state.nutrition_targets['daily_carbs'],
            step=10,
            help="Your target daily carbohydrates intake in grams"
        )
        
        daily_fat = st.number_input(
            "Daily Fat Goal (g)",
            min_value=10,
            max_value=500,
            value=st.session_state.nutrition_targets['daily_fat'],
            step=5,
            help="Your target daily fat intake in grams"
        )
    
    st.divider()
    
    # Preset goals
    st.write("### Quick Presets")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💪 Muscle Building"):
            st.session_state.nutrition_targets = {
                "daily_calories": 2500,
                "daily_protein": 150,
                "daily_carbs": 300,
                "daily_fat": 83
            }
            st.success("Muscle building targets set!")
            st.rerun()
    
    with col2:
        if st.button("⚖️ Weight Loss"):
            st.session_state.nutrition_targets = {
                "daily_calories": 1500,
                "daily_protein": 100,
                "daily_carbs": 150,
                "daily_fat": 50
            }
            st.success("Weight loss targets set!")
            st.rerun()
    
    with col3:
        if st.button("🏃 Athletic"):
            st.session_state.nutrition_targets = {
                "daily_calories": 2300,
                "daily_protein": 130,
                "daily_carbs": 320,
                "daily_fat": 77
            }
            st.success("Athletic targets set!")
            st.rerun()
    
    with col4:
        if st.button("🥗 Balanced"):
            st.session_state.nutrition_targets = {
                "daily_calories": 2000,
                "daily_protein": 50,
                "daily_carbs": 250,
                "daily_fat": 65
            }
            st.success("Balanced targets set!")
            st.rerun()
    
    st.divider()
    
    # Save custom targets
    if st.button("💾 Save Custom Targets", key="save_targets"):
        st.session_state.nutrition_targets = {
            "daily_calories": daily_calories,
            "daily_protein": daily_protein,
            "daily_carbs": daily_carbs,
            "daily_fat": daily_fat
        }
        st.success("✅ Your nutrition targets have been saved!")
        st.rerun()
    
    # Display current targets
    st.write("### Current Targets")
    targets = st.session_state.nutrition_targets
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calories", f"{targets['daily_calories']} kcal/day")
    with col2:
        st.metric("Protein", f"{targets['daily_protein']}g/day")
    with col3:
        st.metric("Carbs", f"{targets['daily_carbs']}g/day")
    with col4:
        st.metric("Fat", f"{targets['daily_fat']}g/day")
    
st.title("Nutrition Agent")
st.write("Upload an image of your meal and ask any nutrition-related questions!")

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page:", ["Meal Analysis", "Dashboard", "Settings"])

if page == "Meal Analysis":
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
                    
                    # Parse and store the meal data
                    meal_data = parse_nutrition_response(response)
                    if meal_data:
                        st.session_state.meals.append(meal_data)
                        st.success("✅ Meal logged successfully! Check the Dashboard to view your nutrition summary.")
        except FileNotFoundError as e:
            st.error(e)

elif page == "Dashboard":
    display_dashboard()

elif page == "Settings":
    display_settings()

# def main():
#     print("Hello from nutrition-agent!")


# if __name__ == "__main__":
#     main()
